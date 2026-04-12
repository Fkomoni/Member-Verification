"""
WhatsApp Dispatch — sends chronic/mixed requests via Leadway WhatsApp bot.

Uses: POST /api/send-message on the Leadway WhatsApp bot
"""

import json
import logging

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.medication import (
    MedicationAuditLog,
    MedicationRequest,
    MedicationRequestItem,
    WhatsAppDispatchLog,
)

logger = logging.getLogger(__name__)


def _build_message(request: MedicationRequest, items: list[MedicationRequestItem]) -> str:
    """Build structured WhatsApp message."""
    med_lines = []
    for i, item in enumerate(items, 1):
        line = f"{i}. {item.drug_name}"
        if item.strength:
            line += f" {item.strength}"
        if item.dosage_instruction:
            line += f" — {item.dosage_instruction}"
        if item.route:
            line += f" {item.route}"
        if item.duration:
            line += f" x {item.duration}"
        if item.item_category:
            line += f" [{item.item_category.upper()}]"
        med_lines.append(line)

    msg = (
        f"*NEW MEDICATION REQUEST*\n"
        f"{'='*30}\n"
        f"*Ref:* {request.reference_number}\n"
        f"*Enrollee:* {request.enrollee_name} ({request.enrollee_id})\n"
        f"*Phone:* {request.member_phone or 'N/A'}\n"
        f"*Facility:* {request.facility_name}\n"
        f"*Doctor:* {request.treating_doctor or 'N/A'}\n"
        f"*Diagnosis:* {request.diagnosis}\n"
        f"*Urgency:* {request.urgency.upper()}\n"
        f"*Location:* {request.delivery_state}"
    )
    if request.delivery_address:
        msg += f"\n*Address:* {request.delivery_address}"
    msg += f"\n\n*Medications:*\n" + "\n".join(med_lines)
    if request.provider_notes:
        msg += f"\n\n*Notes:* {request.provider_notes}"
    return msg


def dispatch_to_whatsapp(
    request_id: str,
    db: Session,
    destination: str,
    actor: str = "system",
) -> WhatsAppDispatchLog:
    """Send medication request to Leadway WhatsApp number via bot API."""
    req = db.query(MedicationRequest).filter(MedicationRequest.request_id == request_id).first()
    if not req:
        raise ValueError(f"Request {request_id} not found")

    items = db.query(MedicationRequestItem).filter(MedicationRequestItem.request_id == request_id).all()

    # Get destination number
    if destination == "whatsapp_lagos":
        number = getattr(settings, 'WHATSAPP_LAGOS_NUMBER', '') or "+2348188626141"
    else:
        number = getattr(settings, 'WHATSAPP_OUTSIDE_LAGOS_NUMBER', '') or "+2348188626141"

    # Clean number format (remove + for WhatsApp API)
    phone = number.lstrip("+")

    message = _build_message(req, items)

    # Send via bot API
    bot_url = getattr(settings, 'WHATSAPP_BOT_URL', '') or "https://leadway-whatsapp-bot.onrender.com/api"
    api_key = getattr(settings, 'WHATSAPP_BOT_API_KEY', '') or ""

    dispatch_success = False
    message_id = None
    error_msg = None

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{bot_url}/send-message",
                json={"phone": phone, "message": message},
                headers={"X-API-Key": api_key, "Content-Type": "application/json"},
            )
        logger.info("WhatsApp bot response: %d %s", resp.status_code, resp.text[:200])
        if resp.status_code in (200, 201):
            data = resp.json() if resp.text else {}
            message_id = data.get("message_id") or data.get("id") or ""
            dispatch_success = True
        else:
            error_msg = f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        error_msg = str(e)
        logger.error("WhatsApp bot call failed: %s", e)

    # Log
    log = WhatsAppDispatchLog(
        request_id=request_id,
        destination_number=number,
        message_payload=message,
        message_id=message_id,
        success=dispatch_success,
        error_message=error_msg,
    )
    db.add(log)
    db.add(MedicationAuditLog(
        event_type="whatsapp_dispatched",
        request_id=request_id,
        actor=actor,
        detail=f"WhatsApp to {number} ({'OK' if dispatch_success else 'FAILED'}). {destination}",
    ))
    db.flush()

    logger.info("WhatsApp dispatch: request=%s, to=%s, success=%s", request_id, number, dispatch_success)
    return log
