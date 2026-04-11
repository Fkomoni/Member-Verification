"""
WellaHealth Dispatch — sends acute-only requests via fulfilment API.

Flow:
1. Validate address via Google Maps
2. Search pharmacy via WellaHealth by verified location
3. Submit fulfilment with pharmacy code, patient data, drugs
4. Store tracking code and link
5. Log everything
"""

import json
import logging

from sqlalchemy.orm import Session

from app.core.config import settings

from app.models.medication import (
    MedicationAuditLog,
    MedicationRequest,
    MedicationRequestItem,
    WellaHealthApiLog,
)
from app.services.wellahealth_client import wellahealth_client

logger = logging.getLogger(__name__)


def _convert_duration_to_wella(duration: str) -> str:
    """Convert layman duration to WellaHealth format (X/7)."""
    d = (duration or "").lower().strip()
    mapping = {
        "3 days": "3/7", "5 days": "5/7", "7 days": "7/7",
        "10 days": "10/7", "14 days": "14/7", "21 days": "21/7",
        "30 days": "30/7", "60 days": "60/7", "90 days": "90/7",
        "ongoing": "continuous",
    }
    return mapping.get(d, d)


def _build_fulfilment_payload(
    request: MedicationRequest,
    items: list[MedicationRequestItem],
    pharmacy_code: str = "",
    verified_address: str = "",
) -> dict:
    """Build the WellaHealth fulfilment payload."""
    # Split enrollee name into first/last
    name_parts = (request.enrollee_name or "Unknown").split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    # Use default staging pharmacy if none provided
    if not pharmacy_code:
        pharmacy_code = getattr(settings, 'WELLAHEALTH_PARTNER_CODE', '') or "WHPXTest10123"
        logger.info("No pharmacy code provided, using default: %s", pharmacy_code)

    return {
        "refId": request.reference_number,
        "pharmacyCode": pharmacy_code,
        "fulfilmentService": "Acute",
        "diagnosis": request.diagnosis or "",
        "notes": f"From Leadway Rx Portal. Provider: {request.facility_name}",
        "isDelivery": False,
        "patientData": {
            "firstName": first_name,
            "lastName": last_name,
            "hmoId": request.enrollee_id,
            "phoneNumber": request.member_phone or "",
            "gender": request.enrollee_gender or "",
            "dateOfBirth": str(request.enrollee_dob) if request.enrollee_dob else "",
            "address": verified_address or request.delivery_address or "",
        },
        "drugs": [
            {
                "refId": str(i + 1),
                "name": item.drug_name,
                "dose": f"{item.dosage_instruction or ''} {item.route or ''} {_convert_duration_to_wella(item.duration)}".strip(),
                "strength": item.strength or "",
                "frequency": item.route or "",
                "duration": _convert_duration_to_wella(item.duration),
            }
            for i, item in enumerate(items)
        ],
    }


def dispatch_to_wellahealth(
    request_id: str,
    db: Session,
    actor: str = "system",
    pharmacy_code: str = "",
    verified_address: str = "",
) -> WellaHealthApiLog:
    """Dispatch an acute medication request to WellaHealth fulfilment API."""
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

    payload = _build_fulfilment_payload(request, items, pharmacy_code, verified_address)

    # Make sync HTTP call to WellaHealth (we're in a sync context)
    import base64

    result = {"success": False, "error": "Not attempted"}

    if not settings.WELLAHEALTH_CLIENT_ID or not settings.WELLAHEALTH_CLIENT_SECRET:
        # Mock mode
        result = {
            "success": True, "mock": True,
            "trackingCode": "MOCK-TRK-" + request.reference_number,
        }
    else:
        creds = f"{settings.WELLAHEALTH_CLIENT_ID}:{settings.WELLAHEALTH_CLIENT_SECRET}"
        encoded = base64.b64encode(creds.encode()).decode()
        headers = {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json",
            "X-Partner-Code": settings.WELLAHEALTH_PARTNER_CODE,
        }
        url = f"{settings.WELLAHEALTH_BASE_URL.rstrip('/')}/fulfilments"

        try:
            import httpx
            logger.info("WellaHealth fulfilment URL: %s", url)
            logger.info("WellaHealth fulfilment payload: %s", json.dumps(payload)[:500])
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, json=payload, headers=headers)
            logger.info("WellaHealth fulfilment response: %d %s", resp.status_code, resp.text[:500])
            if resp.status_code in (200, 201):
                result = {"success": True, **resp.json()}
            else:
                result = {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as e:
            logger.error("WellaHealth fulfilment call failed: %s", e)
            result = {"success": False, "error": str(e)}

    success = result.get("success", False)
    tracking_code = result.get("trackingCode") or result.get("tracking_code") or ""
    tracking_link = result.get("trackingLink") or result.get("tracking_link") or ""

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

    db.add(MedicationAuditLog(
        event_type="wellahealth_dispatched",
        request_id=request_id,
        actor=actor,
        detail=f"Fulfilment {'sent' if success else 'FAILED'}. Tracking: {tracking_code}. Pharmacy: {pharmacy_code}",
    ))

    db.flush()
    logger.info("WellaHealth dispatch: request=%s, success=%s, tracking=%s",
                request_id, success, tracking_code)

    return api_log
