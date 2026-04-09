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
    if destination == "whatsapp_lagos":
        number = settings.WHATSAPP_LAGOS_NUMBER or "LAGOS_NUMBER_NOT_SET"
    else:
        number = settings.WHATSAPP_OUTSIDE_LAGOS_NUMBER or "OUTSIDE_LAGOS_NUMBER_NOT_SET"

    # Build message
    message = _build_whatsapp_message(request, items)

    # TODO: WHATSAPP_INTEGRATION — Send via Meta Cloud API or existing bot
    # Currently: mock dispatch (logged but not sent)
    #
    # When your existing WhatsApp bot is ready, call it here:
    # response = await whatsapp_bot.send_message(number, message)
    # message_id = response.get("message_id")
    #
    # Or via Meta Cloud API:
    # POST https://graph.facebook.com/v18.0/{phone_id}/messages
    # headers: Authorization: Bearer {WHATSAPP_TOKEN}
    # body: { messaging_product: "whatsapp", to: number, type: "text", text: { body: message } }

    mock_success = True  # Mock always succeeds

    # Log the dispatch
    dispatch_log = WhatsAppDispatchLog(
        request_id=request_id,
        destination_number=number,
        message_payload=message,
        message_id=None,  # Will be set when live integration is connected
        success=mock_success,
        error_message=None,
        retry_count=0,
    )
    db.add(dispatch_log)

    # Audit
    audit = MedicationAuditLog(
        event_type="whatsapp_dispatched",
        request_id=request_id,
        actor=actor,
        detail=f"Dispatched to {destination} ({number}). Mock mode.",
    )
    db.add(audit)

    db.flush()

    logger.info(
        "WhatsApp dispatch: request=%s, destination=%s, number=%s, mock=True",
        request_id, destination, number,
    )

    return dispatch_log
