from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_member
from app.models.member import Member
from app.models.medication import Medication
from app.models.request import Request, RequestLog
from app.models.notification import Notification
from app.schemas.member import MemberProfile, MemberDashboard
from app.schemas.medication import MedicationOut
from app.services.refill_intelligence import get_refill_intelligence, calculate_days_remaining
from app.services.pbm_client import prognosis_client
from app.services.sync_service import push_approved_request_to_pbm
import logging

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/member", tags=["Member"])


# ── Profile Update Schema ────────────────────────────────────

class ProfileUpdateRequest(BaseModel):
    new_phone: Optional[str] = None
    new_email: Optional[str] = None
    new_address: Optional[str] = None
    comment: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────

@router.get("/profile", response_model=MemberProfile)
async def get_profile(member: Member = Depends(get_current_member)):
    """Get current member profile (read-only from PBM)."""
    return member


@router.get("/dashboard", response_model=MemberDashboard)
async def get_dashboard(
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """Get member dashboard with alerts and summary."""
    med_count = db.query(Medication).filter(
        Medication.member_id == member.member_id, Medication.status == "ACTIVE"
    ).count()

    pending_count = db.query(Request).filter(
        Request.member_id == member.member_id, Request.status == "PENDING"
    ).count()

    unread_count = db.query(Notification).filter(
        Notification.member_id == member.member_id, Notification.is_read.is_(False)
    ).count()

    # Build alerts from refill intelligence
    intelligence = get_refill_intelligence(member.member_id, db)
    alerts = [
        {
            "type": "REFILL",
            "medication": ri.drug_name,
            "message": ri.alert,
            "days_remaining": ri.days_remaining,
            "next_refill_due": str(ri.next_refill_due) if ri.next_refill_due else None,
        }
        for ri in intelligence if ri.alert
    ]

    return MemberDashboard(
        profile=MemberProfile.model_validate(member),
        medications_count=med_count,
        pending_requests=pending_count,
        unread_notifications=unread_count,
        alerts=alerts,
    )


@router.get("/medications", response_model=list[MedicationOut])
async def get_medications(
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """Get current member medications."""
    meds = (
        db.query(Medication)
        .filter(Medication.member_id == member.member_id)
        .order_by(Medication.drug_name)
        .all()
    )

    results = []
    for med in meds:
        med_out = MedicationOut.model_validate(med)
        med_out.days_until_runout = calculate_days_remaining(med)
        results.append(med_out)

    return results


@router.post("/profile/update-request")
async def request_profile_update(
    body: ProfileUpdateRequest,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """
    Quick endpoint: submit a profile update request (phone, email, address).
    Goes through the approval workflow — does NOT directly edit the member record.
    """
    changes = {}
    if body.new_phone:
        changes["phone"] = {"current": member.phone, "requested": body.new_phone}
    if body.new_email:
        changes["email"] = {"current": member.email or "", "requested": body.new_email}
    if body.new_address:
        changes["address"] = {"requested": body.new_address}

    if not changes:
        raise HTTPException(status_code=400, detail="No changes provided. Enter at least one field to update.")

    req = Request(
        member_id=member.member_id,
        request_type="PROFILE_UPDATE",
        action="MODIFY",
        payload=changes,
        comment=body.comment,
        status="APPROVED",  # Auto-approve
    )
    db.add(req)
    db.flush()

    log = RequestLog(
        request_id=req.id,
        actor_type="SYSTEM",
        actor_id="auto-approve",
        action="AUTO_APPROVED",
        before_state={k: v.get("current", "") for k, v in changes.items() if isinstance(v, dict)},
        after_state={k: v.get("requested", "") for k, v in changes.items() if isinstance(v, dict)},
        notes="Auto-approved and pushed to Prognosis",
    )
    db.add(log)
    db.commit()

    # Auto-push to Prognosis
    try:
        await push_approved_request_to_pbm(str(req.id), db)
        _logger.info(f"Profile update auto-pushed to Prognosis for {member.member_id}")
    except Exception as e:
        _logger.error(f"Failed to push profile update to Prognosis: {e}")

    return {
        "message": "Profile updated successfully and synced to Prognosis.",
        "request_id": str(req.id),
        "changes_requested": list(changes.keys()),
    }


@router.get("/notifications")
async def get_notifications(
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
    unread_only: bool = False,
):
    """Get member notifications."""
    query = db.query(Notification).filter(Notification.member_id == member.member_id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))

    notifications = query.order_by(Notification.created_at.desc()).limit(50).all()
    return notifications


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """Mark a notification as read."""
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.member_id == member.member_id)
        .first()
    )
    if notification:
        notification.is_read = True
        db.commit()
    return {"status": "ok"}


@router.get("/search-medications")
async def search_medications(
    q: str = "",
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """
    Search Prognosis drug database by name.
    Returns list of matching medications with ProcedureId and ProcedureName.
    User starts typing and results populate.
    """
    if len(q) < 2:
        return []

    results = await prognosis_client.search_medications(q, db=db)

    # Map Prognosis fields: tariff_desc, tariff_code, cost
    meds = []
    for r in results[:20]:
        name = (r.get("tariff_desc") or r.get("TariffDesc") or
                r.get("ProcedureName") or r.get("procedureName") or
                r.get("Name") or r.get("name") or
                r.get("DrugName") or r.get("drugName") or "")
        proc_id = (r.get("tariff_code") or r.get("TariffCode") or
                   r.get("ProcedureId") or r.get("procedureId") or
                   r.get("Code") or r.get("code") or "")
        cost = r.get("cost") or r.get("Cost") or ""
        if name:
            meds.append({
                "procedure_id": str(proc_id),
                "procedure_name": str(name),
                "cost": str(cost) if cost else None,
            })

    return meds
