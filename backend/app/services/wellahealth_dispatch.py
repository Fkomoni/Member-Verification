"""
WellaHealth Dispatch — sends acute-only requests via fulfilment API.
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

DURATION_MAP = {
    "3 days": "3/7", "5 days": "5/7", "7 days": "7/7",
    "10 days": "10/7", "14 days": "14/7", "21 days": "21/7",
    "30 days": "30/7", "60 days": "60/7", "90 days": "90/7",
    "ongoing": "continuous",
}


def _search_pharmacy(state: str, lga: str = "") -> str:
    """Search WellaHealth for a pharmacy by state+LGA. Returns pharmacyCode or empty."""
    if not settings.WELLAHEALTH_CLIENT_ID:
        return ""
    try:
        creds = f"{settings.WELLAHEALTH_CLIENT_ID}:{settings.WELLAHEALTH_CLIENT_SECRET}"
        auth = base64.b64encode(creds.encode()).decode()
        url = f"{settings.WELLAHEALTH_BASE_URL.rstrip('/')}/Pharmacies/search"
        # Capitalize state name — WellaHealth is case-sensitive
        state_name = state.strip().title() if state else "Lagos"
        lga_name = lga.strip().title() if lga else ""
        logger.info("Pharmacy search: state=%s, lga=%s", state_name, lga_name)
        headers = {"Authorization": f"Basic {auth}", "X-Partner-Code": settings.WELLAHEALTH_PARTNER_CODE}

        # Priority 1: Search by state + LGA (closest pharmacy)
        if lga_name:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(url, params={"stateName": state_name, "lgaName": lga_name}, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("data", []) if isinstance(data, dict) else []
                if isinstance(items, list) and len(items) > 0:
                    code = items[0].get("pharmacyCode") or ""
                    logger.info("Pharmacy found by LGA: %s from %d results", code, len(items))
                    return code
            logger.info("No pharmacy in %s %s, trying state only", state_name, lga_name)

        # Priority 2: Search by state only (fallback)
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, params={"stateName": state_name}, headers=headers)
        logger.info("Pharmacy search response: %d %s", resp.status_code, resp.text[:300])
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("data", []) if isinstance(data, dict) else []
            if isinstance(items, list) and len(items) > 0:
                code = items[0].get("pharmacyCode") or ""
                name = items[0].get("pharmacyName") or ""
                logger.info("Pharmacy selected: %s (%s) from %d results", code, name, len(items))
                return code
    except Exception as e:
        logger.error("Pharmacy search failed: %s", e)
    return ""


def dispatch_to_wellahealth(
    request_id: str,
    db: Session,
    actor: str = "system",
    pharmacy_code: str = "",
    verified_address: str = "",
) -> WellaHealthApiLog:
    """Dispatch an acute medication request to WellaHealth fulfilment API."""
    req = db.query(MedicationRequest).filter(MedicationRequest.request_id == request_id).first()
    if not req:
        raise ValueError(f"Request {request_id} not found")

    items = db.query(MedicationRequestItem).filter(MedicationRequestItem.request_id == request_id).all()

    # Step 1: Get pharmacy code
    if not pharmacy_code:
        pharmacy_code = _search_pharmacy(req.delivery_state or "Lagos", req.delivery_lga or "")

    if not pharmacy_code:
        logger.error("No pharmacy found for %s, %s — sending to manual review", req.delivery_state, req.delivery_lga)
        api_log = WellaHealthApiLog(
            request_id=request_id, endpoint="/v1/fulfilments", method="POST",
            request_payload="", response_code=0, success=False,
            error_message=f"No pharmacy found for {req.delivery_state}, {req.delivery_lga}",
        )
        db.add(api_log)
        db.add(MedicationAuditLog(
            event_type="wellahealth_dispatch_failed", request_id=request_id, actor=actor,
            detail=f"No pharmacy found for {req.delivery_state}",
        ))
        db.flush()
        return api_log

    # Step 2: Build payload
    name_parts = (req.enrollee_name or "Unknown").split(" ", 1)
    address = verified_address or req.delivery_address or ""

    payload = {
        "refId": req.reference_number,
        "pharmacyCode": pharmacy_code,
        "fulfilmentService": "Acute",
        "diagnosis": req.diagnosis or "",
        "notes": f"From Leadway Rx Portal. Provider: {req.facility_name}",
        "isDelivery": False,
        "patientData": {
            "firstName": name_parts[0],
            "lastName": name_parts[1] if len(name_parts) > 1 else "",
            "hmoId": req.enrollee_id,
            "phoneNumber": req.member_phone or "",
            "gender": req.enrollee_gender or "",
            "dateOfBirth": str(req.enrollee_dob) if req.enrollee_dob else "",
            "address": address,
        },
        "drugs": [
            {
                "refId": str(i + 1),
                "name": item.drug_name,
                "dose": f"{item.dosage_instruction or ''} {item.route or ''} {DURATION_MAP.get((item.duration or '').lower(), item.duration or '')}".strip(),
                "strength": item.strength or "",
                "frequency": item.route or "",
                "duration": DURATION_MAP.get((item.duration or "").lower(), item.duration or ""),
            }
            for i, item in enumerate(items)
        ],
    }

    # Step 3: Send to WellaHealth
    result = {"success": False, "error": "Not attempted"}

    if not settings.WELLAHEALTH_CLIENT_ID:
        result = {"success": True, "mock": True, "trackingCode": "MOCK-TRK-" + req.reference_number}
    else:
        creds = f"{settings.WELLAHEALTH_CLIENT_ID}:{settings.WELLAHEALTH_CLIENT_SECRET}"
        encoded = base64.b64encode(creds.encode()).decode()
        url = f"{settings.WELLAHEALTH_BASE_URL.rstrip('/')}/fulfilments"
        headers = {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json",
            "X-Partner-Code": settings.WELLAHEALTH_PARTNER_CODE,
        }
        try:
            logger.info("WellaHealth POST %s pharmacy=%s", url, pharmacy_code)
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, json=payload, headers=headers)
            logger.info("WellaHealth response: %d %s", resp.status_code, resp.text[:500])
            if resp.status_code in (200, 201):
                result = {"success": True, **resp.json()}
            else:
                result = {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as e:
            logger.error("WellaHealth call failed: %s", e)
            result = {"success": False, "error": str(e)}

    # Step 4: Log
    api_log = WellaHealthApiLog(
        request_id=request_id,
        endpoint="/v1/fulfilments",
        method="POST",
        request_payload=json.dumps(payload),
        response_code=200 if result.get("success") else 500,
        response_body=json.dumps(result),
        external_reference=result.get("trackingCode", ""),
        success=result.get("success", False),
        retry_count=0,
        error_message=result.get("error") if not result.get("success") else None,
    )
    db.add(api_log)
    db.add(MedicationAuditLog(
        event_type="wellahealth_dispatched",
        request_id=request_id,
        actor=actor,
        detail=f"Pharmacy: {pharmacy_code}. {'Success' if result.get('success') else 'Failed'}: {result.get('trackingCode', result.get('error', ''))}",
    ))
    db.flush()

    # Send member notification on success
    if result.get("success"):
        try:
            from app.services.member_notification import send_member_email
            import asyncio
            asyncio.get_event_loop().create_task(
                send_member_email(
                    request_id=request_id, db=db,
                    pharmacy_name=pharmacy_code,
                    tracking_code=result.get("trackingCode", ""),
                    tracking_link=result.get("trackingLink", ""),
                )
            )
        except Exception as e:
            # Fallback: try sync
            try:
                import asyncio as aio
                aio.run(send_member_email(
                    request_id=request_id, db=db,
                    pharmacy_name=pharmacy_code,
                    tracking_code=result.get("trackingCode", ""),
                    tracking_link=result.get("trackingLink", ""),
                ))
            except Exception:
                logger.warning("Member email notification failed: %s", e)

    return api_log
