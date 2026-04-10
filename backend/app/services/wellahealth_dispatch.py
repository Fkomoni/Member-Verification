"""
WellaHealth Dispatch — sends acute-only requests via fulfilment API.

WellaHealth payload format:
{
  "refId": "RX-20260410-XXXXX",     ← Leadway reference number (tracking key)
  "pharmacyCode": "WHPTest1002",    ← from /v1/Pharmacies/search
  "fulfilmentService": "Acute",
  "diagnosis": "Malaria",
  "notes": "From Leadway Portal",
  "isDelivery": true,
  "patientData": {
    "firstName": "John", "lastName": "Doe",
    "hmoId": "123456", "phoneNumber": "2348012345678",
    "gender": "Male", "dateOfBirth": "1990-01-01",
    "address": "Lekki Phase 1, Lagos"
  },
  "drugs": [
    {
      "refId": "1",                  ← line item number
      "name": "Paracetamol",
      "dose": "Tab tds 5/7",         ← dosage_instruction (required if strength absent)
      "strength": "500mg",           ← optional alongside dose
      "frequency": "tds",            ← OD / BD / TDS / QDS / STAT / PRN (item.route stores this)
      "duration": "5/7"              ← e.g. "5 days" or "5/7"
    }
  ]
}

Drug field rule: Either `dose` OR `strength + frequency + duration` must be present.
We send all fields so both rules are satisfied.
"""

import base64
import json
import logging

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.medication import (
    MedicationAuditLog,
    MedicationRequest,
    MedicationRequestItem,
    WellaHealthApiLog,
)

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(30.0)


def _submit_fulfilment_sync(payload: dict) -> dict:
    """
    Synchronous WellaHealth fulfilment submission using httpx.Client.

    Bypasses the asyncio event loop entirely — safe to call from gunicorn
    sync workers or any sync FastAPI route handler.
    """
    client_id = settings.WELLAHEALTH_CLIENT_ID
    client_secret = settings.WELLAHEALTH_CLIENT_SECRET

    # Mock mode — no credentials configured
    if not (client_id and client_secret):
        ref = payload.get("refId", "UNKNOWN")
        logger.info("WellaHealth mock mode: returning mock tracking for %s", ref)
        return {
            "success": True,
            "mock": True,
            "trackingCode": f"MOCK-TRK-{ref}",
            "trackingLink": "",
        }

    base_url = settings.WELLAHEALTH_BASE_URL.rstrip("/")
    creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {
        "Authorization": f"Basic {creds}",
        "Content-Type": "application/json",
        "X-Partner-Code": settings.WELLAHEALTH_PARTNER_CODE or "",
    }

    url = f"{base_url}/fulfilments"
    logger.info("WellaHealth fulfilment POST → %s | pharmacyCode=%s | refId=%s",
                url, payload.get("pharmacyCode"), payload.get("refId"))

    for attempt in range(3):
        try:
            with httpx.Client(timeout=_TIMEOUT) as client:
                resp = client.post(url, json=payload, headers=headers)

            logger.info("WellaHealth response: HTTP %d", resp.status_code)

            if resp.status_code in (200, 201):
                data = resp.json() if resp.text else {}
                return {"success": True, **data}
            elif resp.status_code == 429:
                import time
                wait = 2 ** (attempt + 1)
                logger.warning("WellaHealth rate limited — waiting %ds", wait)
                time.sleep(wait)
                continue
            else:
                err = f"HTTP {resp.status_code}: {resp.text[:300]}"
                logger.error("WellaHealth fulfilment failed: %s", err)
                if attempt < 2:
                    import time
                    time.sleep(2 ** attempt)
                    continue
                return {"success": False, "error": err}

        except httpx.RequestError as e:
            logger.error("WellaHealth request error (attempt %d): %s", attempt + 1, e)
            if attempt < 2:
                import time
                time.sleep(2 ** attempt)
                continue
            return {"success": False, "error": str(e)}

    return {"success": False, "error": "WellaHealth fulfilment failed after 3 attempts"}


