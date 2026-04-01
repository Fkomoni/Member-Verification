import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Numeric, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class HealthReading(Base):
    __tablename__ = "health_readings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = Column(String(50), ForeignKey("members.member_id", ondelete="CASCADE"), nullable=False, index=True)
    reading_type = Column(String(30), nullable=False)  # BLOOD_PRESSURE, BLOOD_GLUCOSE, CHOLESTEROL
    systolic = Column(Numeric(5, 1))       # BP top number
    diastolic = Column(Numeric(5, 1))      # BP bottom number
    glucose_level = Column(Numeric(6, 1))  # mg/dL
    glucose_context = Column(String(20))   # FASTING, RANDOM, POST_MEAL
    total_cholesterol = Column(Numeric(6, 1))
    hdl = Column(Numeric(6, 1))
    ldl = Column(Numeric(6, 1))
    triglycerides = Column(Numeric(6, 1))
    notes = Column(Text)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    member = relationship("Member", back_populates="health_readings")
