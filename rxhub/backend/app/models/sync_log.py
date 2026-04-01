import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(30), nullable=False)
    entity_id = Column(String(100), nullable=False)
    direction = Column(String(10), nullable=False)
    endpoint = Column(String(300))
    request_body = Column(JSONB)
    response_body = Column(JSONB)
    status_code = Column(Integer)
    success = Column(Boolean, default=False)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
