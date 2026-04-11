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

from app.models.medication import (
    MedicationAuditLog,
    MedicationRequest,
    MedicationRequestItem,
    WellaHealthApiLog,
)
from app.services.wellahealth_client import wellahealth_client

logger = logging.getLogger(__name__)


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
                "dose": item.dosage_instruction or "",
                "strength": item.strength or "",
                "frequency": item.route or "",
                "duration": item.duration or "",
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

    # Log the API call (mock or live)
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = pool.submit(asyncio.run, wellahealth_client.submit_fulfilment(payload)).result()
        else:
            result = asyncio.run(wellahealth_client.submit_fulfilment(payload))
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