def _build_fulfilment_payload(
    request: MedicationRequest,
    items: list[MedicationRequestItem],
    pharmacy_code: str = "",
) -> dict:
    """
    Build the WellaHealth fulfilment payload.

    Drug field mapping:
      name       ← item.drug_name
      dose       ← item.dosage_instruction  (e.g. "Tab tds 5/7")
      strength   ← item.strength            (e.g. "500mg")
      frequency  ← item.route               (stores frequency: OD/BD/TDS/QDS/STAT/PRN)
      duration   ← item.duration            (e.g. "5 days" or "5/7")
    """
    name_parts = (request.enrollee_name or "Unknown").split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    # Use stored pharmacy_code from request if not explicitly passed
    p_code = pharmacy_code or getattr(request, "pharmacy_code", "") or ""

    drugs = []
    for i, item in enumerate(items):
        drug_entry = {
            "refId": str(i + 1),
            "name": item.drug_name,
            "dose": item.dosage_instruction or "",
        }
        # Add optional fields only if populated
        if item.strength:
            drug_entry["strength"] = item.strength
        # item.route stores the dosing frequency (OD/BD/TDS etc.) — see frontend mapping
        freq = (item.route or "").strip()
        if freq:
            drug_entry["frequency"] = freq
        if item.duration:
            drug_entry["duration"] = item.duration

        drugs.append(drug_entry)

    return {
        "refId": request.reference_number,
        "pharmacyCode": p_code,
        "fulfilmentService": "Acute",
        "diagnosis": request.diagnosis or "",
        "notes": f"From Leadway Rx Portal. Provider: {request.facility_name}",
        "isDelivery": True,
        "patientData": {
            "firstName": first_name,
            "lastName": last_name,
            "hmoId": request.enrollee_id,
            "phoneNumber": request.member_phone or "",
            "gender": request.enrollee_gender or "",
            "dateOfBirth": str(request.enrollee_dob.date()) if request.enrollee_dob else "",
            "address": request.delivery_address or "",
        },
        "drugs": drugs,
    }


def dispatch_to_wellahealth(
    request_id: str,
    db: Session,
    actor: str = "system",
    pharmacy_code: str = "",
    verified_address: str = "",
) -> WellaHealthApiLog:
    """
    Dispatch an acute medication request to WellaHealth fulfilment API.
    Uses synchronous httpx — no asyncio required.
    """
    request = (
        db.query(MedicationRequest)
        .filter(MedicationRequest.request_id == request_id)
        .first()
    )
    if not request:
        raise ValueError(f"Request {request_id} not found")

    items = (
        db.query(MedicationRequestItem)
        .filter(MedicationRequestItem.request_id == request_id)
        .all()
    )

    payload = _build_fulfilment_payload(request, items, pharmacy_code)

    # Submit to WellaHealth (sync — no asyncio issues)
    result = _submit_fulfilment_sync(payload)

    success = result.get("success", False)
    tracking_code = result.get("trackingCode") or result.get("tracking_code") or ""
    tracking_link = result.get("trackingLink") or result.get("tracking_link") or ""

    # Log the API call
    api_log = WellaHealthApiLog(
        request_id=request_id,
        endpoint="/v1/fulfilments",
        method="POST",
        request_payload=json.dumps(payload),
        response_code=200 if success else 500,
        response_body=json.dumps(result),
        external_reference=tracking_code,
        success=success,
        retry_count=0,
        error_message=result.get("error") if not success else None,
    )
    db.add(api_log)

    # Audit entry
    db.add(MedicationAuditLog(
        event_type="wellahealth_dispatched",
        request_id=request_id,
        actor=actor,
        detail=(
            f"Fulfilment {'SENT' if success else 'FAILED'}. "
            f"Tracking: {tracking_code or 'none'}. "
            f"Pharmacy: {payload.get('pharmacyCode') or 'none'}. "
            f"Drugs: {len(payload.get('drugs', []))}."
        ),
    ))

    db.flush()
    logger.info(
        "WellaHealth dispatch: request=%s, success=%s, tracking=%s, pharmacy=%s",
        request_id, success, tracking_code, payload.get("pharmacyCode"),
    )

    return api_log
