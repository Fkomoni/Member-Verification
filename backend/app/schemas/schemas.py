import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


# ── Auth ──────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    provider_id: uuid.UUID
    provider_name: str


# ── Member ────────────────────────────────────────────────────
class MemberLookup(BaseModel):
    enrollee_id: str


class MemberResponse(BaseModel):
    member_id: uuid.UUID
    enrollee_id: str
    name: str
    dob: datetime | None
    gender: str | None
    nin: str | None
    biometric_registered: bool

    model_config = {"from_attributes": True}


# ── Biometric ─────────────────────────────────────────────────
class BiometricCaptureRequest(BaseModel):
    member_id: uuid.UUID
    fingerprint_template_b64: str  # base64-encoded template from device SDK
    finger_position: str = "right_thumb"
    nin: str | None = None


class BiometricCaptureResponse(BaseModel):
    biometric_id: uuid.UUID
    member_id: uuid.UUID
    status: str  # "REGISTERED"
    message: str


# ── Fingerprint Validation ────────────────────────────────────
class FingerprintValidateRequest(BaseModel):
    member_id: uuid.UUID
    fingerprint_template_b64: str  # base64-encoded live scan


class FingerprintValidateResponse(BaseModel):
    member_id: uuid.UUID
    match: bool
    verification_token: str | None = None
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
