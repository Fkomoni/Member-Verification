"""
POST /capture-biometric  – Enroll a new fingerprint
POST /validate-fingerprint – Verify a live scan against stored template
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_provider
from backend.app.core.security import create_access_token
from backend.app.models.models import (
    Biometric,
    Member,
    Provider,
    VerificationLog,
    Visit,
)
from backend.app.schemas.schemas import (
    BiometricCaptureRequest,
    BiometricCaptureResponse,
    FingerprintValidateRequest,
    FingerprintValidateResponse,
)
from backend.app.services.biometric_service import compare_templates, encrypt_template
from backend.app.services import prognosis_client

router = APIRouter(tags=["biometrics"])


@router.post("/capture-biometric", response_model=BiometricCaptureResponse)
def capture_biometric(
    body: BiometricCaptureRequest,
    db: Session = Depends(get_db),
    provider: Provider = Depends(get_current_provider),
):
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

    # Audit log
    log = VerificationLog(
        member_id=member.member_id,
        provider_id=provider.provider_id,
        match_status="NEW_ENROLLMENT",
        device_id=provider.device_id,
    )
    db.add(log)
    db.commit()
    db.refresh(biometric)

    return BiometricCaptureResponse(
        biometric_id=biometric.biometric_id,
        member_id=member.member_id,
        status="REGISTERED",
        message="Biometric enrolled successfully",
    )


@router.post("/validate-fingerprint", response_model=FingerprintValidateResponse)
async def validate_fingerprint(
    body: FingerprintValidateRequest,
    db: Session = Depends(get_db),
    provider: Provider = Depends(get_current_provider),
):
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

    if matched:
        # Generate verification token (signed JWT with visit context)
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

        log = VerificationLog(
            member_id=member.member_id,
            provider_id=provider.provider_id,
            match_status="MATCH",
            device_id=provider.device_id,
        )
        db.add(log)
        db.commit()

        return FingerprintValidateResponse(
            member_id=member.member_id,
            match=True,
            verification_token=verification_token,
            message="Identity verified – check-in approved",
        )
    else:
        log = VerificationLog(
            member_id=member.member_id,
            provider_id=provider.provider_id,
            match_status="NO_MATCH",
            device_id=provider.device_id,
        )
        db.add(log)

        visit = Visit(
            member_id=member.member_id,
            provider_id=provider.provider_id,
            verification_status="DENIED",
        )
        db.add(visit)
        db.commit()

        # Notify Prognosis of potential impersonation
        await prognosis_client.flag_impersonation(
            str(member.member_id), str(provider.provider_id)
        )

        return FingerprintValidateResponse(
            member_id=member.member_id,
            match=False,
            message="Fingerprint mismatch – access denied. Flagged for HMO review.",
        )
