import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.member import Member
from app.models.medication import Medication
from app.models.request import Request
from app.services.pbm_client import pbm_client

logger = logging.getLogger(__name__)


async def sync_member_from_pbm(member_id: str, db: Session) -> bool:
    """Pull latest member data from PBM and update local DB."""
    data = await pbm_client.get_member(member_id, db=db)
    if "error" in data:
        logger.error(f"Failed to sync member {member_id}: {data['error']}")
        return False

    member = db.query(Member).filter(Member.member_id == member_id).first()
    if not member:
        member = Member(member_id=member_id)
        db.add(member)

    for field in ["first_name", "last_name", "email", "phone", "date_of_birth",
                   "gender", "diagnosis", "plan_type", "plan_name", "employer", "status"]:
        if field in data:
            setattr(member, field, data[field])

    member.pbm_synced_at = datetime.now(timezone.utc)
    db.commit()
    return True


async def sync_medications_from_pbm(member_id: str, db: Session) -> bool:
    """Pull latest medication list from PBM."""
    data = await pbm_client.get_member_medications(member_id, db=db)
    if "error" in data:
        logger.error(f"Failed to sync medications for {member_id}: {data['error']}")
        return False

    medications = data.get("medications", [])
    for med_data in medications:
        pbm_drug_id = med_data.get("pbm_drug_id") or med_data.get("drug_id")
        existing = (
            db.query(Medication)
            .filter(Medication.member_id == member_id, Medication.pbm_drug_id == pbm_drug_id)
            .first()
        )

        if existing:
            for field in ["drug_name", "generic_name", "dosage", "frequency", "route",
                          "prescriber", "start_date", "end_date", "is_covered", "coverage_pct",
                          "copay_amount", "refill_count", "max_refills", "next_refill_due",
                          "days_supply", "quantity", "status"]:
                if field in med_data:
                    setattr(existing, field, med_data[field])
            existing.pbm_synced_at = datetime.now(timezone.utc)
        else:
            med = Medication(
                member_id=member_id,
                pbm_drug_id=pbm_drug_id,
                **{k: v for k, v in med_data.items() if hasattr(Medication, k) and k != "pbm_drug_id"},
            )
            med.pbm_synced_at = datetime.now(timezone.utc)
            db.add(med)

    db.commit()
    return True


async def push_approved_request_to_pbm(request_id: str, db: Session) -> bool:
    """Push an approved request to the PBM system."""
    req = db.query(Request).filter(Request.id == request_id).first()
    if not req:
        return False

    payload = {
        "request_id": str(req.id),
        "member_id": req.member_id,
        "request_type": req.request_type,
        "action": req.action,
        "payload": req.payload,
    }

    result = await pbm_client.submit_change_request(payload, db=db)

    if "error" not in result:
        req.pbm_synced = True
        req.pbm_sync_error = None
    else:
        req.pbm_synced = False
        req.pbm_sync_error = result["error"]

    db.commit()
    return req.pbm_synced
