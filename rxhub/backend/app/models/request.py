import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class Request(Base):
    __tablename__ = "requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = Column(String(50), ForeignKey("members.member_id", ondelete="CASCADE"), nullable=False, index=True)
    request_type = Column(String(30), nullable=False)
    action = Column(String(30), nullable=False)
    payload = Column(JSONB, nullable=False, default={})
    comment = Column(Text)
    attachment_url = Column(Text)
    status = Column(String(20), default="PENDING", index=True)
    admin_id = Column(UUID(as_uuid=True), ForeignKey("admins.id"))
    admin_comment = Column(Text)
    reviewed_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    pbm_synced = Column(Boolean, default=False)
    pbm_sync_error = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    member = relationship("Member", back_populates="requests")
    admin = relationship("Admin", back_populates="handled_requests")
    logs = relationship("RequestLog", back_populates="request", lazy="dynamic")


class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("requests.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_type = Column(String(20), nullable=False)
    actor_id = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)
    before_state = Column(JSONB)
    after_state = Column(JSONB)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    request = relationship("Request", back_populates="logs")
