import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = Column(String(50), ForeignKey("members.member_id", ondelete="CASCADE"), nullable=False, index=True)
    medication_id = Column(UUID(as_uuid=True), ForeignKey("medications.id"))
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="NGN")
    payment_type = Column(String(30), nullable=False)
    gateway = Column(String(30), default="PAYSTACK")
    gateway_ref = Column(String(200))
    gateway_status = Column(String(30))
    status = Column(String(20), default="PENDING")
    metadata = Column(JSONB, default={})
    paid_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    member = relationship("Member", back_populates="payments")
