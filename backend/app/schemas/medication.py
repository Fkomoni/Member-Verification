"""
Pydantic schemas for the medication routing module — Phase 1: Drug Master.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


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
