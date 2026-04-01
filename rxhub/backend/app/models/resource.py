import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Resource(Base):
    __tablename__ = "resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(300), nullable=False)
    body = Column(Text, nullable=False)
    category = Column(String(30), nullable=False)
    diagnosis_tags = Column(ARRAY(String), default=[])
    thumbnail_url = Column(Text)
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime(timezone=True))
    author_id = Column(UUID(as_uuid=True), ForeignKey("admins.id"))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
