"""
Medication Routing Module – SQLAlchemy ORM Models

Tables:
  - drug_master: Reference table of known medications with classification
  - drug_aliases: Alternative/brand names mapping to drug_master entries
  - medication_requests: Provider-submitted prescription requests
  - medication_request_items: Individual medication lines within a request
  - classification_results: Per-request classification outcome
  - routing_decisions: Per-request routing outcome
  - request_status_history: Audit trail of status changes
  - wellahealth_api_logs: Outbound WellaHealth API call logs
  - whatsapp_dispatch_logs: Outbound WhatsApp dispatch logs
  - medication_audit_logs: General audit trail for the medication module
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# ── Enums ────────────────────────────────────────────────────────

DRUG_CATEGORY_ENUM = Enum(
    "acute", "chronic", "either", "unknown",
    name="drug_category_enum",
)

REQUEST_CLASSIFICATION_ENUM = Enum(
    "acute", "chronic", "mixed", "review_required",
    name="request_classification_enum",
)

ROUTE_DESTINATION_ENUM = Enum(
    "wellahealth",
    "whatsapp_lagos",
    "whatsapp_outside_lagos",
    "manual_review",
    name="route_destination_enum",
)

REQUEST_STATUS_ENUM = Enum(
    "draft",
    "submitted",
    "under_review",
    "routed_wellahealth",
    "sent_whatsapp_lagos",
    "sent_whatsapp_outside_lagos",
    "awaiting_fulfilment",
    "in_progress",
    "completed",
    "failed",
    "escalated",
    "cancelled",
    name="request_status_enum",
)

URGENCY_ENUM = Enum(
    "routine", "urgent", "emergency",
    name="urgency_enum",
)


# ── Drug Master ──────────────────────────────────────────────────

class DrugMaster(Base):
    """Reference table of known medications with acute/chronic classification."""
    __tablename__ = "drug_master"

    drug_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    generic_name: Mapped[str] = mapped_column(
        String(300), nullable=False, index=True,
    )
    category: Mapped[str] = mapped_column(
        DRUG_CATEGORY_ENUM, nullable=False, default="unknown",
        comment="acute | chronic | either | unknown",
    )
    common_brand_names: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Comma-separated common brand names for quick reference",
    )
    therapeutic_class: Mapped[str | None] = mapped_column(
        String(200), nullable=True,
        comment="e.g. antihypertensive, antibiotic, analgesic",
    )
    requires_review: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="Flag for high-risk or ambiguous medications",
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # WellaHealth tariff fields
    brand_name: Mapped[str | None] = mapped_column(
        String(300), nullable=True, index=True,
    )
    drug_name_display: Mapped[str | None] = mapped_column(
        String(400), nullable=True, index=True,
        comment="Full display name e.g. 'PARACETAMOL 500MG TABLET'",
    )
    dosage_form: Mapped[str | None] = mapped_column(String(100), nullable=True)
    strength: Mapped[str | None] = mapped_column(String(100), nullable=True)
    drug_class: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # Track data source
    source: Mapped[str] = mapped_column(
        String(50), default="seed",
        comment="seed | wellahealth | manual | ai_suggested",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    aliases: Mapped[list["DrugAlias"]] = relationship(
        back_populates="drug", cascade="all, delete-orphan",
    )


class DrugAlias(Base):
    """Alternative names (brand, misspelling, abbreviation) for a drug_master entry."""
    __tablename__ = "drug_aliases"

    alias_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    drug_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drug_master.drug_id"), nullable=False,
    )
    alias_name: Mapped[str] = mapped_column(
        String(300), nullable=False, index=True,
    )
    alias_type: Mapped[str] = mapped_column(
        String(50), default="brand",
        comment="brand | abbreviation | misspelling | local_name",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
    )

    drug: Mapped["DrugMaster"] = relationship(back_populates="aliases")


# ── Medication Requests ──────────────────────────────────────────

class MedicationRequest(Base):
    """A provider-submitted prescription/medication request for a member."""
    __tablename__ = "medication_requests"

    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    # Human-readable reference: e.g. "RX-20260409-0001"
    reference_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True,
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("providers.provider_id"), nullable=False,
    )
    # Enrollee details
    enrollee_id: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="CIF number from Prognosis",
    )
    enrollee_name: Mapped[str] = mapped_column(String(200), nullable=False)
    enrollee_dob: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    enrollee_gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    member_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    member_email: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Clinical info
    diagnosis: Mapped[str] = mapped_column(Text, nullable=False)
    treating_doctor: Mapped[str] = mapped_column(String(200), nullable=False)
    doctor_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    provider_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Delivery location (structured)
    delivery_state: Mapped[str] = mapped_column(String(100), nullable=False)
    delivery_lga: Mapped[str | None] = mapped_column(String(100), nullable=True)
    delivery_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    delivery_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivery_landmark: Mapped[str | None] = mapped_column(String(300), nullable=True)
    is_lagos: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True,
        comment="Computed: True if delivery is in Lagos state",
    )

    # Request metadata
    urgency: Mapped[str] = mapped_column(
        URGENCY_ENUM, default="routine",
    )
    status: Mapped[str] = mapped_column(
        REQUEST_STATUS_ENUM, default="submitted",
    )
    facility_name: Mapped[str] = mapped_column(String(300), nullable=False)
    facility_branch: Mapped[str | None] = mapped_column(String(200), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    items: Mapped[list["MedicationRequestItem"]] = relationship(
        back_populates="request", cascade="all, delete-orphan",
    )
    classification: Mapped["ClassificationResult | None"] = relationship(
        back_populates="request", uselist=False,
    )
    routing: Mapped["RoutingDecision | None"] = relationship(
        back_populates="request", uselist=False,
    )
    status_history: Mapped[list["RequestStatusHistory"]] = relationship(
        back_populates="request", cascade="all, delete-orphan",
    )


class MedicationRequestItem(Base):
    """A single medication line within a request."""
    __tablename__ = "medication_request_items"

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("medication_requests.request_id"),
        nullable=False,
    )
    drug_name: Mapped[str] = mapped_column(
        String(300), nullable=False,
        comment="Name as entered by provider",
    )
    generic_name: Mapped[str | None] = mapped_column(
        String(300), nullable=True,
        comment="Resolved generic name from drug master or AI",
    )
    matched_drug_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drug_master.drug_id"), nullable=True,
        comment="FK to drug_master if matched",
    )
    strength: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dosage_instruction: Mapped[str] = mapped_column(Text, nullable=False)
    duration: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="e.g. 5 days, 30 days, ongoing",
    )
    quantity: Mapped[str] = mapped_column(String(100), nullable=False)
    route: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
        comment="e.g. oral, IV, topical",
    )
    # Per-item classification
    item_category: Mapped[str | None] = mapped_column(
        DRUG_CATEGORY_ENUM, nullable=True,
        comment="acute | chronic | either | unknown — set by classification engine",
    )
    requires_review: Mapped[bool] = mapped_column(Boolean, default=False)
    classification_confidence: Mapped[float | None] = mapped_column(
        Float, nullable=True,
        comment="0.0–1.0 confidence score from classifier",
    )
    classification_source: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
        comment="drug_master | ai | manual",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
    )

    request: Mapped["MedicationRequest"] = relationship(back_populates="items")


# ── Classification & Routing Results ─────────────────────────────

class ClassificationResult(Base):
    """Request-level classification outcome."""
    __tablename__ = "classification_results"

    classification_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("medication_requests.request_id"),
        unique=True,
        nullable=False,
    )
    classification: Mapped[str] = mapped_column(
        REQUEST_CLASSIFICATION_ENUM, nullable=False,
    )
    acute_count: Mapped[int] = mapped_column(Integer, default=0)
    chronic_count: Mapped[int] = mapped_column(Integer, default=0)
    unknown_count: Mapped[int] = mapped_column(Integer, default=0)
    review_required: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[float | None] = mapped_column(
        Float, nullable=True,
        comment="Overall confidence 0.0–1.0",
    )
    reasoning: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Human-readable explanation of classification decision",
    )
    classified_by: Mapped[str] = mapped_column(
        String(50), default="rules",
        comment="rules | ai | manual",
    )
    classified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
    )

    request: Mapped["MedicationRequest"] = relationship(
        back_populates="classification",
    )


class RoutingDecision(Base):
    """Where and why a request was routed."""
    __tablename__ = "routing_decisions"

    routing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("medication_requests.request_id"),
        unique=True,
        nullable=False,
    )
    destination: Mapped[str] = mapped_column(
        ROUTE_DESTINATION_ENUM, nullable=False,
    )
    reasoning: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Why this route was chosen",
    )
    is_lagos: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    routed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
    )

    request: Mapped["MedicationRequest"] = relationship(
        back_populates="routing",
    )


# ── Status History ───────────────────────────────────────────────

class RequestStatusHistory(Base):
    """Audit trail of every status change on a medication request."""
    __tablename__ = "request_status_history"

    history_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("medication_requests.request_id"),
        nullable=False,
    )
    old_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_by: Mapped[str | None] = mapped_column(
        String(200), nullable=True,
        comment="User or system identifier that triggered the change",
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
    )

    request: Mapped["MedicationRequest"] = relationship(
        back_populates="status_history",
    )


# ── Integration Logs ─────────────────────────────────────────────

class WellaHealthApiLog(Base):
    """Log of every outbound call to the WellaHealth API."""
    __tablename__ = "wellahealth_api_logs"

    log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("medication_requests.request_id"),
        nullable=False,
    )
    endpoint: Mapped[str] = mapped_column(String(500), nullable=False)
    method: Mapped[str] = mapped_column(String(10), default="POST")
    request_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_reference: Mapped[str | None] = mapped_column(
        String(200), nullable=True,
        comment="WellaHealth fulfilment ID or order reference",
    )
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
    )


class WhatsAppDispatchLog(Base):
    """Log of every WhatsApp message dispatched for chronic/mixed requests."""
    __tablename__ = "whatsapp_dispatch_logs"

    log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("medication_requests.request_id"),
        nullable=False,
    )
    destination_number: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="Leadway WhatsApp number (Lagos or Outside Lagos)",
    )
    message_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    message_id: Mapped[str | None] = mapped_column(
        String(200), nullable=True,
        comment="WhatsApp/Meta message ID if available",
    )
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
    )


# ── Medication Audit Log ─────────────────────────────────────────

class MedicationAuditLog(Base):
    """General audit trail for the medication routing module."""
    __tablename__ = "medication_audit_logs"

    audit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    event_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="e.g. request_created, classification_completed, routing_completed",
    )
    request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
    )
    provider_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
    )
    actor: Mapped[str | None] = mapped_column(
        String(200), nullable=True,
        comment="User email or system identifier",
    )
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
    )
