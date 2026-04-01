import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Date, DateTime, Integer, Numeric, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Medication(Base):
    __tablename__ = "medications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = Column(String(50), ForeignKey("members.member_id", ondelete="CASCADE"), nullable=False, index=True)
    drug_name = Column(String(200), nullable=False)
    generic_name = Column(String(200))
    dosage = Column(String(100), nullable=False)
    frequency = Column(String(100), nullable=False)
    route = Column(String(50))
    prescriber = Column(String(200))
    start_date = Column(Date)
    end_date = Column(Date)
    is_covered = Column(Boolean, default=True)
    coverage_pct = Column(Numeric(5, 2), default=100.00)
    copay_amount = Column(Numeric(10, 2), default=0.00)
    refill_count = Column(Integer, default=0)
    max_refills = Column(Integer, default=12)
    last_refill_at = Column(DateTime(timezone=True))
    next_refill_due = Column(Date)
    days_supply = Column(Integer, default=30)
    quantity = Column(Integer)
    status = Column(String(20), default="ACTIVE")
    pbm_drug_id = Column(String(100))
    pbm_synced_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    member = relationship("Member", back_populates="medications")
