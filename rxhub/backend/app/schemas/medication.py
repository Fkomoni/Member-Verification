from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal


class MedicationOut(BaseModel):
    id: UUID
    member_id: str
    drug_name: str
    generic_name: Optional[str] = None
    dosage: str
    frequency: str
    route: Optional[str] = None
    prescriber: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_covered: bool
    coverage_pct: Optional[Decimal] = None
    copay_amount: Optional[Decimal] = None
    refill_count: int
    max_refills: int
    last_refill_at: Optional[datetime] = None
    next_refill_due: Optional[date] = None
    days_supply: int
    quantity: Optional[int] = None
    status: str
    days_until_runout: Optional[int] = None

    model_config = {"from_attributes": True}


class MedicationAddPayload(BaseModel):
    drug_name: str
    dosage: str
    frequency: str
    route: Optional[str] = None
    prescriber: Optional[str] = None
    comment: str
    # attachment_url provided via file upload


class MedicationRemovePayload(BaseModel):
    medication_id: str
    reason: str


class MedicationModifyPayload(BaseModel):
    medication_id: str
    new_dosage: Optional[str] = None
    new_frequency: Optional[str] = None
    comment: str
