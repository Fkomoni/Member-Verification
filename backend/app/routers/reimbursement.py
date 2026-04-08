"""
Reimbursement endpoints — public-facing Member Portal.

No JWT auth required. The authorization code is the credential.
"""

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limiter import (
    get_client_ip,
    member_lookup_limiter,
    submission_limiter,
)
from app.core.security import mask_account_number, mask_phone, sanitize_text
from app.schemas.schemas import ReimbursementClaimResponse, SubmitReimbursementRequest
from app.services import (
    audit_service,
    authorization_service,
    claim_service,
    email_service,
    mock_bank_service,
    mock_member_service,
)

log = logging.getLogger(__name__)

router = APIRouter(prefix="/reimbursement", tags=["reimbursement"])


# ── Request / Response models ──────────────────────────────


class ValidateMemberRequest(BaseModel):
    enrollee_id: str = Field(..., min_length=1, max_length=50)


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
    Step 1: Validate member identity by enrollee ID.
    Public endpoint — no auth required.
    Rate-limited: 10 attempts per IP per 15 minutes.
    """
    client_ip = get_client_ip(request)
    member_lookup_limiter.check_and_record(f"member:{client_ip}")

    member_data = mock_member_service.lookup_member(
        db, enrollee_id=body.enrollee_id
    )
    is_valid = member_data is not None
    message = "Member found." if is_valid else "Member not found. Please check your Enrollee ID."

    # Audit
    audit_service.log_action(
        db,
        entity_type="member_validation",
        entity_id=body.enrollee_id,
        action="member_lookup",
        actor_type="member",
        actor_id=body.enrollee_id,
        details={"valid": is_valid},
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
async def submit_reimbursement(
    request: Request,
    data: str = Form(...),
    receipts: list[UploadFile] = File(default=[]),
    medical_reports: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
):
    """
    Submit a reimbursement claim with document attachments.

    Accepts multipart form data:
    - data: JSON string of SubmitReimbursementRequest fields
    - receipts: Receipt/invoice files (mandatory)
    - medical_reports: Medical report files (mandatory for secondary care)

    Files are read into memory, attached to the claims email, then DISCARDED.
    No file persistence anywhere.

    Rate-limited: 3 submissions per IP per 30 minutes.
    Duplicate guard: rejects if auth code already used.
    """
    # Rate limit
    client_ip = get_client_ip(request)
    submission_limiter.check_and_record(f"submit:{client_ip}")

    # Parse JSON form data
    try:
        body = SubmitReimbursementRequest(**json.loads(data))
    except (json.JSONDecodeError, Exception) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid form data: {e}",
        )

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

    # 5. Read files into memory (then discard after email)
    attachments: list[tuple[str, bytes, str]] = []
    all_files = [("receipt", f) for f in receipts] + [("report", f) for f in medical_reports]

    for label, upload_file in all_files:
        if upload_file.filename:
            file_bytes = await upload_file.read()
            content_type = upload_file.content_type or "application/octet-stream"
            attachments.append((upload_file.filename, file_bytes, content_type))
            log.info(
                "File received: %s (%s, %d bytes) — will attach to email",
                upload_file.filename,
                content_type,
                len(file_bytes),
            )

    # 6. Send email with all claim data + attachments
    email_data = {
        "claim_ref": claim.claim_ref,
        "member_name": member_name,
        "enrollee_id": body.enrollee_id,
        "member_phone": body.member_phone,
        "authorization_code": auth_code.code,
        "approved_amount": float(auth_code.approved_amount),
        "agent_name": auth_code.agent_name,
        "claim_amount": float(body.claim_amount),
        "hospital_name": body.hospital_name,
        "visit_date": str(body.visit_date),
        "reason_for_visit": body.reason_for_visit,
        "reimbursement_reason": body.reimbursement_reason,
        "medications": body.medications,
        "lab_investigations": body.lab_investigations,
        "comments": body.comments,
        "bank_name": body.bank_name,
        "account_number": body.account_number,
        "account_name": body.account_name,
        "service_lines": service_lines,
        "amount_flag": amount_flag,
    }

    email_sent = email_service.send_claim_email(
        claim_data=email_data,
        attachments=attachments,
    )

    # 7. Audit trail
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
            "attachments_count": len(attachments),
            "email_sent": email_sent,
            "bank": body.bank_name,
            "account_number_masked": mask_account_number(body.account_number),
            "phone_masked": mask_phone(body.member_phone),
        },
        ip_address=client_ip,
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

    # Files are now out of scope — garbage collected, never stored
    return SubmitClaimResponse(
        success=True,
        message=f"Claim submitted successfully. Reference: {claim.claim_ref}"
        + (f" Note: {amount_flag}" if amount_flag else ""),
        claim_id=str(claim.claim_id),
        claim_ref=claim.claim_ref,
    )
