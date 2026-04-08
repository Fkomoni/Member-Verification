"""
POST /verify-member – Look up member via Prognosis GetEnrolleeBioDataByEnrolleeID,
                      then check local biometric status.

POST /service-types – Fetch available visit/service types for an enrollee
                      via Prognosis GetSeviceType.
"""

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

router = APIRouter(tags=["members"])


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

    prognosis_data = biodata_result["data"]

    # 2. Extract fields from Prognosis response (adapt to actual API field names)
    # Common field patterns from Prognosis HMO APIs:
    enrollee_id = (
        prognosis_data.get("ENROLLEE_ID")
        or prognosis_data.get("EnrolleeID")
        or prognosis_data.get("enrolleeId")
        or prognosis_data.get("enrollee_id")
        or body.enrollee_id
    )
    first_name = (
        prognosis_data.get("FIRST_NAME")
        or prognosis_data.get("FirstName")
        or prognosis_data.get("firstName")
        or prognosis_data.get("first_name")
        or ""
    )
    last_name = (
        prognosis_data.get("LAST_NAME")
        or prognosis_data.get("LastName")
        or prognosis_data.get("lastName")
        or prognosis_data.get("last_name")
        or prognosis_data.get("SURNAME")
        or prognosis_data.get("Surname")
        or ""
    )
    other_names = (
        prognosis_data.get("OTHER_NAMES")
        or prognosis_data.get("OtherNames")
        or prognosis_data.get("otherNames")
        or prognosis_data.get("MIDDLE_NAME")
        or prognosis_data.get("MiddleName")
        or ""
    )
    # Build full name
    name_parts = [p for p in [first_name, other_names, last_name] if p]
    name = " ".join(name_parts) or prognosis_data.get("NAME") or prognosis_data.get("Name") or "Unknown"

    gender = (
        prognosis_data.get("GENDER")
        or prognosis_data.get("Gender")
        or prognosis_data.get("SEX")
        or prognosis_data.get("Sex")
        or None
    )
    dob = (
        prognosis_data.get("DATE_OF_BIRTH")
        or prognosis_data.get("DateOfBirth")
        or prognosis_data.get("DOB")
        or prognosis_data.get("Dob")
        or prognosis_data.get("dob")
        or None
    )
    phone = (
        prognosis_data.get("PHONE_NUMBER")
        or prognosis_data.get("PhoneNumber")
        or prognosis_data.get("MOBILE_NO")
        or prognosis_data.get("MobileNo")
        or prognosis_data.get("Phone")
        or None
    )
    email = (
        prognosis_data.get("EMAIL")
        or prognosis_data.get("Email")
        or prognosis_data.get("EMAIL_ADDRESS")
        or prognosis_data.get("EmailAddress")
        or None
    )
    company = (
        prognosis_data.get("COMPANY_NAME")
        or prognosis_data.get("CompanyName")
        or prognosis_data.get("COMPANY")
        or prognosis_data.get("Company")
        or None
    )
    plan = (
        prognosis_data.get("PLAN_NAME")
        or prognosis_data.get("PlanName")
        or prognosis_data.get("PLAN")
        or prognosis_data.get("Plan")
        or prognosis_data.get("PLAN_TYPE")
        or prognosis_data.get("PlanType")
        or None
    )
    scheme_name = (
        prognosis_data.get("SCHEME_NAME")
        or prognosis_data.get("SchemeName")
        or prognosis_data.get("SCHEME")
        or prognosis_data.get("Scheme")
        or None
    )
    scheme_id = (
        prognosis_data.get("SCHEME_ID")
        or prognosis_data.get("SchemeId")
        or prognosis_data.get("schemeId")
        or prognosis_data.get("scheme_id")
        or None
    )
    cif_number = (
        prognosis_data.get("CIF_NUMBER")
        or prognosis_data.get("CifNumber")
        or prognosis_data.get("CIF")
        or prognosis_data.get("Cif")
        or prognosis_data.get("cif_number")
        or None
    )
    provider_name_field = (
        prognosis_data.get("PROVIDER_NAME")
        or prognosis_data.get("ProviderName")
        or None
    )
    policy_no = (
        prognosis_data.get("POLICY_NO")
        or prognosis_data.get("PolicyNo")
        or prognosis_data.get("POLICY_NUMBER")
        or prognosis_data.get("PolicyNumber")
        or None
    )

    # 3. Check if member exists in local DB (for biometric status)
    member = db.query(Member).filter(Member.enrollee_id == body.enrollee_id).first()
    biometric_registered = member.biometric_registered if member else False
    local_member_id = member.member_id if member else None

    # 4. Determine verification status
    if not biometric_registered:
        return EligibilityResponse(
            enrollee_id=enrollee_id,
            name=name,
            dob=str(dob) if dob else None,
            gender=gender,
            phone=phone,
            email=email,
            company=company,
            plan=plan,
            scheme_name=scheme_name,
            scheme_id=str(scheme_id) if scheme_id else None,
            cif_number=str(cif_number) if cif_number else None,
            provider_name=provider_name_field,
            policy_no=policy_no,
            member_id=local_member_id,
            biometric_registered=False,
            prognosis_eligible=True,
            prognosis_data=prognosis_data,
            verification_status="UNVERIFIED",
            verification_reason=(
                "Enrollee found in Prognosis but has NO biometric on file. "
                "Fingerprint capture is required before services can be rendered."
            ),
        )

    # Prognosis found AND biometric registered — still needs live scan
    return EligibilityResponse(
        enrollee_id=enrollee_id,
        name=name,
        dob=str(dob) if dob else None,
        gender=gender,
        phone=phone,
        email=email,
        company=company,
        plan=plan,
        scheme_name=scheme_name,
        scheme_id=str(scheme_id) if scheme_id else None,
        cif_number=str(cif_number) if cif_number else None,
        provider_name=provider_name_field,
        policy_no=policy_no,
        member_id=local_member_id,
        biometric_registered=True,
        prognosis_eligible=True,
        prognosis_data=prognosis_data,
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
