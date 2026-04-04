import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


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
