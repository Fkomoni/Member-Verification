import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.member import Member
from app.models.medication import Medication
from app.models.request import Request
from app.services.pbm_client import prognosis_client

logger = logging.getLogger(__name__)


async def sync_member_from_pbm(member_id: str, db: Session) -> bool:
    """Pull latest member data from Prognosis and update local DB."""
    data = await prognosis_client.get_member(member_id, db=db)
    if "error" in data:
        logger.error(f"Failed to sync member {member_id}: {data['error']}")
        return False

    member = db.query(Member).filter(Member.member_id == member_id).first()
    if not member:
        member = Member(member_id=member_id)
        db.add(member)

    # Map Prognosis fields (handle various field name formats)
    field_map = {
        "first_name": ["firstName", "FirstName", "first_name", "Firstname"],
        "last_name": ["lastName", "LastName", "last_name", "Lastname", "surname", "Surname"],
        "email": ["email", "Email", "emailAddress", "EmailAddress"],
        "phone": ["phone", "Phone", "phoneNumber", "PhoneNumber", "mobileNumber", "MobileNumber"],
        "gender": ["gender", "Gender", "sex", "Sex"],
        "diagnosis": ["diagnosis", "Diagnosis", "primaryDiagnosis", "PrimaryDiagnosis"],
        "plan_type": ["planType", "PlanType", "planCode", "PlanCode"],
        "plan_name": ["planName", "PlanName", "plan", "Plan"],
        "employer": ["employer", "Employer", "company", "Company", "organizationName", "OrganizationName"],
    }

    for our_field, prognosis_keys in field_map.items():
        for key in prognosis_keys:
            if key in data and data[key]:
                setattr(member, our_field, data[key])
                break

    member.pbm_synced_at = datetime.now(timezone.utc)
    db.commit()
    return True


async def sync_medications_from_pbm(member_id: str, db: Session) -> bool:
    """Pull latest medication list from Prognosis."""
    data = await prognosis_client.get_member_medications(member_id, db=db)
    if "error" in data:
        logger.error(f"Failed to sync medications for {member_id}: {data['error']}")
        return False

    medications = data.get("medications", [])
    for med_data in medications:
        pbm_drug_id = (
            med_data.get("pbm_drug_id") or med_data.get("drug_id") or
            med_data.get("DrugID") or med_data.get("drugId") or
            med_data.get("id")
        )

        if not pbm_drug_id:
            continue

        existing = (
            db.query(Medication)
            .filter(Medication.member_id == member_id, Medication.pbm_drug_id == str(pbm_drug_id))
            .first()
        )

        # Map medication fields
        med_field_map = {
            "drug_name": ["drugName", "DrugName", "drug_name", "name", "Name"],
            "generic_name": ["genericName", "GenericName", "generic_name"],
            "dosage": ["dosage", "Dosage", "dose", "Dose"],
            "frequency": ["frequency", "Frequency"],
            "route": ["route", "Route"],
            "prescriber": ["prescriber", "Prescriber", "doctor", "Doctor"],
        }

        if existing:
            for our_field, keys in med_field_map.items():
                for key in keys:
                    if key in med_data and med_data[key]:
                        setattr(existing, our_field, med_data[key])
                        break
            existing.pbm_synced_at = datetime.now(timezone.utc)
        else:
            med = Medication(
                member_id=member_id,
                pbm_drug_id=str(pbm_drug_id),
                drug_name="Unknown",
                dosage="N/A",
                frequency="N/A",
            )
            for our_field, keys in med_field_map.items():
                for key in keys:
                    if key in med_data and med_data[key]:
                        setattr(med, our_field, med_data[key])
                        break
            med.pbm_synced_at = datetime.now(timezone.utc)
            db.add(med)

    db.commit()
    return True


async def push_approved_request_to_pbm(request_id: str, db: Session) -> bool:
    """Push an approved request to the Prognosis system."""
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

    result = await prognosis_client.submit_change_request(payload, db=db)

    if "error" not in result:
        req.pbm_synced = True
        req.pbm_sync_error = None
    else:
        req.pbm_synced = False
        req.pbm_sync_error = result.get("error", "Unknown error")

    db.commit()
    return req.pbm_synced
