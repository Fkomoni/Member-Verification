"""
POST /log-visit       – Record a verified visit (for claims)
POST /validate-claim  – Check if a claim has a valid verification token
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_provider
from app.core.security import decode_access_token
from app.models.models import Provider, Visit
from app.schemas.schemas import (
    ClaimValidationRequest,
    ClaimValidationResponse,
    LogVisitRequest,
    VisitResponse,
)

router = APIRouter(tags=["visits"])


@router.post("/log-visit", response_model=VisitResponse)
def log_visit(
    body: LogVisitRequest,
    db: Session = Depends(get_db),
    provider: Provider = Depends(get_current_provider),
):
    # Validate the verification token
    payload = decode_access_token(body.verification_token)
    if not payload or payload.get("type") != "visit_verification":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    token_member = payload.get("member_id")
    token_provider = payload.get("provider_id")

    if token_member != str(body.member_id) or token_provider != str(body.provider_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token does not match the supplied member/provider",
        )

    visit = (
        db.query(Visit)
        .filter(
            Visit.member_id == body.member_id,
            Visit.provider_id == body.provider_id,
            Visit.verification_token == body.verification_token,
        )
        .first()
    )
    if not visit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")

    return visit


@router.post("/validate-claim", response_model=ClaimValidationResponse)
def validate_claim(
    body: ClaimValidationRequest,
    db: Session = Depends(get_db),
    provider: Provider = Depends(get_current_provider),
):
    """
    Claims validation rule: a claim must include a valid verification token,
    timestamp, and provider ID.  If no valid verification exists → reject.
    """
    payload = decode_access_token(body.verification_token)
    if not payload or payload.get("type") != "visit_verification":
        return ClaimValidationResponse(valid=False, message="Invalid or expired verification token")

    if payload.get("provider_id") != str(body.provider_id):
        return ClaimValidationResponse(valid=False, message="Provider ID mismatch")

    visit = (
        db.query(Visit)
        .filter(
            Visit.verification_token == body.verification_token,
            Visit.verification_status == "APPROVED",
        )
        .first()
    )
    if not visit:
        return ClaimValidationResponse(valid=False, message="No approved visit found for this token")

    return ClaimValidationResponse(
        valid=True,
        message="Claim verified successfully",
        visit_id=visit.visit_id,
    )
