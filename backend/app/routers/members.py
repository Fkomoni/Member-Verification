"""
POST /verify-member – Look up member, check Prognosis eligibility,
                      and enforce biometric verification requirement.

Even if all Prognosis criteria are met, if the member has not been
biometrically verified in this session, the response returns
verification_status="UNVERIFIED" with the reason.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_provider
from backend.app.models.models import Member, Provider
from backend.app.schemas.schemas import EligibilityResponse, MemberLookup
from backend.app.services import prognosis_client

router = APIRouter(tags=["members"])


@router.post("/verify-member", response_model=EligibilityResponse)
async def verify_member(
    body: MemberLookup,
    db: Session = Depends(get_db),
    provider: Provider = Depends(get_current_provider),
):
    # 1. Find member locally
    member = db.query(Member).filter(Member.enrollee_id == body.enrollee_id).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member with enrollee ID '{body.enrollee_id}' not found",
        )

    # 2. Check eligibility via Prognosis API
    eligibility = await prognosis_client.validate_enrollee_eligibility(
        cifno=body.enrollee_id,
        provider_id=provider.prognosis_provider_id,
    )

    prognosis_eligible = eligibility.get("is_eligible", False)
    prognosis_data = eligibility.get("prognosis_response")

    # 3. Determine final verification status
    if not prognosis_eligible:
        # Prognosis says ineligible — reject regardless of biometric
        return EligibilityResponse(
            member_id=member.member_id,
            enrollee_id=member.enrollee_id,
            name=member.name,
            dob=member.dob,
            gender=member.gender,
            nin=member.nin,
            biometric_registered=member.biometric_registered,
            prognosis_eligible=False,
            prognosis_data=prognosis_data,
            verification_status="INELIGIBLE",
            verification_reason=(
                eligibility.get("reason")
                or "Enrollee is not eligible for this provider on the Prognosis network. "
                "Contact the HMO for details."
            ),
        )

    if not member.biometric_registered:
        # Prognosis says eligible BUT no biometric on file — UNVERIFIED
        return EligibilityResponse(
            member_id=member.member_id,
            enrollee_id=member.enrollee_id,
            name=member.name,
            dob=member.dob,
            gender=member.gender,
            nin=member.nin,
            biometric_registered=False,
            prognosis_eligible=True,
            prognosis_data=prognosis_data,
            verification_status="UNVERIFIED",
            verification_reason=(
                "Enrollee is eligible on Prognosis but has NO biometric on file. "
                "Fingerprint capture is required before services can be rendered. "
                "Please enroll the member's fingerprint using the FS80H scanner."
            ),
        )

    # Prognosis eligible AND biometric registered — but still needs live scan
    return EligibilityResponse(
        member_id=member.member_id,
        enrollee_id=member.enrollee_id,
        name=member.name,
        dob=member.dob,
        gender=member.gender,
        nin=member.nin,
        biometric_registered=True,
        prognosis_eligible=True,
        prognosis_data=prognosis_data,
        verification_status="UNVERIFIED",
        verification_reason=(
            "Enrollee is eligible on Prognosis and has biometric on file. "
            "Fingerprint scan required to complete identity verification."
        ),
    )
