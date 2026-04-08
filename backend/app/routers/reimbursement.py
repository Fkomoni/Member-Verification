"""
Reimbursement endpoints — public-facing Member Portal.

No JWT auth required. The authorization code is the credential.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schemas import ReimbursementClaimResponse, SubmitReimbursementRequest
from app.services import (
    audit_service,
    authorization_service,
    claim_service,
    mock_bank_service,
    mock_member_service,
)

log = logging.getLogger(__name__)

router = APIRouter(prefix="/reimbursement", tags=["reimbursement"])


# ── Request / Response models ──────────────────────────────


class ValidateMemberRequest(BaseModel):
    enrollee_id: str = Field(..., min_length=1, max_length=50)
    phone: str = Field(..., min_length=1, max_length=20)


class ValidateMemberResponse(BaseModel):
    valid: bool
    message: str
    member_name: str | None = None
    enrollee_id: str | None = None
    gender: str | None = None
    plan: str | None = None


class ValidateBankRequest(BaseModel):
    bank_name: str = Field(..., min_length=1)
    account_number: str = Field(..., min_length=10, max_length=10)


class ValidateBankResponse(BaseModel):
    valid: bool
    account_name: str | None = None
    message: str


class BankListResponse(BaseModel):
    banks: list[str]


class SubmitClaimResponse(BaseModel):
    success: bool
    message: str
    claim_id: str | None = None
    claim_ref: str | None = None


# ── Endpoints ──────────────────────────────────────────────


@router.post("/validate-member", response_model=ValidateMemberResponse)
def validate_member(
    body: ValidateMemberRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Step 1: Validate member identity (enrollee ID + phone).
    Public endpoint — no auth required.
    """
    is_valid, message, member_data = mock_member_service.validate_member_phone(
        db, enrollee_id=body.enrollee_id, phone=body.phone
    )

    # Audit
    audit_service.log_action(
        db,
        entity_type="member_validation",
        entity_id=body.enrollee_id,
        action="member_identity_check",
        actor_type="member",
        actor_id=body.enrollee_id,
        details={"phone_provided": body.phone[:4] + "****", "valid": is_valid},
        ip_address=request.client.host if request.client else None,
    )

    if not is_valid:
        return ValidateMemberResponse(valid=False, message=message)

    return ValidateMemberResponse(
        valid=True,
        message=message,
        member_name=member_data.get("name"),
        enrollee_id=member_data.get("enrollee_id"),
        gender=member_data.get("gender"),
        plan=member_data.get("plan"),
    )


@router.get("/banks", response_model=BankListResponse)
def list_banks():
    """Return list of supported Nigerian banks."""
    return BankListResponse(banks=mock_bank_service.get_bank_list())


@router.post("/validate-bank", response_model=ValidateBankResponse)
def validate_bank(body: ValidateBankRequest):
    """
    Validate bank account and resolve account holder name.
    PLACEHOLDER: Uses mock service — will integrate real bank API later.
    """
    result = mock_bank_service.validate_bank_account(
        bank_name=body.bank_name,
        account_number=body.account_number,
    )
    return ValidateBankResponse(**result)


@router.post("/submit", response_model=SubmitClaimResponse)
def submit_reimbursement(
    body: SubmitReimbursementRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Submit a reimbursement claim.

    Validates:
    1. Authorization code is valid and matches the enrollee
    2. Claim amount does not exceed approved amount (flags if it does)
    3. All required fields are present

    Creates the claim, marks the auth code as used, and audits everything.
    """
    # 1. Validate authorization code
    is_valid, message, auth_code = authorization_service.validate_authorization_code(
        db, code=body.authorization_code, enrollee_id=body.enrollee_id
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authorization code invalid: {message}",
        )

    # 2. Check claim amount vs approved amount
    amount_flag = None
    if float(body.claim_amount) > float(auth_code.approved_amount):
        amount_flag = (
            f"Claim amount ({body.claim_amount}) exceeds approved amount "
            f"({auth_code.approved_amount}). Flagged for review."
        )
        log.warning("Amount flag: %s for code %s", amount_flag, auth_code.code)

    # 3. Look up member name
    member_data = mock_member_service.lookup_member(db, enrollee_id=body.enrollee_id)
    member_name = member_data["name"] if member_data else body.enrollee_id

    # 4. Create claim
    service_lines = [
        {
            "service_name": sl.service_name,
            "quantity": sl.quantity,
            "unit_price": float(sl.unit_price),
        }
        for sl in body.service_lines
    ]

    claim = claim_service.create_claim(
        db,
        auth_code=auth_code,
        member_name=member_name,
        member_phone=body.member_phone,
        hospital_name=body.hospital_name,
        visit_date=body.visit_date,
        reason_for_visit=body.reason_for_visit,
        reimbursement_reason=body.reimbursement_reason,
        claim_amount=float(body.claim_amount),
        medications=body.medications,
        lab_investigations=body.lab_investigations,
        comments=body.comments,
        bank_name=body.bank_name,
        account_number=body.account_number,
        account_name=body.account_name,
        service_lines=service_lines,
    )

    # 5. Audit trail
    audit_service.log_action(
        db,
        entity_type="claim",
        entity_id=str(claim.claim_id),
        action="submitted",
        actor_type="member",
        actor_id=body.enrollee_id,
        details={
            "claim_ref": claim.claim_ref,
            "authorization_code": auth_code.code,
            "claim_amount": float(body.claim_amount),
            "approved_amount": float(auth_code.approved_amount),
            "amount_flag": amount_flag,
            "hospital": body.hospital_name,
            "service_lines_count": len(service_lines),
        },
        ip_address=request.client.host if request.client else None,
    )

    audit_service.log_action(
        db,
        entity_type="authorization_code",
        entity_id=str(auth_code.id),
        action="used",
        actor_type="member",
        actor_id=body.enrollee_id,
        details={"linked_claim_ref": claim.claim_ref},
        ip_address=request.client.host if request.client else None,
    )

    # 6. PLACEHOLDER: Send email with documents (Phase 5)
    log.info(
        "PLACEHOLDER: Email with claim %s documents would be sent to claims team",
        claim.claim_ref,
    )

    return SubmitClaimResponse(
        success=True,
        message=f"Claim submitted successfully. Reference: {claim.claim_ref}"
        + (f" Note: {amount_flag}" if amount_flag else ""),
        claim_id=str(claim.claim_id),
        claim_ref=claim.claim_ref,
    )
