"""
WellaHealth Dispatch Service — sends acute-only requests to WellaHealth API.

Phase 6: Mock dispatch with full logging.
Future: Connect to live WellaHealth API when credentials are provided.
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


def _build_wellahealth_payload(request: MedicationRequest, items: list[MedicationRequestItem]) -> dict:
    """
    Build the payload for WellaHealth fulfilment submission.

    WellaHealth expects: memberName, memberNumber, address, medications (name + quantity)
    """
    # Build geolocated address string
    address_parts = [request.delivery_address or ""]
    if request.delivery_landmark:
        address_parts.append(request.delivery_landmark)
    address_parts.extend([request.delivery_lga, request.delivery_state])
    address = ", ".join(p for p in address_parts if p)

    return {
        "reference": request.reference_number,
        "enrollee_id": request.enrollee_id,
        "member_name": request.enrollee_name,
        "delivery_address": address,
        "medications": [
            {
                "drug_name": item.drug_name,
                "strength": item.strength or "",
                "quantity": item.quantity,
                "dosage": item.dosage_instruction,
                "duration": item.duration,
            }
            for item in items
        ],
    }


def dispatch_to_wellahealth(
    request_id: str,
    db: Session,
    actor: str = "system",
) -> WellaHealthApiLog:
    """
    Dispatch an acute medication request to WellaHealth.

    Currently mock. When WellaHealth API credentials are provided,
    the wellahealth_client will handle the actual HTTP call.
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

    payload = _build_wellahealth_payload(request, items)

    # TODO: WELLAHEALTH_INTEGRATION — Replace mock with live call
    # response = await wellahealth_client.submit_order(payload)
    mock_success = True
    mock_response = {"order_id": "MOCK-WH-" + request.reference_number, "status": "pending"}

    # Log the API call
    api_log = WellaHealthApiLog(
        request_id=request_id,
        endpoint="/orders",
        method="POST",
        request_payload=json.dumps(payload),
        response_code=200 if mock_success else 500,
        response_body=json.dumps(mock_response),
        external_reference=mock_response.get("order_id"),
        success=mock_success,
        retry_count=0,
        error_message=None,
    )
    db.add(api_log)

    # Audit
    audit = MedicationAuditLog(
        event_type="wellahealth_dispatched",
        request_id=request_id,
        actor=actor,
        detail=f"Dispatched to WellaHealth. Mock mode. Ref: {mock_response.get('order_id')}",
    )
    db.add(audit)

    db.flush()

    logger.info(
        "WellaHealth dispatch: request=%s, ref=%s, mock=True",
        request_id, request.reference_number,
    )

    return api_log
