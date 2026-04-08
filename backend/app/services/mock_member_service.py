"""
Member Service — looks up enrollees via the Prognosis API.

Primary: GET /api/EnrolleeProfile/GetEnrolleeBioDataByEnrolleeID?enrolleeid={id}
Fallback: Local database cache (auto-created on first successful API lookup).
"""

import logging

from sqlalchemy.orm import Session

from app.models.models import Member
from app.services.prognosis_client import get_enrollee_biodata

log = logging.getLogger(__name__)


def lookup_member(
    db: Session, *, enrollee_id: str
) -> dict | None:
    """
    Look up a member by enrollee ID.

    Strategy:
    1. Call Prognosis API (real enrollee data)
    2. If API fails/unavailable, check local DB cache
    3. Auto-cache successful API responses to local DB

    Returns dict with member info or None if not found.
    """
    eid = enrollee_id.strip()

    # 1. Call Prognosis API
    api_result = _lookup_via_prognosis(db, eid)
    if api_result:
        return api_result

    # 2. Fallback: check local DB cache
    member = (
        db.query(Member)
        .filter(Member.enrollee_id == eid)
        .first()
    )
    if member:
        log.info("Member found in local DB cache: %s", eid)
        return {
            "member_id": str(member.member_id),
            "enrollee_id": member.enrollee_id,
            "name": member.name,
            "dob": member.dob.isoformat() if member.dob else None,
            "gender": member.gender,
            "phone": None,
            "plan": None,
            "source": "database_cache",
        }

    log.warning("Member not found anywhere: %s", eid)
    return None


def _lookup_via_prognosis(db: Session, enrollee_id: str) -> dict | None:
    """
    Look up member via the Prognosis GetEnrolleeBioDataByEnrolleeID endpoint.
    Returns parsed member dict or None if not found / API unavailable.
    """
    import asyncio

    try:
        # Run the async function synchronously
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(get_enrollee_biodata(enrollee_id))
        loop.close()
    except Exception as e:
        log.warning("Prognosis API call failed for %s: %s", enrollee_id, e)
        return None

    if not result or not result.get("success"):
        return None

    data = result["data"]

    # Extract fields from the Prognosis API response
    # The API may return different field names — handle common variations
    name_parts = []
    for field in ["Surname", "surname", "LastName", "lastName"]:
        if data.get(field):
            name_parts.append(str(data[field]).strip())
            break
    for field in ["FirstName", "firstName", "Firstname", "firstname"]:
        if data.get(field):
            name_parts.append(str(data[field]).strip())
            break
    for field in ["OtherNames", "otherNames", "MiddleName", "middleName"]:
        if data.get(field):
            name_parts.append(str(data[field]).strip())
            break

    full_name = " ".join(name_parts) if name_parts else data.get("Name") or data.get("name") or "Unknown"

    gender = data.get("Gender") or data.get("gender") or data.get("Sex") or data.get("sex")
    dob = data.get("DateOfBirth") or data.get("dateOfBirth") or data.get("DOB") or data.get("dob")
    phone = data.get("PhoneNumber") or data.get("phoneNumber") or data.get("Phone") or data.get("phone")
    plan = data.get("PlanName") or data.get("planName") or data.get("Plan") or data.get("plan")
    company = data.get("CompanyName") or data.get("companyName")

    eid = data.get("EnrolleeID") or data.get("enrolleeID") or data.get("EnrolleeId") or enrollee_id

    # Auto-cache to local DB
    member = (
        db.query(Member)
        .filter(Member.enrollee_id == str(eid))
        .first()
    )
    if not member:
        member = Member(
            enrollee_id=str(eid),
            name=full_name,
            gender=gender,
        )
        db.add(member)
        db.commit()
        db.refresh(member)
        log.info("Cached new member from Prognosis: %s (%s)", eid, full_name)
    else:
        # Update name if changed
        if member.name != full_name:
            member.name = full_name
            db.commit()

    return {
        "member_id": str(member.member_id),
        "enrollee_id": str(eid),
        "name": full_name,
        "dob": dob,
        "gender": gender,
        "phone": phone,
        "plan": plan,
        "company": company,
        "source": "prognosis_api",
    }
