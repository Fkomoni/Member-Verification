import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Date, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Member(Base):
    __tablename__ = "members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255))
    phone = Column(String(20), nullable=False, index=True)
    date_of_birth = Column(Date)
    gender = Column(String(10))
    diagnosis = Column(Text)
    plan_type = Column(String(50))
    plan_name = Column(String(100))
    employer = Column(String(200))
    status = Column(String(20), default="ACTIVE")
    pbm_synced_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    medications = relationship("Medication", back_populates="member", lazy="dynamic")
    requests = relationship("Request", back_populates="member", lazy="dynamic")
    payments = relationship("Payment", back_populates="member", lazy="dynamic")
    notifications = relationship("Notification", back_populates="member", lazy="dynamic")
