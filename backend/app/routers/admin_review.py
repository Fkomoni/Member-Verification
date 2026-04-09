"""
Admin Review Queue API — manage requests that need manual intervention.

Cases for manual review:
- Unknown drug names (flagged by classifier)
- Missing/ambiguous location
- API dispatch failures
- High-risk medications flagged for review

Admin actions:
- View queue (filterable)
- Override classification
- Override routing + trigger dispatch
- Add internal comments
- Reject/cancel requests
"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_provider
from app.models.medication import (
    ClassificationResult,
    MedicationAuditLog,
    MedicationRequest,
    MedicationRequestItem,
    RequestStatusHistory,
    RoutingDecision,
)
from app.models.models import Provider
from app.schemas.medication import MedicationRequestListOut, MedicationRequestOut
from app.services.classification_service import run_classification
from app.services.routing_service import run_routing
from app.services.wellahealth_dispatch import dispatch_to_wellahealth
from app.services.whatsapp_dispatch import dispatch_to_whatsapp

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Admin Review Queue"])


# ── Schemas ──────────────────────────────────────────────────────

class OverrideClassificationIn(BaseModel):
    classification: str  # acute | chronic | mixed
    reasoning: str | None = None


class OverrideRoutingIn(BaseModel):
    destination: str  # wellahealth | whatsapp_lagos | whatsapp_outside_lagos
    reasoning: str | None = None


class AdminCommentIn(BaseModel):
    comment: str


class UpdateStatusIn(BaseModel):
    status: str
    notes: str | None = None


# ── Review Queue ─────────────────────────────────────────────────

@router.get("/admin/review-queue", response_model=MedicationRequestListOut)
def get_review_queue(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    queue_type: str = Query("all", description="all | review | failed | pending"),
    db: Session = Depends(get_db),
    _provider=Depends(get_current_provider),
):
    """Get requests needing admin attention."""
    query = db.query(MedicationRequest)

    if queue_type == "review":
        query = query.filter(MedicationRequest.status == "under_review")
    elif queue_type == "failed":
        query = query.filter(MedicationRequest.status == "failed")
    elif queue_type == "pending":
        query = query.filter(MedicationRequest.status == "submitted")
    elif queue_type == "all":
        query = query.filter(
            MedicationRequest.status.in_(["under_review", "failed", "submitted", "escalated"])
        )

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
        total=total, page=page, per_page=per_page,
        requests=[MedicationRequestOut.model_validate(r) for r in requests],
    )


# ── Override Classification ──────────────────────────────────────

@router.post("/admin/requests/{request_id}/override-classification")
def override_classification(
    request_id: uuid.UUID,
    body: OverrideClassificationIn,
    db: Session = Depends(get_db),
    provider: Provider = Depends(get_current_provider),
):
    """Override the classification of a request and re-route."""
    allowed = {"acute", "chronic", "mixed"}
    if body.classification not in allowed:
        raise HTTPException(400, f"classification must be one of {allowed}")

    req = db.query(MedicationRequest).filter(MedicationRequest.request_id == request_id).first()
    if not req:
        raise HTTPException(404, "Request not found")

    # Update or create classification
    cls = db.query(ClassificationResult).filter(ClassificationResult.request_id == request_id).first()
    if cls:
        cls.classification = body.classification
        cls.classified_by = "manual"
        cls.reasoning = body.reasoning or f"Manual override to {body.classification}"
        cls.confidence = 1.0
        cls.review_required = False
    else:
        cls = ClassificationResult(
            request_id=request_id,
            classification=body.classification,
            classified_by="manual",
            reasoning=body.reasoning or f"Manual override to {body.classification}",
            confidence=1.0,
            review_required=False,
        )
        db.add(cls)

    # Audit
    db.add(MedicationAuditLog(
        event_type="classification_overridden",
        request_id=request_id,
        provider_id=provider.provider_id,
        actor=provider.email,
        detail=f"Classification overridden to {body.classification}",
    ))

    # Re-route
    db.flush()
    try:
        routing_record = run_routing(request_id, db, actor=provider.email)
        # Auto-dispatch
        if routing_record.destination == "wellahealth":
            dispatch_to_wellahealth(request_id, db, actor=provider.email)
        elif routing_record.destination in ("whatsapp_lagos", "whatsapp_outside_lagos"):
            dispatch_to_whatsapp(request_id, db, routing_record.destination, actor=provider.email)
    except Exception as e:
        logger.error("Re-routing failed after override: %s", e)

    db.commit()
    return {"message": f"Classification overridden to {body.classification}, re-routed"}


# ── Override Routing ─────────────────────────────────────────────

@router.post("/admin/requests/{request_id}/override-routing")
def override_routing(
    request_id: uuid.UUID,
    body: OverrideRoutingIn,
    db: Session = Depends(get_db),
    provider: Provider = Depends(get_current_provider),
):
    """Override routing destination and dispatch."""
    allowed = {"wellahealth", "whatsapp_lagos", "whatsapp_outside_lagos"}
    if body.destination not in allowed:
        raise HTTPException(400, f"destination must be one of {allowed}")

    req = db.query(MedicationRequest).filter(MedicationRequest.request_id == request_id).first()
    if not req:
        raise HTTPException(404, "Request not found")

    status_map = {
        "wellahealth": "routed_wellahealth",
        "whatsapp_lagos": "sent_whatsapp_lagos",
        "whatsapp_outside_lagos": "sent_whatsapp_outside_lagos",
    }

    # Update routing
    routing = db.query(RoutingDecision).filter(RoutingDecision.request_id == request_id).first()
    if routing:
        routing.destination = body.destination
        routing.reasoning = body.reasoning or f"Manual routing override to {body.destination}"
    else:
        routing = RoutingDecision(
            request_id=request_id,
            destination=body.destination,
            reasoning=body.reasoning or f"Manual routing override to {body.destination}",
        )
        db.add(routing)

    # Update status
    old_status = req.status
    req.status = status_map[body.destination]

    db.add(RequestStatusHistory(
        request_id=request_id, old_status=old_status,
        new_status=req.status, changed_by=provider.email,
        notes=f"Routing overridden to {body.destination}",
    ))

    db.add(MedicationAuditLog(
        event_type="routing_overridden",
        request_id=request_id,
        provider_id=provider.provider_id,
        actor=provider.email,
        detail=f"Routing overridden to {body.destination}",
    ))

    # Dispatch
    db.flush()
    try:
        if body.destination == "wellahealth":
            dispatch_to_wellahealth(request_id, db, actor=provider.email)
        else:
            dispatch_to_whatsapp(request_id, db, body.destination, actor=provider.email)
    except Exception as e:
        logger.error("Dispatch failed after routing override: %s", e)

    db.commit()
    return {"message": f"Routed to {body.destination} and dispatched"}


# ── Update Status ────────────────────────────────────────────────

@router.post("/admin/requests/{request_id}/status")
def update_request_status(
    request_id: uuid.UUID,
    body: UpdateStatusIn,
    db: Session = Depends(get_db),
    provider: Provider = Depends(get_current_provider),
):
    """Update request status (complete, cancel, escalate, etc.)."""
    req = db.query(MedicationRequest).filter(MedicationRequest.request_id == request_id).first()
    if not req:
        raise HTTPException(404, "Request not found")

    old_status = req.status
    req.status = body.status

    db.add(RequestStatusHistory(
        request_id=request_id, old_status=old_status,
        new_status=body.status, changed_by=provider.email,
        notes=body.notes,
    ))

    db.add(MedicationAuditLog(
        event_type="status_updated",
        request_id=request_id,
        provider_id=provider.provider_id,
        actor=provider.email,
        detail=f"Status changed: {old_status} → {body.status}. {body.notes or ''}",
    ))

    db.commit()
    return {"message": f"Status updated to {body.status}"}


# ── Add Comment ──────────────────────────────────────────────────

@router.post("/admin/requests/{request_id}/comment")
def add_admin_comment(
    request_id: uuid.UUID,
    body: AdminCommentIn,
    db: Session = Depends(get_db),
    provider: Provider = Depends(get_current_provider),
):
    """Add an internal admin comment to a request."""
    req = db.query(MedicationRequest).filter(MedicationRequest.request_id == request_id).first()
    if not req:
        raise HTTPException(404, "Request not found")

    db.add(MedicationAuditLog(
        event_type="admin_comment",
        request_id=request_id,
        provider_id=provider.provider_id,
        actor=provider.email,
        detail=body.comment,
    ))

    db.commit()
    return {"message": "Comment added"}


# ── Get Audit Trail ──────────────────────────────────────────────

@router.get("/admin/requests/{request_id}/audit")
def get_request_audit(
    request_id: uuid.UUID,
    db: Session = Depends(get_db),
    _provider=Depends(get_current_provider),
):
    """Get full audit trail for a request."""
    logs = (
        db.query(MedicationAuditLog)
        .filter(MedicationAuditLog.request_id == request_id)
        .order_by(MedicationAuditLog.created_at.asc())
        .all()
    )
    return [
        {
            "event_type": l.event_type,
            "actor": l.actor,
            "detail": l.detail,
            "timestamp": l.created_at.isoformat(),
        }
        for l in logs
    ]
