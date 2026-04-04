from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class HealthReadingCreate(BaseModel):
    reading_type: str = Field(..., pattern="^(BLOOD_PRESSURE|BLOOD_GLUCOSE|CHOLESTEROL)$")
    systolic: Optional[Decimal] = None
    diastolic: Optional[Decimal] = None
    glucose_level: Optional[Decimal] = None
    glucose_context: Optional[str] = Field(None, pattern="^(FASTING|RANDOM|POST_MEAL)$")
    total_cholesterol: Optional[Decimal] = None
    hdl: Optional[Decimal] = None
    ldl: Optional[Decimal] = None
    triglycerides: Optional[Decimal] = None
    notes: Optional[str] = None
    recorded_at: Optional[datetime] = None


class HealthReadingOut(BaseModel):
    id: UUID
    member_id: str
    reading_type: str
    systolic: Optional[Decimal] = None
    diastolic: Optional[Decimal] = None
    glucose_level: Optional[Decimal] = None
    glucose_context: Optional[str] = None
    total_cholesterol: Optional[Decimal] = None
    hdl: Optional[Decimal] = None
    ldl: Optional[Decimal] = None
    triglycerides: Optional[Decimal] = None
    notes: Optional[str] = None
    recorded_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
