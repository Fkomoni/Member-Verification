from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.core.deps import get_current_member
from app.models.member import Member
from app.models.medication import Medication
from app.models.request import Request, RequestLog
from app.schemas.refill import RefillRequest, RefillSuspendRequest, RefillResumeRequest, RefillIntelligence
from app.services.refill_intelligence import get_refill_intelligence
from app.services.sync_service import push_approved_request_to_pbm

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/refill", tags=["Refill"])


@router.post("/request")
async def request_refill(
    req: RefillRequest,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """Request a medication refill."""
    med = (
        db.query(Medication)
        .filter(Medication.id == req.medication_id, Medication.member_id == member.member_id)
        .first()
    )
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")

    if med.status != "ACTIVE":
        raise HTTPException(status_code=400, detail="Cannot refill inactive medication")

    if med.refill_count >= med.max_refills:
        raise HTTPException(status_code=400, detail="No refills remaining. Contact your prescriber.")

    change_req = Request(
        member_id=member.member_id,
        request_type="REFILL_ACTION",
        action="REFILL",
        payload={
            "medication_id": str(med.id),
            "drug_name": med.drug_name,
            "dosage": med.dosage,
            "current_refill_count": med.refill_count,
        },
        comment=req.comment,
        status="APPROVED",
    )
    db.add(change_req)
    db.flush()

    log = RequestLog(
        request_id=change_req.id,
        actor_type="SYSTEM",
        actor_id="auto-approve",
        action="AUTO_APPROVED",
        after_state={"medication_id": str(med.id), "drug_name": med.drug_name},
        notes="Refill auto-approved and pushed to Prognosis",
    )
    db.add(log)
    db.commit()

    try:
        await push_approved_request_to_pbm(str(change_req.id), db)
    except Exception as e:
        logger.error(f"Failed to push refill to Prognosis: {e}")

    return {"message": "Refill request submitted and processed", "request_id": str(change_req.id)}


@router.post("/suspend")
async def suspend_refill(
    req: RefillSuspendRequest,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """Suspend refills for a medication."""
    med = (
        db.query(Medication)
        .filter(Medication.id == req.medication_id, Medication.member_id == member.member_id)
        .first()
    )
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")

    change_req = Request(
        member_id=member.member_id,
        request_type="REFILL_ACTION",
        action="SUSPEND_REFILL",
        payload={
            "medication_id": str(med.id),
            "drug_name": med.drug_name,
            "suspend_until": str(req.suspend_until) if req.suspend_until else None,
        },
        comment=req.reason,
        status="APPROVED",
    )
    db.add(change_req)
    db.flush()

    log = RequestLog(
        request_id=change_req.id,
        actor_type="SYSTEM",
        actor_id="auto-approve",
        action="AUTO_APPROVED",
        after_state={"medication_id": str(med.id), "suspend_until": str(req.suspend_until)},
    )
    db.add(log)
    db.commit()

    try:
        await push_approved_request_to_pbm(str(change_req.id), db)
    except Exception as e:
        logger.error(f"Failed to push suspend to Prognosis: {e}")

    return {"message": "Refill suspension processed", "request_id": str(change_req.id)}


@router.post("/resume")
async def resume_refill(
    req: RefillResumeRequest,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """Resume refills for a medication."""
    med = (
        db.query(Medication)
        .filter(Medication.id == req.medication_id, Medication.member_id == member.member_id)
        .first()
    )
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")

    change_req = Request(
        member_id=member.member_id,
        request_type="REFILL_ACTION",
        action="RESUME_REFILL",
        payload={"medication_id": str(med.id), "drug_name": med.drug_name},
        comment=req.comment,
        status="APPROVED",
    )
    db.add(change_req)
    db.flush()

    log = RequestLog(
        request_id=change_req.id,
        actor_type="SYSTEM",
        actor_id="auto-approve",
        action="AUTO_APPROVED",
        after_state={"medication_id": str(med.id)},
        notes="Resume refill auto-approved",
    )
    db.add(log)
    db.commit()

    try:
        await push_approved_request_to_pbm(str(change_req.id), db)
    except Exception as e:
        logger.error(f"Failed to push resume to Prognosis: {e}")

    return {"message": "Refill resumed and processed", "request_id": str(change_req.id)}


@router.get("/intelligence", response_model=list[RefillIntelligence])
async def refill_intelligence(
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """Get refill intelligence: days remaining, alerts, reminders."""
    return get_refill_intelligence(member.member_id, db)
