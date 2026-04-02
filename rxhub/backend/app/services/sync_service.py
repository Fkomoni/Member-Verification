import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.member import Member
from app.models.medication import Medication
from app.models.request import Request
from app.services.pbm_client import prognosis_client

logger = logging.getLogger(__name__)


def _find(data: dict, *fields) -> str:
    """Find first non-empty value from a list of possible field names."""
    for f in fields:
        val = data.get(f)
        if val is not None and str(val).strip():
            return str(val).strip()
    return ""


def _find_date(data: dict, *fields):
    """Find and parse a date from possible field names."""
    for f in fields:
        val = data.get(f)
        if val and str(val).strip():
            try:
                from dateutil import parser as dp
                return dp.parse(str(val)).date()
            except Exception:
                continue
    return None


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
        "first_name": ["Member_FirstName", "Member_Firstname", "firstName", "FirstName"],
        "last_name": ["Member_LastName", "Member_Surname", "lastName", "LastName", "Surname"],
        "email": ["Member_Email", "Member_EmailAddress", "email", "Email"],
        "phone": ["Member_MobileNo", "Member_Phone", "Member_PhoneNumber", "phone", "Phone", "MobileNo"],
        "gender": ["Member_Gender", "Member_Sex", "gender", "Gender"],
        "plan_type": ["Member_PlanType", "Member_PlanCode", "planType", "PlanType"],
        "plan_name": ["Member_SchemeName", "Member_SchemeDescription", "Member_Scheme", "Member_PlanName", "SchemeName", "planName"],
        "employer": ["Member_Employer", "Member_Company", "Member_OrganizationName", "employer", "Employer"],
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
    """
    Pull medications from Prognosis PharmacyDelivery/GetPbmMedication API.
    Replaces all existing medications with fresh data from PBM.
    Also updates member delivery info and diagnosis.
    """
    data = await prognosis_client.get_member_medications(member_id, db=db)
    if "error" in data:
        logger.error(f"Failed to sync medications for {member_id}: {data['error']}")
        return False

    medications = data.get("medications", [])
    delivery_info = data.get("delivery_info", {})

    # Update member with delivery info and diagnosis if available
    if delivery_info:
        member = db.query(Member).filter(Member.member_id == member_id).first()
        if member:
            if delivery_info.get("diagnosis"):
                member.diagnosis = delivery_info["diagnosis"]
            if delivery_info.get("delivery_phone") and not member.phone:
                member.phone = delivery_info["delivery_phone"]
            db.commit()

    # Clear old medications and replace with fresh PBM data
    if medications:
        db.query(Medication).filter(Medication.member_id == member_id).delete()
        db.flush()
        logger.info(f"Cleared old medications for {member_id}, syncing {len(medications)} from PBM")

    for med_data in medications:
        # Find a unique ID for this medication
        pbm_drug_id = _find(med_data,
            "PBMMedicationID", "PbmMedicationID", "MedicationID", "medicationId",
            "DrugID", "drugId", "drug_id", "pbm_drug_id", "ID", "id",
        )
        if not pbm_drug_id:
            # Use drug name as fallback ID
            pbm_drug_id = _find(med_data, "DrugName", "Drug_Name", "drugName", "drug_name", "Name", "name") or "unknown"

        # Map all medication fields
        drug_name = _find(med_data,
            "DrugName", "Drug_Name", "drugName", "drug_name",
            "MedicationName", "Medication_Name", "Name", "name",
            "ItemName", "Item_Name", "ProductName",
        ) or "Unknown Medication"

        generic_name = _find(med_data,
            "GenericName", "Generic_Name", "genericName", "generic_name",
        )

        dosage = _find(med_data,
            "Dosage", "dosage", "Dose", "dose",
            "Strength", "strength", "DrugStrength",
        ) or ""

        frequency = _find(med_data,
            "Frequency", "frequency", "Freq", "freq",
            "Direction", "direction", "Directions", "SigDescription",
        ) or ""

        route = _find(med_data, "Route", "route", "RouteOfAdmin")

        prescriber = _find(med_data,
            "Prescriber", "prescriber", "Doctor", "doctor",
            "PrescriberName", "DoctorName", "Physician",
        )

        quantity = _find(med_data,
            "Quantity", "quantity", "Qty", "qty",
            "QuantityDispensed", "QtyDispensed",
        )

        days_supply = _find(med_data,
            "DaysSupply", "Days_Supply", "daysSupply", "days_supply",
            "SupplyDays", "Duration", "duration",
        )

        # Refill dates
        next_refill_due = _find_date(med_data,
            "NextRefillDate", "Next_Refill_Date", "nextRefillDate", "next_refill_date",
            "NextRefill", "NextDispenseDate", "NextFillDate",
            "ExpectedRefillDate", "DueDate",
        )

        last_refill_at_date = _find_date(med_data,
            "LastRefillDate", "Last_Refill_Date", "lastRefillDate", "last_refill_date",
            "LastRefill", "LastDispenseDate", "LastFillDate",
            "DateDispensed", "DispenseDate", "FillDate",
        )

        start_date = _find_date(med_data,
            "StartDate", "start_date", "startDate",
            "PrescriptionDate", "RxDate", "DatePrescribed",
        )

        end_date = _find_date(med_data,
            "EndDate", "end_date", "endDate",
            "ExpiryDate", "ExpirationDate",
        )

        refill_count = _find(med_data,
            "RefillCount", "refillCount", "refill_count",
            "NumberOfRefills", "RefillsUsed", "FillNumber",
        )

        max_refills = _find(med_data,
            "MaxRefills", "maxRefills", "max_refills",
            "TotalRefills", "RefillsAllowed", "RefillsAuthorized",
        )

        status = _find(med_data,
            "Status", "status", "MedicationStatus", "DrugStatus",
        ) or "ACTIVE"

        # Create medication record
        med = Medication(
            member_id=member_id,
            pbm_drug_id=str(pbm_drug_id)[:100],
            drug_name=drug_name,
            generic_name=generic_name or None,
            dosage=dosage or "N/A",
            frequency=frequency or "N/A",
            route=route or None,
            prescriber=prescriber or None,
            start_date=start_date,
            end_date=end_date,
            next_refill_due=next_refill_due,
            days_supply=int(days_supply) if days_supply and days_supply.isdigit() else 30,
            quantity=int(quantity) if quantity and quantity.isdigit() else None,
            refill_count=int(refill_count) if refill_count and refill_count.isdigit() else 0,
            max_refills=int(max_refills) if max_refills and max_refills.isdigit() else 12,
            status=status.upper() if status.upper() in ("ACTIVE", "DISCONTINUED", "SUSPENDED", "PENDING") else "ACTIVE",
            pbm_synced_at=datetime.now(timezone.utc),
        )

        # Set last_refill_at as datetime
        if last_refill_at_date:
            med.last_refill_at = datetime.combine(last_refill_at_date, datetime.min.time()).replace(tzinfo=timezone.utc)

        db.add(med)

    db.commit()
    logger.info(f"Synced {len(medications)} medications for {member_id}")
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
