from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class PaymentInitiate(BaseModel):
    medication_id: Optional[str] = None
    amount: Decimal
    payment_type: str
    metadata: Optional[dict] = None


class PaymentVerify(BaseModel):
    gateway_ref: str


class PaymentOut(BaseModel):
    id: UUID
    member_id: str
    medication_id: Optional[UUID] = None
    amount: Decimal
    currency: str
    payment_type: str
    gateway: str
    gateway_ref: Optional[str] = None
    status: str
    paid_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
