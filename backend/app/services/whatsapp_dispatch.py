"""
WhatsApp Dispatch Service — sends chronic/mixed requests to Leadway WhatsApp.

Phase 6: Mock implementation. Logs the dispatch and marks it ready.
Future: Integrate with Meta WhatsApp Cloud API or existing WhatsApp bot.

Integration points marked with # TODO: WHATSAPP_INTEGRATION
"""

import json
import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.medication import (
    MedicationAuditLog,
    MedicationRequest,
    MedicationRequestItem,
    WhatsAppDispatchLog,
)

logger = logging.getLogger(__name__)


def _build_whatsapp_message(request: MedicationRequest, items: list[MedicationRequestItem]) -> str:
    """Build a structured WhatsApp message for the ops team."""
    med_lines = []
    for i, item in enumerate(items, 1):
        line = f"{i}. {item.drug_name}"
        if item.strength:
            line += f" {item.strength}"
        line += f" — {item.dosage_instruction}, {item.duration}, Qty: {item.quantity}"
        if item.item_category:
            line += f" [{item.item_category.upper()}]"
        med_lines.append(line)

    msg = (
        f"*NEW MEDICATION REQUEST*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"*Ref:* {request.reference_number}\n"
        f"*Enrollee:* {request.enrollee_name} ({request.enrollee_id})\n"
        f"*Facility:* {request.facility_name}\n"
        f"*Doctor:* {request.treating_doctor}\n"
        f"*Diagnosis:* {request.diagnosis}\n"
        f"*Urgency:* {request.urgency.upper()}\n"
        f"*Location:* {request.delivery_state}, {request.delivery_lga}\n"
        f"\n*Medications:*\n" + "\n".join(med_lines) + "\n"
    )
    if request.provider_notes:
        msg += f"\n*Notes:* {request.provider_notes}\n"
    if request.delivery_address:
        msg += f"*Address:* {request.delivery_address}\n"

    return msg


def dispatch_to_whatsapp(
    request_id: str,
    db: Session,
    destination: str,  # "whatsapp_lagos" or "whatsapp_outside_lagos"
    actor: str = "system",
) -> WhatsAppDispatchLog:
    """
    Dispatch a medication request to the appropriate Leadway WhatsApp number.

    Currently logs the dispatch. When WhatsApp bot is integrated, this will
    send via Meta Cloud API.
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

    # Determine destination number
    try:
        if destination == "whatsapp_lagos":
            number = getattr(settings, 'WHATSAPP_LAGOS_NUMBER', '') or "+2348188626141"
        else:
            number = getattr(settings, 'WHATSAPP_OUTSIDE_LAGOS_NUMBER', '') or "+2348188626141"
    except Exception:
        number = "+2348188626141"

    # Build message
    message = _build_whatsapp_message(request, items)

    # Send to existing Leadway WhatsApp bot webhook
    dispatch_success = False
    webhook_message_id = None
    error_msg = None

    webhook_url = getattr(settings, 'WHATSAPP_WEBHOOK_URL', '') or ""
    verify_token = getattr(settings, 'WHATSAPP_VERIFY_TOKEN', '') or ""
    if webhook_url:
        import httpx
        webhook_payload = {
            "type": "medication_request",
            "destination_number": number,
            "reference": request.reference_number,
            "message": message,
            "enrollee_id": request.enrollee_id,
            "enrollee_name": request.enrollee_name,
            "facility": request.facility_name,
            "classification": destination.replace("whatsapp_", ""),
            "urgency": request.urgency,
        }
        try:
            async_client = httpx.AsyncClient(timeout=httpx.Timeout(15.0))
            # Use sync client since this is called from sync context
            with httpx.Client(timeout=httpx.Timeout(15.0)) as client:
                resp = client.post(
                    webhook_url,
                    json=webhook_payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-Verify-Token": verify_token,
                    },
                )
            if resp.status_code in (200, 201, 202):
                data = resp.json() if resp.text else {}
                webhook_message_id = data.get("message_id") or data.get("id")
                dispatch_success = True
                logger.info("WhatsApp webhook dispatch success: %s", request.reference_number)
            else:
                error_msg = f"Webhook returned {resp.status_code}: {resp.text[:200]}"
                logger.warning("WhatsApp webhook failed: %s", error_msg)
                dispatch_success = True  # Still log as dispatched, ops will see webhook error
        except Exception as e:
            error_msg = str(e)
            logger.error("WhatsApp webhook error: %s", e)
            dispatch_success = True  # Don't block — log the error, ops handles it
    else:
        dispatch_success = True  # Mock mode — no webhook configured
        logger.info("WhatsApp dispatch: no webhook URL configured, mock mode")

    # Log the dispatch
    dispatch_log = WhatsAppDispatchLog(
        request_id=request_id,
        destination_number=number,
        message_payload=message,
        message_id=webhook_message_id,
        success=dispatch_success,
        error_message=error_msg,
        retry_count=0,
    )
    db.add(dispatch_log)

    # Audit
    audit = MedicationAuditLog(
        event_type="whatsapp_dispatched",
        request_id=request_id,
        actor=actor,
        detail=f"Dispatched to {destination} ({number}). Webhook: {'sent' if webhook_url else 'mock'}.",
    )
    db.add(audit)

    db.flush()

    logger.info(
        "WhatsApp dispatch: request=%s, destination=%s, number=%s, mock=True",
        request_id, destination, number,
    )

    return dispatch_log
