import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
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


# ══════════════════════════════════════════════════════════════
# Reimbursement & Authorization Control System
# ══════════════════════════════════════════════════════════════


class Agent(Base):
    """Call-center agents, claims officers, and admins."""

    __tablename__ = "agents"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(
        Enum("call_center", "claims_officer", "admin", name="agent_role_enum"),
        nullable=False,
        default="call_center",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    authorization_codes: Mapped[list["AuthorizationCode"]] = relationship(
        back_populates="agent"
    )


class AuthorizationCode(Base):
    """
    Core authorization code engine.
    Codes are unique, member-bound, single-use, time-limited, and auditable.
    """

    __tablename__ = "authorization_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("members.member_id"), nullable=False
    )
    enrollee_id: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    approved_amount: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    visit_type: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.agent_id"), nullable=False
    )
    agent_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("active", "used", "expired", name="auth_code_status_enum"),
        default="active",
        index=True,
    )
    linked_claim_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reimbursement_claims.claim_id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    agent: Mapped["Agent"] = relationship(back_populates="authorization_codes")
    member: Mapped["Member"] = relationship()
    linked_claim: Mapped["ReimbursementClaim | None"] = relationship(
        back_populates="authorization_code",
        foreign_keys=[linked_claim_id],
    )


class ReimbursementClaim(Base):
    """Reimbursement claim submitted by a member using an authorization code."""

    __tablename__ = "reimbursement_claims"

    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    claim_ref: Mapped[str] = mapped_column(
        String(30), unique=True, index=True, nullable=False
    )
    authorization_code_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("authorization_codes.id"),
        nullable=False,
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("members.member_id"), nullable=False
    )
    enrollee_id: Mapped[str] = mapped_column(String(50), nullable=False)
    member_name: Mapped[str] = mapped_column(String(200), nullable=False)
    member_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    hospital_name: Mapped[str] = mapped_column(String(300), nullable=False)
    visit_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    reason_for_visit: Mapped[str] = mapped_column(Text, nullable=False)
    reimbursement_reason: Mapped[str] = mapped_column(Text, nullable=False)
    claim_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    medications: Mapped[str | None] = mapped_column(Text, nullable=True)
    lab_investigations: Mapped[str | None] = mapped_column(Text, nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    bank_name: Mapped[str] = mapped_column(String(200), nullable=False)
    account_number: Mapped[str] = mapped_column(String(20), nullable=False)
    account_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(
            "submitted",
            "under_review",
            "pending_info",
            "approved",
            "rejected",
            "payment_processing",
            "paid",
            name="claim_status_enum",
        ),
        default="submitted",
        index=True,
    )
    approved_amount: Mapped[float | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.agent_id"), nullable=True
    )
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    authorization_code: Mapped["AuthorizationCode | None"] = relationship(
        back_populates="linked_claim",
        foreign_keys=[authorization_code_id],
    )
    member: Mapped["Member"] = relationship()
    service_lines: Mapped[list["ClaimServiceLine"]] = relationship(
        back_populates="claim", cascade="all, delete-orphan"
    )


class ClaimServiceLine(Base):
    """Dynamic service line items on a reimbursement claim."""

    __tablename__ = "claim_service_lines"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reimbursement_claims.claim_id", ondelete="CASCADE"),
        nullable=False,
    )
    service_name: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    claim: Mapped["ReimbursementClaim"] = relationship(
        back_populates="service_lines"
    )


class ClaimAuditLog(Base):
    """Full audit trail for authorization codes and claims."""

    __tablename__ = "claim_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # agent, member, system
    actor_id: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
