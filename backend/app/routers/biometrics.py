"""
POST /capture-biometric    – Enroll a new fingerprint (Futronic FS80H)
POST /validate-fingerprint – Verify live scan, then check Prognosis eligibility.
                             Only returns ELIGIBLE if BOTH biometric matches AND
                             Prognosis confirms enrollee access.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_provider
from app.core.security import create_access_token
from app.models.models import (
    Biometric,
    Member,
    Provider,
    VerificationLog,
    Visit,
)
from app.schemas.schemas import (
    BiometricCaptureRequest,
    BiometricCaptureResponse,
    FingerprintValidateRequest,
    FingerprintValidateResponse,
)
from app.services.biometric_service import compare_templates, encrypt_template
from app.services import prognosis_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["biometrics"])

MIN_IMAGE_QUALITY = 40


def _enforce_lfd(lfd_passed: bool):
    if settings.REQUIRE_LFD and not lfd_passed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Live Finger Detection failed — the scanner detected a fake finger. "
                "Only real fingers are accepted. Clean the scanner surface and try again."
            ),
        )


def _enforce_quality(quality: int):
    if quality > 0 and quality < MIN_IMAGE_QUALITY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Fingerprint image quality too low ({quality}/100). "
                "Clean the finger and scanner, press firmly and hold still."
            ),
        )


@router.post("/capture-biometric", response_model=BiometricCaptureResponse)
def capture_biometric(
    body: BiometricCaptureRequest,
    db: Session = Depends(get_db),
    provider: Provider = Depends(get_current_provider),
):
    _enforce_lfd(body.lfd_passed)
    _enforce_quality(body.image_quality)

    member = db.query(Member).filter(Member.member_id == body.member_id).first()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    if member.biometric_registered:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Biometric already registered for this member",
        )

    encrypted = encrypt_template(body.fingerprint_template_b64)

    biometric = Biometric(
        member_id=member.member_id,
        fingerprint_template=encrypted,
        finger_position=body.finger_position,
    )
    db.add(biometric)

    member.biometric_registered = True
    if body.nin:
        member.nin = body.nin

    audit = VerificationLog(
        member_id=member.member_id,
        provider_id=provider.provider_id,
        match_status="NEW_ENROLLMENT",
        device_id=provider.device_id,
    )
    db.add(audit)
    db.commit()
    db.refresh(biometric)

    logger.info(
        "Biometric enrolled: member=%s provider=%s quality=%d lfd=%s",
        member.member_id, provider.provider_id, body.image_quality, body.lfd_passed,
    )

    return BiometricCaptureResponse(
        biometric_id=biometric.biometric_id,
        member_id=member.member_id,
        status="REGISTERED",
        message="Biometric enrolled successfully via Futronic FS80H",
    )


@router.post("/validate-fingerprint", response_model=FingerprintValidateResponse)
async def validate_fingerprint(
    body: FingerprintValidateRequest,
    db: Session = Depends(get_db),
    provider: Provider = Depends(get_current_provider),
):
    _enforce_lfd(body.lfd_passed)
    _enforce_quality(body.image_quality)

    member = db.query(Member).filter(Member.member_id == body.member_id).first()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    if not member.biometric_registered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No biometric on file. Capture fingerprint first.",
        )

    stored = (
        db.query(Biometric)
        .filter(Biometric.member_id == member.member_id)
        .order_by(Biometric.date_created.desc())
        .first()
    )
    if not stored:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Biometric record missing")

    matched = compare_templates(body.fingerprint_template_b64, stored.fingerprint_template)

    if not matched:
        # Biometric mismatch — DENIED
        audit = VerificationLog(
            member_id=member.member_id,
            provider_id=provider.provider_id,
            match_status="NO_MATCH",
            device_id=provider.device_id,
        )
        db.add(audit)

        visit = Visit(
            member_id=member.member_id,
            provider_id=provider.provider_id,
            verification_status="DENIED",
        )
        db.add(visit)
        db.commit()

        logger.warning("NO_MATCH: member=%s provider=%s", member.member_id, provider.provider_id)

        await prognosis_client.flag_impersonation(
            str(member.member_id), str(provider.provider_id)
        )

        return FingerprintValidateResponse(
            member_id=member.member_id,
            match=False,
            verification_status="DENIED",
            verification_reason="Fingerprint does not match the enrolled biometric.",
            message=(
                "Fingerprint mismatch — access denied. "
                "This incident has been flagged for HMO review."
            ),
        )

    # Biometric MATCHED — now check Prognosis eligibility
    eligibility = await prognosis_client.validate_enrollee_eligibility(
        cifno=member.enrollee_id,
        provider_id=provider.prognosis_provider_id,
    )

    prognosis_eligible = eligibility.get("is_eligible", False)
    prognosis_data = eligibility.get("prognosis_response")

    if not prognosis_eligible:
        # Biometric matched but Prognosis says NOT eligible — INELIGIBLE
        audit = VerificationLog(
            member_id=member.member_id,
            provider_id=provider.provider_id,
            match_status="MATCH",
            device_id=provider.device_id,
        )
        db.add(audit)

        visit = Visit(
            member_id=member.member_id,
            provider_id=provider.provider_id,
            verification_status="DENIED",
        )
        db.add(visit)
        db.commit()

        reason = eligibility.get("reason") or (
            "Enrollee identity confirmed via biometric, but Prognosis reports "
            "the enrollee is NOT ELIGIBLE for this provider. Contact the HMO."
        )

        logger.warning(
            "MATCH but INELIGIBLE: member=%s provider=%s reason=%s",
            member.member_id, provider.provider_id, reason,
        )

        return FingerprintValidateResponse(
            member_id=member.member_id,
            match=True,
            verification_status="INELIGIBLE",
            verification_reason=reason,
            prognosis_data=prognosis_data,
            message=(
                "Identity confirmed via fingerprint, but enrollee is NOT ELIGIBLE "
                "on the Prognosis network for this provider."
            ),
        )

    # BOTH biometric matched AND Prognosis eligible — FULL APPROVAL
    verification_token = create_access_token(
        data={
            "type": "visit_verification",
            "member_id": str(member.member_id),
            "provider_id": str(provider.provider_id),
        }
    )

    visit = Visit(
        member_id=member.member_id,
        provider_id=provider.provider_id,
        verification_token=verification_token,
        verification_status="APPROVED",
    )
    db.add(visit)

    audit = VerificationLog(
        member_id=member.member_id,
        provider_id=provider.provider_id,
        match_status="MATCH",
        device_id=provider.device_id,
    )
    db.add(audit)
    db.commit()

    logger.info(
        "ELIGIBLE: member=%s provider=%s (biometric + Prognosis verified)",
        member.member_id, provider.provider_id,
    )

    return FingerprintValidateResponse(
        member_id=member.member_id,
        match=True,
        verification_token=verification_token,
        verification_status="ELIGIBLE",
        verification_reason="Identity verified via biometric and Prognosis eligibility confirmed.",
        prognosis_data=prognosis_data,
        message="Member verified — check-in approved.",
    )
