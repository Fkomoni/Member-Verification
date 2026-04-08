import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Member(Base):
    __tablename__ = "members"

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    enrollee_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    dob: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    gender: Mapped[str] = mapped_column(String(10), nullable=True)
    nin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    biometric_registered: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    biometrics: Mapped[list["Biometric"]] = relationship(back_populates="member")
    visits: Mapped[list["Visit"]] = relationship(back_populates="member")
    verification_logs: Mapped[list["VerificationLog"]] = relationship(
        back_populates="member"
    )


class Biometric(Base):
    __tablename__ = "biometrics"

    biometric_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("members.member_id"), nullable=False
    )
    fingerprint_template: Mapped[bytes] = mapped_column(
        LargeBinary, nullable=False, comment="AES-encrypted fingerprint template"
    )
    finger_position: Mapped[str] = mapped_column(
        String(20), nullable=False, default="right_thumb"
    )
    date_created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    member: Mapped["Member"] = relationship(back_populates="biometrics")


class Provider(Base):
    __tablename__ = "providers"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    prognosis_provider_id: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Provider ID in the Prognosis system"
    )
    location: Mapped[str] = mapped_column(String(300), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    visits: Mapped[list["Visit"]] = relationship(back_populates="provider")
    verification_logs: Mapped[list["VerificationLog"]] = relationship(
        back_populates="provider"
    )


class Visit(Base):
    __tablename__ = "visits"

    visit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("members.member_id"), nullable=False
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("providers.provider_id"), nullable=False
    )
    verification_token: Mapped[str | None] = mapped_column(String(500), nullable=True)
    verification_status: Mapped[str] = mapped_column(
        Enum("APPROVED", "DENIED", "PENDING", name="verification_status_enum"),
        default="PENDING",
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    member: Mapped["Member"] = relationship(back_populates="visits")
    provider: Mapped["Provider"] = relationship(back_populates="visits")


class VerificationLog(Base):
    __tablename__ = "verification_logs"

    log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("members.member_id"), nullable=False
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("providers.provider_id"), nullable=False
    )
    match_status: Mapped[str] = mapped_column(
        Enum("MATCH", "NO_MATCH", "NEW_ENROLLMENT", name="match_status_enum"),
        nullable=False,
    )
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    member: Mapped["Member"] = relationship(back_populates="verification_logs")
    provider: Mapped["Provider"] = relationship(back_populates="verification_logs")


# ── Call Center ──────────────────────────────────────────────

class Agent(Base):
    """Call center agent — separate from healthcare providers."""
    __tablename__ = "agents"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="CALL_CENTER_AGENT")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    authorization_codes: Mapped[list["AuthorizationCode"]] = relationship(
        back_populates="agent"
    )


class AuthorizationCode(Base):
    """Pre-authorization code generated by call center for member visits."""
    __tablename__ = "authorization_codes"

    code_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    enrollee_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    enrollee_name: Mapped[str] = mapped_column(String(200), nullable=False)
    visit_type_id: Mapped[int] = mapped_column(Integer, nullable=False)
    visit_type_name: Mapped[str] = mapped_column(String(100), nullable=False)
    approved_amount: Mapped[float] = mapped_column(Float, default=0.0)
    cif_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    scheme_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")  # ACTIVE, USED, EXPIRED, CANCELLED
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.agent_id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    agent: Mapped["Agent"] = relationship(back_populates="authorization_codes")
