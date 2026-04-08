"""
POST /verify-member – Look up member via Prognosis GetEnrolleeBioDataByEnrolleeID,
                      then check local biometric status.

POST /service-types – Fetch available visit/service types for an enrollee
                      via Prognosis GetSeviceType.

POST /debug-biodata – Return raw Prognosis API response for debugging field names.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_provider
from app.models.models import Member, Provider
from app.schemas.schemas import (
    EligibilityResponse,
    MemberLookup,
    ServiceTypesRequest,
    ServiceTypesResponse,
)
from app.services import prognosis_client

log = logging.getLogger(__name__)
router = APIRouter(tags=["members"])


def _get_field(data: dict, *keys: str) -> Any:
    """
    Case-insensitive field lookup.  Tries each key literally first,
    then falls back to a case-insensitive scan of the dict.
    """
    # Fast path: exact match
    for k in keys:
        if k in data:
            return data[k]
    # Slow path: case-insensitive
    lower_map = {dk.lower(): dk for dk in data}
    for k in keys:
        actual = lower_map.get(k.lower())
        if actual is not None and data[actual] is not None:
            return data[actual]
    return None


def _normalize_response(raw: Any) -> dict:
    """If the API returns a list, unwrap the first element."""
    if isinstance(raw, list):
        return raw[0] if raw else {}
    if isinstance(raw, dict):
        return raw
    return {}


@router.post("/verify-member", response_model=EligibilityResponse)
async def verify_member(
    body: MemberLookup,
    db: Session = Depends(get_db),
    provider: Provider = Depends(get_current_provider),
):
    # 1. Fetch enrollee bio-data from Prognosis
    biodata_result = await prognosis_client.get_enrollee_biodata(body.enrollee_id)

    if not biodata_result["success"] or not biodata_result["data"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=biodata_result.get("reason")
            or f"Enrollee '{body.enrollee_id}' not found in Prognosis",
        )

    raw_data = biodata_result["data"]
    d = _normalize_response(raw_data)

    # Log all keys for debugging
    log.info("Prognosis biodata keys for %s: %s", body.enrollee_id, list(d.keys()))

    # 2. Extract fields — case-insensitive, covers common naming conventions
    enrollee_id = (
        _get_field(d, "ENROLLEE_ID", "EnrolleeID", "EnrolleeId", "enrolleeId",
                   "enrollee_id", "Enrollee_ID", "MEMBERID", "MemberId", "memberId")
        or body.enrollee_id
    )

    # Name — try full name first, then combine parts
    full_name = _get_field(
        d, "FULL_NAME", "FullName", "fullName", "Fullname", "FULLNAME",
        "NAME", "Name", "name", "MEMBER_NAME", "MemberName", "memberName",
    )
    first_name = _get_field(
        d, "FIRST_NAME", "FirstName", "firstName", "first_name", "Firstname",
        "FORENAME", "Forename",
    ) or ""
    last_name = _get_field(
        d, "LAST_NAME", "LastName", "lastName", "last_name", "Lastname",
        "SURNAME", "Surname", "surname", "FAMILY_NAME", "FamilyName",
    ) or ""
    other_names = _get_field(
        d, "OTHER_NAMES", "OtherNames", "otherNames", "other_names",
        "Othernames", "OTHERNAMES",
        "MIDDLE_NAME", "MiddleName", "middleName",
    ) or ""

    if full_name:
        name = str(full_name)
    else:
        name_parts = [p for p in [first_name, other_names, last_name] if p]
        name = " ".join(name_parts) if name_parts else "Unknown"

    gender = _get_field(
        d, "GENDER", "Gender", "gender", "SEX", "Sex", "sex",
    )
    dob = _get_field(
        d, "DATE_OF_BIRTH", "DateOfBirth", "dateOfBirth", "DOB", "Dob", "dob",
        "BIRTH_DATE", "BirthDate", "birthDate",
    )
    phone = _get_field(
        d, "PHONE_NUMBER", "PhoneNumber", "phoneNumber", "PHONE", "Phone", "phone",
        "MOBILE_NO", "MobileNo", "mobileNo", "MOBILE", "Mobile", "mobile",
        "GSM", "Gsm", "gsm", "TELEPHONE", "Telephone",
    )
    email = _get_field(
        d, "EMAIL", "Email", "email", "EMAIL_ADDRESS", "EmailAddress",
        "emailAddress", "E_MAIL", "E_mail",
    )
    company = _get_field(
        d, "COMPANY_NAME", "CompanyName", "companyName", "COMPANY", "Company",
        "company", "EMPLOYER", "Employer", "employer",
        "ORGANIZATION", "Organization",
    )
    plan = _get_field(
        d, "PLAN_NAME", "PlanName", "planName", "PLAN", "Plan", "plan",
        "PLAN_TYPE", "PlanType", "planType",
        "BENEFIT_PLAN", "BenefitPlan",
    )
    scheme_name = _get_field(
        d, "SCHEME_NAME", "SchemeName", "schemeName", "SCHEME", "Scheme", "scheme",
    )
    scheme_id = _get_field(
        d, "SCHEME_ID", "SchemeId", "schemeId", "scheme_id", "SCHEMEID", "Schemeid",
    )
    cif_number = _get_field(
        d, "CIF_NUMBER", "CifNumber", "cifNumber", "CIF", "Cif", "cif",
        "cif_number", "CIFNUMBER", "CIFNumber",
    )
    provider_name_field = _get_field(
        d, "PROVIDER_NAME", "ProviderName", "providerName",
        "PROVIDER", "Provider",
    )
    policy_no = _get_field(
        d, "POLICY_NO", "PolicyNo", "policyNo", "POLICY_NUMBER", "PolicyNumber",
        "policyNumber", "POLICYNO", "POLICY", "Policy",
    )

    # 3. Check if member exists in local DB (for biometric status)
    member = db.query(Member).filter(Member.enrollee_id == body.enrollee_id).first()
    biometric_registered = member.biometric_registered if member else False
    local_member_id = member.member_id if member else None

    # 4. Build response
    response_kwargs = dict(
        enrollee_id=str(enrollee_id) if enrollee_id else body.enrollee_id,
        name=name,
        dob=str(dob) if dob else None,
        gender=str(gender) if gender else None,
        phone=str(phone) if phone else None,
        email=str(email) if email else None,
        company=str(company) if company else None,
        plan=str(plan) if plan else None,
        scheme_name=str(scheme_name) if scheme_name else None,
        scheme_id=str(scheme_id) if scheme_id else None,
        cif_number=str(cif_number) if cif_number else None,
        provider_name=str(provider_name_field) if provider_name_field else None,
        policy_no=str(policy_no) if policy_no else None,
        member_id=local_member_id,
        biometric_registered=biometric_registered,
        prognosis_eligible=True,
        prognosis_data=d,
    )

    if not biometric_registered:
        return EligibilityResponse(
            **response_kwargs,
            verification_status="UNVERIFIED",
            verification_reason=(
                "Enrollee found in Prognosis but has NO biometric on file. "
                "Fingerprint capture is required before services can be rendered."
            ),
        )

    return EligibilityResponse(
        **response_kwargs,
        verification_status="UNVERIFIED",
        verification_reason=(
            "Enrollee found in Prognosis and has biometric on file. "
            "Fingerprint scan required to complete identity verification."
        ),
    )


@router.post("/service-types", response_model=ServiceTypesResponse)
async def get_service_types(
    body: ServiceTypesRequest,
    provider: Provider = Depends(get_current_provider),
):
    """Fetch visit/service types for an enrollee from Prognosis."""
    result = await prognosis_client.get_service_types(
        cif=body.cif_number,
        scheme_id=body.scheme_id,
    )

    return ServiceTypesResponse(
        success=result["success"],
        reason=result.get("reason"),
        service_types=result.get("service_types", []),
    )


@router.post("/debug-biodata")
async def debug_biodata(
    body: MemberLookup,
    provider: Provider = Depends(get_current_provider),
):
    """
    Debug endpoint: returns the raw Prognosis API response so you can see
    the actual field names. Remove in production.
    """
    biodata_result = await prognosis_client.get_enrollee_biodata(body.enrollee_id)
    raw = biodata_result.get("data")
    normalized = _normalize_response(raw) if raw else {}
    return {
        "enrollee_id": body.enrollee_id,
        "success": biodata_result["success"],
        "reason": biodata_result.get("reason"),
        "raw_response": raw,
        "normalized_keys": list(normalized.keys()) if normalized else [],
        "normalized_data": normalized,
    }
