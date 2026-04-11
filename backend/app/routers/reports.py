"""
Reporting API — analytics and audit data for the medication routing system.

Endpoints:
  GET /reports/summary         — key metrics overview
  GET /reports/by-provider     — requests grouped by provider
  GET /reports/by-facility     — requests grouped by facility
  GET /reports/by-classification — acute vs chronic vs mixed volumes
  GET /reports/by-route        — WellaHealth vs WhatsApp volumes
  GET /reports/by-status       — request status breakdown
  GET /reports/top-drugs       — most prescribed medications
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, case, distinct
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_admin_provider
from app.models.medication import (
    ClassificationResult,
    MedicationAuditLog,
    MedicationRequest,
    MedicationRequestItem,
    RoutingDecision,
    WellaHealthApiLog,
    WhatsAppDispatchLog,
)
from app.models.models import Provider

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Reports"])


def _date_filter(query, column, days: int | None):
    """Apply optional date range filter."""
    if days:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return query.filter(column >= cutoff)
    return query


# ── Summary ──────────────────────────────────────────────────────

@router.get("/reports/summary")
def get_summary(
    days: int | None = Query(None, description="Filter to last N days"),
    db: Session = Depends(get_db),
    _provider=Depends(get_admin_provider),
):
    """Key metrics overview."""
    base = db.query(MedicationRequest)
    base = _date_filter(base, MedicationRequest.created_at, days)

    total = base.count()
    by_status = dict(
        base.with_entities(MedicationRequest.status, func.count())
        .group_by(MedicationRequest.status).all()
    )

    # Classification counts
    cls_base = db.query(ClassificationResult)
    if days:
        cls_base = _date_filter(cls_base, ClassificationResult.classified_at, days)
    cls_counts = dict(
        cls_base.with_entities(ClassificationResult.classification, func.count())
        .group_by(ClassificationResult.classification).all()
    )

    # Route counts
    rt_base = db.query(RoutingDecision)
    if days:
        rt_base = _date_filter(rt_base, RoutingDecision.routed_at, days)
    route_counts = dict(
        rt_base.with_entities(RoutingDecision.destination, func.count())
        .group_by(RoutingDecision.destination).all()
    )

    # Lagos split
    lagos_count = base.filter(MedicationRequest.is_lagos.is_(True)).count()
    outside_count = base.filter(MedicationRequest.is_lagos.is_(False)).count()
    unknown_loc = base.filter(MedicationRequest.is_lagos.is_(None)).count()

    return {
        "total_requests": total,
        "by_status": by_status,
        "by_classification": cls_counts,
        "by_route": route_counts,
        "location": {
            "lagos": lagos_count,
            "outside_lagos": outside_count,
            "unknown": unknown_loc,
        },
        "period_days": days,
    }


# ── By Provider ──────────────────────────────────────────────────

@router.get("/reports/by-provider")
def report_by_provider(
    days: int | None = Query(None),
    db: Session = Depends(get_db),
    _provider=Depends(get_admin_provider),
):
    """Requests grouped by provider."""
    query = (
        db.query(
            Provider.name,
            Provider.email,
            func.count(MedicationRequest.request_id).label("total"),
        )
        .join(MedicationRequest, MedicationRequest.provider_id == Provider.provider_id)
    )
    query = _date_filter(query, MedicationRequest.created_at, days)
    results = query.group_by(Provider.name, Provider.email).order_by(func.count().desc()).all()

    return [{"provider_name": r[0], "email": r[1], "total_requests": r[2]} for r in results]


# ── By Facility ──────────────────────────────────────────────────

@router.get("/reports/by-facility")
def report_by_facility(
    days: int | None = Query(None),
    db: Session = Depends(get_db),
    _provider=Depends(get_admin_provider),
):
    """Requests grouped by facility name."""
    query = (
        db.query(
            MedicationRequest.facility_name,
            func.count().label("total"),
        )
    )
    query = _date_filter(query, MedicationRequest.created_at, days)
    results = query.group_by(MedicationRequest.facility_name).order_by(func.count().desc()).all()

    return [{"facility": r[0], "total_requests": r[1]} for r in results]


# ── By Classification ────────────────────────────────────────────

@router.get("/reports/by-classification")
def report_by_classification(
    days: int | None = Query(None),
    db: Session = Depends(get_db),
    _provider=Depends(get_admin_provider),
):
    """Acute vs chronic vs mixed volumes."""
    query = (
        db.query(
            ClassificationResult.classification,
            func.count().label("total"),
        )
    )
    query = _date_filter(query, ClassificationResult.classified_at, days)
    results = query.group_by(ClassificationResult.classification).all()

    return [{"classification": r[0], "count": r[1]} for r in results]


# ── By Route ─────────────────────────────────────────────────────

@router.get("/reports/by-route")
def report_by_route(
    days: int | None = Query(None),
    db: Session = Depends(get_db),
    _provider=Depends(get_admin_provider),
):
    """WellaHealth vs WhatsApp routing volumes."""
    query = (
        db.query(
            RoutingDecision.destination,
            func.count().label("total"),
        )
    )
    query = _date_filter(query, RoutingDecision.routed_at, days)
    results = query.group_by(RoutingDecision.destination).all()

    return [{"destination": r[0], "count": r[1]} for r in results]


# ── By Status ────────────────────────────────────────────────────

@router.get("/reports/by-status")
def report_by_status(
    days: int | None = Query(None),
    db: Session = Depends(get_db),
    _provider=Depends(get_admin_provider),
):
    """Request status breakdown."""
    query = (
        db.query(
            MedicationRequest.status,
            func.count().label("total"),
        )
    )
    query = _date_filter(query, MedicationRequest.created_at, days)
    results = query.group_by(MedicationRequest.status).order_by(func.count().desc()).all()

    return [{"status": r[0], "count": r[1]} for r in results]


# ── Top Drugs ────────────────────────────────────────────────────

@router.get("/reports/top-drugs")
def report_top_drugs(
    limit: int = Query(20, ge=1, le=100),
    days: int | None = Query(None),
    db: Session = Depends(get_db),
    _provider=Depends(get_admin_provider),
):
    """Most prescribed medications."""
    query = (
        db.query(
            MedicationRequestItem.drug_name,
            MedicationRequestItem.item_category,
            func.count().label("count"),
        )
        .join(MedicationRequest)
    )
    query = _date_filter(query, MedicationRequest.created_at, days)
    results = (
        query
        .group_by(MedicationRequestItem.drug_name, MedicationRequestItem.item_category)
        .order_by(func.count().desc())
        .limit(limit)
        .all()
    )

    return [{"drug_name": r[0], "category": r[1], "count": r[2]} for r in results]
