import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


# ── Auth ──────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    provider_id: uuid.UUID
    provider_name: str
    prognosis_provider_id: str  # Prognosis system provider ID


# ── Member / Eligibility ─────────────────────────────────────
class MemberLookup(BaseModel):
    enrollee_id: str  # CIF number used in Prognosis


class EligibilityResponse(BaseModel):
    """
    Combined response: Prognosis eligibility + local biometric status.
    Even if Prognosis says eligible, if biometric is not verified,
    the member is returned as UNVERIFIED.
    """
    member_id: uuid.UUID
    enrollee_id: str
    name: str
    dob: datetime | None = None
    gender: str | None = None
    nin: str | None = None
    biometric_registered: bool

    # Prognosis eligibility fields
    prognosis_eligible: bool
    prognosis_data: Any = None  # raw Prognosis API response

    # Final verification status
    verification_status: str  # ELIGIBLE | UNVERIFIED | INELIGIBLE
    verification_reason: str  # human-readable reason

    model_config = {"from_attributes": True}


class MemberResponse(BaseModel):
    member_id: uuid.UUID
    enrollee_id: str
    name: str
    dob: datetime | None = None
    gender: str | None = None
    nin: str | None = None
    biometric_registered: bool

    model_config = {"from_attributes": True}


# ── Biometric ─────────────────────────────────────────────────
class BiometricCaptureRequest(BaseModel):
    member_id: uuid.UUID
    fingerprint_template_b64: str  # base64-encoded ANSI 378 template from FS80H
    finger_position: str = "right_thumb"
    nin: str | None = None
    lfd_passed: bool = True
    image_quality: int = 0


class BiometricCaptureResponse(BaseModel):
    biometric_id: uuid.UUID
    member_id: uuid.UUID
    status: str  # "REGISTERED"
    message: str


# ── Fingerprint Validation ────────────────────────────────────
class FingerprintValidateRequest(BaseModel):
    member_id: uuid.UUID
    fingerprint_template_b64: str
    lfd_passed: bool = True
    image_quality: int = 0


class FingerprintValidateResponse(BaseModel):
    member_id: uuid.UUID
    match: bool
    verification_token: str | None = None
    verification_status: str  # ELIGIBLE | UNVERIFIED | DENIED
    verification_reason: str
    prognosis_data: Any = None
    message: str


# ── Visit / Claims ────────────────────────────────────────────
class LogVisitRequest(BaseModel):
    member_id: uuid.UUID
    provider_id: uuid.UUID
    verification_token: str


class VisitResponse(BaseModel):
    visit_id: uuid.UUID
    member_id: uuid.UUID
    provider_id: uuid.UUID
    verification_status: str
    timestamp: datetime

    model_config = {"from_attributes": True}


class ClaimValidationRequest(BaseModel):
    verification_token: str
    timestamp: datetime
    provider_id: uuid.UUID


class ClaimValidationResponse(BaseModel):
    valid: bool
    message: str
    visit_id: uuid.UUID | None = None


# ── Reimbursement Claims Status ──────────────────────────────
class ClaimsStatusRequest(BaseModel):
    enrollee_id: str  # CIF number


class ClaimsStatusResponse(BaseModel):
    enrollee_id: str
    success: bool
    reason: str | None = None
    claims: list[Any] = []
    total_claims: int = 0


# ══════════════════════════════════════════════════════════════
# Agent Auth
# ══════════════════════════════════════════════════════════════


class AgentLoginRequest(BaseModel):
    email: str
    password: str


class AgentTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    agent_id: uuid.UUID
    agent_name: str
    role: str


# ══════════════════════════════════════════════════════════════
# Authorization Codes
# ══════════════════════════════════════════════════════════════


class CreateAuthCodeRequest(BaseModel):
    enrollee_id: str = Field(..., min_length=1, max_length=50)
    approved_amount: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    visit_type: str = Field(..., min_length=1, max_length=100)
    notes: str | None = None


class AuthCodeResponse(BaseModel):
    id: uuid.UUID
    code: str
    member_id: uuid.UUID
    enrollee_id: str
    member_name: str | None = None
    approved_amount: Decimal
    visit_type: str
    notes: str | None = None
    agent_id: uuid.UUID
    agent_name: str
    status: str
    created_at: datetime
    expires_at: datetime
    linked_claim_id: uuid.UUID | None = None

    model_config = {"from_attributes": True}


class ValidateAuthCodeRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    enrollee_id: str = Field(..., min_length=1, max_length=50)


class ValidateAuthCodeResponse(BaseModel):
    valid: bool
    message: str
    code: str | None = None
    enrollee_id: str | None = None
    member_name: str | None = None
    approved_amount: Decimal | None = None
    visit_type: str | None = None
    expires_at: datetime | None = None


class AuthCodeListResponse(BaseModel):
    codes: list[AuthCodeResponse]
    total: int


# ══════════════════════════════════════════════════════════════
# Reimbursement Claims
# ══════════════════════════════════════════════════════════════


class ServiceLineItem(BaseModel):
    service_name: str = Field(..., min_length=1, max_length=200)
    quantity: int = Field(..., ge=1)
    unit_price: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)


class SubmitReimbursementRequest(BaseModel):
    authorization_code: str = Field(..., min_length=1, max_length=20)
    enrollee_id: str = Field(..., min_length=1, max_length=50)
    member_phone: str = Field(..., min_length=1, max_length=20)
    hospital_name: str = Field(..., min_length=1, max_length=300)
    visit_date: date
    reason_for_visit: str = Field(..., min_length=1)
    reimbursement_reason: str = Field(..., min_length=1)
    claim_amount: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    medications: str | None = None
    lab_investigations: str | None = None
    comments: str | None = None
    bank_name: str = Field(..., min_length=1, max_length=200)
    account_number: str = Field(..., min_length=1, max_length=20)
    account_name: str = Field(..., min_length=1, max_length=200)
    service_lines: list[ServiceLineItem] = Field(default_factory=list)


class ReimbursementClaimResponse(BaseModel):
    claim_id: uuid.UUID
    claim_ref: str
    enrollee_id: str
    member_name: str
    hospital_name: str
    claim_amount: Decimal
    status: str
    authorization_code: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ClaimDetailResponse(BaseModel):
    claim_id: uuid.UUID
    claim_ref: str
    enrollee_id: str
    member_name: str
    member_phone: str
    hospital_name: str
    visit_date: date
    reason_for_visit: str
    reimbursement_reason: str
    claim_amount: Decimal
    medications: str | None = None
    lab_investigations: str | None = None
    comments: str | None = None
    bank_name: str
    account_number: str
    account_name: str
    status: str
    approved_amount: Decimal | None = None
    reviewer_notes: str | None = None
    authorization_code: str | None = None
    agent_name: str | None = None
    service_lines: list[ServiceLineItem] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UpdateClaimStatusRequest(BaseModel):
    status: str = Field(
        ...,
        pattern="^(under_review|pending_info|approved|rejected|payment_processing|paid)$",
    )
    approved_amount: Decimal | None = None
    reviewer_notes: str | None = None


class ClaimsListResponse(BaseModel):
    claims: list[ReimbursementClaimResponse]
    total: int


# ══════════════════════════════════════════════════════════════
# Audit
# ══════════════════════════════════════════════════════════════


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    action: str
    actor_type: str
    actor_id: str
    details: dict | None = None
    ip_address: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
