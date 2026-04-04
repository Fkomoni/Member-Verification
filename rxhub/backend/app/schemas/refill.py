from pydantic import BaseModel
from typing import Optional
from datetime import date


class RefillRequest(BaseModel):
    medication_id: str
    comment: Optional[str] = None


class RefillSuspendRequest(BaseModel):
    medication_id: str
    suspend_until: Optional[date] = None  # None = indefinitely
    reason: Optional[str] = None


class RefillResumeRequest(BaseModel):
    medication_id: str
    comment: Optional[str] = None


class RefillIntelligence(BaseModel):
    medication_id: str
    drug_name: str
    days_remaining: Optional[int] = None
    next_refill_due: Optional[date] = None
    refills_remaining: int
    status: str
    alert: Optional[str] = None
