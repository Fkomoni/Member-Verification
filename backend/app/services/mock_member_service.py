"""
Member Service — looks up enrollees via the Prognosis API.

Primary: GET /api/EnrolleeProfile/GetEnrolleeBioDataByEnrolleeID?enrolleeid={id}
No local DB caching — uses Prognosis as the single source of truth.
"""

import logging

from sqlalchemy.orm import Session

from app.services.prognosis_client import get_enrollee_biodata

log = logging.getLogger(__name__)


def lookup_member(
    db: Session, *, enrollee_id: str
) -> dict | None:
    """
    Look up a member by enrollee ID via Prognosis API.
    Returns dict with member info or None if not found.
    """
    eid = enrollee_id.strip()
    result = _lookup_via_prognosis(eid)
    if result:
        return result

    log.warning("Member not found: %s", eid)
    return None


def _lookup_via_prognosis(enrollee_id: str) -> dict | None:
    """Call Prognosis GetEnrolleeBioDataByEnrolleeID endpoint."""
    import asyncio

    try:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(get_enrollee_biodata(enrollee_id))
        loop.close()
    except Exception as e:
        log.warning("Prognosis API call failed for %s: %s", enrollee_id, e)
        return None

    if not result or not result.get("success"):
        return None

    data = result["data"]

    # Extract name fields
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

    return {
        "enrollee_id": str(eid),
        "name": full_name,
        "dob": dob,
        "gender": gender,
        "phone": phone,
        "plan": plan,
        "company": company,
        "source": "prognosis_api",
    }
