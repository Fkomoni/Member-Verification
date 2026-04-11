"""
Medication Request API — submit, list, and view prescription requests.

Endpoints:
  POST /medication-requests           — create a new medication request
  GET  /medication-requests           — list requests for current provider
  GET  /medication-requests/{id}      — get a single request by ID
"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_provider
from app.models.medication import (
    ClassificationResult,
    MedicationAuditLog,
    MedicationRequest,
    MedicationRequestItem,
    RequestStatusHistory,
    WellaHealthApiLog,
    WhatsAppDispatchLog,
)
from app.models.models import Provider
from app.schemas.medication import (
    ClassificationResultOut,
    MedicationRequestIn,
    MedicationRequestListOut,
    MedicationRequestOut,
)
from app.services.classification_service import run_classification
from app.services.routing_service import run_routing
from app.services.wellahealth_dispatch import dispatch_to_wellahealth
from app.services.whatsapp_dispatch import dispatch_to_whatsapp
from app.utils.nigerian_locations import is_lagos_location

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Medication Requests"])


def _generate_reference() -> str:
    """Generate a human-readable reference: RX-YYYYMMDD-XXXX."""
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_part = uuid.uuid4().hex[:6].upper()
    return f"RX-{date_part}-{random_part}"


# ── Create Request ───────────────────────────────────────────────

@router.post(
    "/medication-requests",
    response_model=MedicationRequestOut,
    status_code=status.HTTP_201_CREATED,
)
def create_medication_request(
    payload: MedicationRequestIn,
    db: Session = Depends(get_db),
    provider: Provider = Depends(get_current_provider),
):
    """Submit a new medication request."""

    # Determine Lagos routing
    lagos = is_lagos_location(payload.delivery_state, payload.delivery_city)

    # Create request
    ref = _generate_reference()
    request = MedicationRequest(
        reference_number=ref,
        provider_id=provider.provider_id,
        enrollee_id=payload.enrollee_id,
        enrollee_name=payload.enrollee_name,
        enrollee_dob=payload.enrollee_dob,
        enrollee_gender=payload.enrollee_gender,
        member_phone=payload.member_phone,
        member_email=payload.member_email,
        diagnosis=payload.diagnosis,
        treating_doctor=payload.treating_doctor,
        doctor_phone=payload.doctor_phone,
        provider_notes=payload.provider_notes,
        delivery_state=payload.delivery_state,
        delivery_lga=payload.delivery_lga,
        delivery_city=payload.delivery_city,
        delivery_address=payload.delivery_address,
        delivery_landmark=payload.delivery_landmark,
        is_lagos=lagos,
        urgency=payload.urgency,
        status="submitted",
        facility_name=payload.facility_name,
        facility_branch=payload.facility_branch,
    )
    db.add(request)
    db.flush()

    # Create medication items
    for med in payload.medications:
        item = MedicationRequestItem(
            request_id=request.request_id,
            drug_name=med.drug_name,
            generic_name=med.generic_name,
            matched_drug_id=med.matched_drug_id,
            strength=med.strength,
            dosage_instruction=med.dosage_instruction,
            duration=med.duration,
            quantity=med.quantity,
            route=med.route,
        )
        db.add(item)

    # Create initial status history
    history = RequestStatusHistory(
        request_id=request.request_id,
        old_status=None,
        new_status="submitted",
        changed_by=provider.email,
        notes="Request submitted by provider",
    )
    db.add(history)

    # Audit log
    audit = MedicationAuditLog(
        event_type="request_created",
        request_id=request.request_id,
        provider_id=provider.provider_id,
        actor=provider.email,
        detail=f"New medication request {ref} for enrollee {payload.enrollee_id}",
    )
    db.add(audit)

    db.flush()

    # ── Auto-classify ──────────────────────────────
    classification_ok = False
    try:
        run_classification(request.request_id, db, actor=provider.email)
        classification_ok = True
    except Exception as e:
        logger.error("Classification failed for %s: %s", ref, e)

    # ── Auto-route (only if classification succeeded) ─
    routing_dest = None
    if classification_ok:
        try:
            routing_record = run_routing(request.request_id, db, actor=provider.email)
            routing_dest = routing_record.destination
        except Exception as e:
            logger.error("Routing failed for %s: %s", ref, e)

    # ── Auto-dispatch based on routing destination ────
    pharmacy_code = payload.pharmacy_code or ""
    verified_address = payload.delivery_address or ""
    if routing_dest:
        try:
            if routing_dest == "wellahealth":
                dispatch_to_wellahealth(
                    request.request_id, db, actor=provider.email,
                    pharmacy_code=pharmacy_code, verified_address=verified_address,
                )
            elif routing_dest in ("whatsapp_lagos", "whatsapp_outside_lagos"):
                dispatch_to_whatsapp(request.request_id, db, routing_dest, actor=provider.email)
        except Exception as e:
            logger.error("Dispatch failed for %s: %s", ref, e)

    db.commit()
    db.refresh(request)

    logger.info(
        "Medication request created: ref=%s, provider=%s, enrollee=%s, is_lagos=%s",
        ref, provider.email, payload.enrollee_id, lagos,
    )

    # Reload with items, classification, and routing
    request = (
        db.query(MedicationRequest)
        .options(
            joinedload(MedicationRequest.items),
            joinedload(MedicationRequest.classification),
            joinedload(MedicationRequest.routing),
        )
        .filter(MedicationRequest.request_id == request.request_id)
        .first()
    )

    return MedicationRequestOut.model_validate(request)


# ── List Requests (for current provider) ─────────────────────────

@router.get("/medication-requests", response_model=MedicationRequestListOut)
def list_medication_requests(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    provider: Provider = Depends(get_current_provider),
):
    """List medication requests submitted by the current provider."""
    query = (
        db.query(MedicationRequest)
        .filter(MedicationRequest.provider_id == provider.provider_id)
    )

    if status_filter:
        query = query.filter(MedicationRequest.status == status_filter)

    total = query.count()
    requests = (
        query
        .options(
            joinedload(MedicationRequest.items),
            joinedload(MedicationRequest.classification),
            joinedload(MedicationRequest.routing),
        )
        .order_by(MedicationRequest.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return MedicationRequestListOut(
        total=total,
        page=page,
        per_page=per_page,
        requests=[MedicationRequestOut.model_validate(r) for r in requests],
    )


# ── Get Single Request ───────────────────────────────────────────

@router.get("/medication-requests/{request_id}", response_model=MedicationRequestOut)
def get_medication_request(
    request_id: uuid.UUID,
    db: Session = Depends(get_db),
    provider: Provider = Depends(get_current_provider),
):
    """Get a single medication request by ID."""
    request = (
        db.query(MedicationRequest)
        .options(
            joinedload(MedicationRequest.items),
            joinedload(MedicationRequest.classification),
            joinedload(MedicationRequest.routing),
        )
        .filter(
            MedicationRequest.request_id == request_id,
            MedicationRequest.provider_id == provider.provider_id,
        )
        .first()
    )

    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication request not found",
        )

    return MedicationRequestOut.model_validate(request)


# ── Classification Detail ────────────────────────────────────────

@router.get(
    "/medication-requests/{request_id}/classification",
    response_model=ClassificationResultOut,
)
def get_classification(
    request_id: uuid.UUID,
    db: Session = Depends(get_db),
    provider: Provider = Depends(get_current_provider),
):
    """Get classification result for a medication request."""
    # Verify provider owns this request
    request = (
        db.query(MedicationRequest)
        .filter(
            MedicationRequest.request_id == request_id,
            MedicationRequest.provider_id == provider.provider_id,
        )
        .first()
    )
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication request not found",
        )

    classification = (
        db.query(ClassificationResult)
        .filter(ClassificationResult.request_id == request_id)
        .first()
    )
    if not classification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classification not yet available",
        )

    return ClassificationResultOut.model_validate(classification)


# ── Fulfilment Tracking ──────────────────────────────────────────

@router.get("/medication-requests/{request_id}/tracking")
def get_tracking(
    request_id: uuid.UUID,
    db: Session = Depends(get_db),
    provider: Provider = Depends(get_current_provider),
):
    """Get fulfilment/dispatch tracking info for a request."""
    req = (
        db.query(MedicationRequest)
        .filter(
            MedicationRequest.request_id == request_id,
            MedicationRequest.provider_id == provider.provider_id,
        )
        .first()
    )
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    # Check WellaHealth logs
    wh_log = (
        db.query(WellaHealthApiLog)
        .filter(WellaHealthApiLog.request_id == request_id)
        .order_by(WellaHealthApiLog.created_at.desc())
        .first()
    )

    # Check WhatsApp logs
    wa_log = (
        db.query(WhatsAppDispatchLog)
        .filter(WhatsAppDispatchLog.request_id == request_id)
        .order_by(WhatsAppDispatchLog.created_at.desc())
        .first()
    )

    tracking = {
        "request_id": str(request_id),
        "reference": req.reference_number,
        "status": req.status,
    }

    if wh_log:
        import json
        response_data = {}
        try:
            response_data = json.loads(wh_log.response_body) if wh_log.response_body else {}
        except Exception:
            pass
        tracking["wellahealth"] = {
            "dispatched": wh_log.success,
            "tracking_code": wh_log.external_reference or response_data.get("trackingCode", ""),
            "tracking_link": response_data.get("trackingLink", ""),
            "pharmacy_code": "",
            "dispatched_at": wh_log.created_at.isoformat() if wh_log.created_at else "",
            "response": response_data,
        }
        # Extract pharmacy from request payload
        try:
            req_payload = json.loads(wh_log.request_payload) if wh_log.request_payload else {}
            tracking["wellahealth"]["pharmacy_code"] = req_payload.get("pharmacyCode", "")
        except Exception:
            pass

    if wa_log:
        tracking["whatsapp"] = {
            "dispatched": wa_log.success,
            "destination_number": wa_log.destination_number,
            "message_id": wa_log.message_id,
            "dispatched_at": wa_log.created_at.isoformat() if wa_log.created_at else "",
            "error": wa_log.error_message,
        }

    return tracking
