"""
Pydantic schemas for the medication routing module.

Phase 1: Drug Master
Phase 2: Medication Request Submission
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


# ── Drug Master Schemas ──────────────────────────────────────────

class DrugAliasOut(BaseModel):
    alias_id: uuid.UUID
    alias_name: str
    alias_type: str

    model_config = {"from_attributes": True}


class DrugMasterOut(BaseModel):
    drug_id: uuid.UUID
    generic_name: str
    category: str
    common_brand_names: str | None = None
    therapeutic_class: str | None = None
    requires_review: bool
    source: str
    is_active: bool
    aliases: list[DrugAliasOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DrugMasterListOut(BaseModel):
    total: int
    page: int
    per_page: int
    drugs: list[DrugMasterOut]


class DrugSearchResult(BaseModel):
    """Lightweight result for drug search/autocomplete."""
    drug_id: uuid.UUID
    generic_name: str
    category: str
    common_brand_names: str | None = None
    therapeutic_class: str | None = None
    requires_review: bool
    match_type: str = Field(
        description="How the match was found: generic | alias | brand",
    )

    model_config = {"from_attributes": True}


class DrugSearchResponse(BaseModel):
    query: str
    results: list[DrugSearchResult]
    total: int


# ── Drug Master Admin (for future use) ──────────────────────────

class DrugMasterCreate(BaseModel):
    generic_name: str
    category: str = "unknown"
    common_brand_names: str | None = None
    therapeutic_class: str | None = None
    requires_review: bool = False
    notes: str | None = None
    source: str = "manual"


class DrugAliasCreate(BaseModel):
    alias_name: str
    alias_type: str = "brand"


# ── Nigerian Location Schemas ────────────────────────────────────

class StateOut(BaseModel):
    name: str
    is_lagos: bool


class LgaOut(BaseModel):
    name: str
    state: str


class LocationListOut(BaseModel):
    states: list[StateOut]


class LgaListOut(BaseModel):
    state: str
    lgas: list[str]


# ── Medication Request Schemas (Phase 2) ─────────────────────────

class MedicationItemIn(BaseModel):
    """A single medication line in a request submission."""
    drug_name: str = Field(..., min_length=1, max_length=300)
    generic_name: str | None = None
    matched_drug_id: uuid.UUID | None = None
    strength: str | None = None
    dosage_instruction: str = Field(..., min_length=1)
    duration: str = Field(..., min_length=1, max_length=100)
    quantity: str = Field(..., min_length=1, max_length=100)
    route: str | None = None


class MedicationRequestIn(BaseModel):
    """Payload for creating a new medication request."""
    enrollee_id: str = Field(..., min_length=1, max_length=50)
    enrollee_name: str = Field(..., min_length=1, max_length=200)
    enrollee_dob: datetime | None = None
    enrollee_gender: str | None = None
    member_phone: str = Field(..., min_length=1, max_length=30)
    member_email: str | None = None
    diagnosis: str = Field(..., min_length=1)
    treating_doctor: str = Field(default="Not specified", max_length=200)
    doctor_phone: str | None = None
    provider_notes: str | None = None

    # Delivery location
    delivery_state: str = Field(..., min_length=1, max_length=100)
    delivery_lga: str | None = None
    delivery_city: str | None = None
    delivery_address: str | None = None
    delivery_landmark: str | None = None

    urgency: str = Field(default="routine")
    facility_name: str = Field(..., min_length=1, max_length=300)
    facility_branch: str | None = None

    # Medication lines — at least one required
    medications: list[MedicationItemIn] = Field(..., min_length=1)

    @field_validator("urgency")
    @classmethod
    def validate_urgency(cls, v: str) -> str:
        allowed = {"routine", "urgent", "emergency"}
        if v.lower() not in allowed:
            raise ValueError(f"urgency must be one of {allowed}")
        return v.lower()


class MedicationItemOut(BaseModel):
    item_id: uuid.UUID
    drug_name: str
    generic_name: str | None = None
    matched_drug_id: uuid.UUID | None = None
    strength: str | None = None
    dosage_instruction: str
    duration: str
    quantity: str
    route: str | None = None
    item_category: str | None = None
    requires_review: bool
    classification_confidence: float | None = None
    classification_source: str | None = None

    model_config = {"from_attributes": True}


# ── Classification Schemas (Phase 3) ─────────────────────────────

class ClassificationResultOut(BaseModel):
    classification_id: uuid.UUID
    request_id: uuid.UUID
    classification: str  # acute | chronic | mixed | review_required
    acute_count: int
    chronic_count: int
    unknown_count: int
    review_required: bool
    confidence: float | None = None
    reasoning: str | None = None
    classified_by: str
    classified_at: datetime

    model_config = {"from_attributes": True}


class ClassificationSummaryOut(BaseModel):
    """Lightweight classification info embedded in request responses."""
    classification: str
    acute_count: int
    chronic_count: int
    unknown_count: int
    review_required: bool
    confidence: float | None = None
    reasoning: str | None = None

    model_config = {"from_attributes": True}


# ── Routing Schemas (Phase 4) ────────────────────────────────────

class RoutingSummaryOut(BaseModel):
    """Lightweight routing info embedded in request responses."""
    destination: str  # wellahealth | whatsapp_lagos | whatsapp_outside_lagos | manual_review
    reasoning: str | None = None
    is_lagos: bool | None = None

    model_config = {"from_attributes": True}


class MedicationRequestOut(BaseModel):
    request_id: uuid.UUID
    reference_number: str
    enrollee_id: str
    enrollee_name: str
    enrollee_dob: datetime | None = None
    enrollee_gender: str | None = None
    member_phone: str | None = None
    member_email: str | None = None
    diagnosis: str
    treating_doctor: str
    doctor_phone: str | None = None
    provider_notes: str | None = None
    delivery_state: str
    delivery_lga: str
    delivery_city: str | None = None
    delivery_address: str | None = None
    delivery_landmark: str | None = None
    is_lagos: bool | None = None
    urgency: str
    status: str
    facility_name: str
    facility_branch: str | None = None
    items: list[MedicationItemOut] = []
    classification: ClassificationSummaryOut | None = None
    routing: RoutingSummaryOut | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MedicationRequestListOut(BaseModel):
    total: int
    page: int
    per_page: int
    requests: list[MedicationRequestOut]
