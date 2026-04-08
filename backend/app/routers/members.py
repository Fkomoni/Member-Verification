"""
POST /verify-member – Look up member via Prognosis GetEnrolleeBioDataByEnrolleeID,
                      then check local biometric status.

POST /service-types – Fetch available visit/service types for an enrollee
                      via Prognosis GetSeviceType.

POST /debug-biodata – Return raw Prognosis API response for debugging field names.
"""

import logging

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

    d = biodata_result["data"]

    # 2. Extract fields using exact Prognosis Member_* field names
    enrollee_id = d.get("Member_EnrolleeID") or body.enrollee_id
    name = (
        d.get("Member_CustomerName")
        or f"{d.get('Member_FirstName', '')} {d.get('Member_othernames', '')} {d.get('Member_Surname', '')}".strip()
        or "Unknown"
    )
    gender = d.get("Member_Gender")
    dob = d.get("Member_DateOfBirth")
    phone = d.get("Member_Phone_One")
    email = d.get("Member_EmailAddress_One")
    company = d.get("Client_ClientName")
    plan = d.get("Member_Plan")
    scheme_name = d.get("client_schemename") or d.get("Product_schemeType")
    scheme_id = str(d.get("Member_PlanID", ""))
    cif_number = str(d.get("Member_MemberUniqueID") or d.get("Member_ParentMemberUniqueID") or "")
    provider_name_field = d.get("Member_PCP")
    policy_no = d.get("Client_PolicyNumber")
    member_status = d.get("Member_MemberStatus_Description", "")
    member_type = d.get("Member_Membertype", "")
    plan_category = d.get("Plan_Category", "")
    address = d.get("Member_Address", "")
    expiry_date = d.get("Member_ExpiryDate", "")
    effective_date = d.get("Member_Effectivedate", "")
    family_no = d.get("Member_FamilyNo", "")

    # 3. Check if member exists in local DB (for biometric status)
    member = db.query(Member).filter(Member.enrollee_id == body.enrollee_id).first()
    biometric_registered = member.biometric_registered if member else False
    local_member_id = member.member_id if member else None

    # 4. Build response — strip large profilepic from prognosis_data
    prognosis_data_clean = {k: v for k, v in d.items() if k != "profilepic"}

    response_kwargs = dict(
        enrollee_id=str(enrollee_id),
        name=name,
        dob=str(dob) if dob else None,
        gender=str(gender) if gender else None,
        phone=str(phone) if phone else None,
        email=str(email) if email else None,
        company=str(company) if company else None,
        plan=str(plan) if plan else None,
        scheme_name=str(scheme_name) if scheme_name else None,
        scheme_id=scheme_id if scheme_id else None,
        cif_number=cif_number if cif_number else None,
        provider_name=str(provider_name_field) if provider_name_field else None,
        policy_no=str(policy_no) if policy_no else None,
        member_status=member_status,
        member_type=member_type,
        plan_category=plan_category,
        address=address,
        expiry_date=str(expiry_date) if expiry_date else None,
        effective_date=str(effective_date) if effective_date else None,
        family_no=str(family_no) if family_no else None,
        member_id=local_member_id,
        biometric_registered=biometric_registered,
        prognosis_eligible=True,
        prognosis_data=prognosis_data_clean,
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
    """Debug endpoint: returns the Prognosis API response fields (no photo)."""
    biodata_result = await prognosis_client.get_enrollee_biodata(body.enrollee_id)
    data = biodata_result.get("data") or {}
    # Strip large profilepic
    clean = {k: v for k, v in data.items() if k != "profilepic"} if data else {}
    return {
        "enrollee_id": body.enrollee_id,
        "success": biodata_result["success"],
        "reason": biodata_result.get("reason"),
        "keys": list(clean.keys()),
        "data": clean,
    }
