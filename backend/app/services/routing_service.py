"""
Routing Decision Engine — determines where a classified request should go.

Routing table (from business brief):
  Classification  | Location       | Destination
  ─────────────────────────────────────────────────
  acute           | Any            | WellaHealth API
  chronic         | Lagos          | Leadway WhatsApp Number A
  chronic         | Outside Lagos  | Leadway WhatsApp Number B
  mixed           | Lagos          | Leadway WhatsApp Number A
  mixed           | Outside Lagos  | Leadway WhatsApp Number B
  any             | Unknown loc    | Under review (manual)

This engine runs after classification. It:
1. Reads the classification result
2. Checks the location (is_lagos flag)
3. Creates a RoutingDecision record
4. Updates the request status
5. Logs the audit event
"""

import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.medication import (
    ClassificationResult,
    MedicationAuditLog,
    MedicationRequest,
    RequestStatusHistory,
    RoutingDecision,
)

logger = logging.getLogger(__name__)


# ── Status mapping by destination ────────────────────────────────

DESTINATION_STATUS_MAP = {
    "wellahealth": "routed_wellahealth",
    "whatsapp_lagos": "sent_whatsapp_lagos",
    "whatsapp_outside_lagos": "sent_whatsapp_outside_lagos",
    "manual_review": "under_review",
}


@dataclass
class RoutingResult:
    """Result of the routing decision."""
    destination: str          # wellahealth | whatsapp_lagos | whatsapp_outside_lagos | manual_review
    new_status: str           # the request status to set
    reasoning: str            # human-readable explanation
    is_lagos: bool | None


def determine_route(
    classification: str,
    is_lagos: bool | None,
) -> RoutingResult:
    """
    Pure function: given a classification and location, return the routing decision.

    Rules:
    - acute only → WellaHealth (regardless of location)
    - chronic/mixed + Lagos → WhatsApp Lagos
    - chronic/mixed + Outside Lagos → WhatsApp Outside Lagos
    - chronic/mixed + unknown location → manual review (location needed)
    """
    if classification == "acute":
        return RoutingResult(
            destination="wellahealth",
            new_status="routed_wellahealth",
            reasoning="Acute-only request. Routed to WellaHealth API for fulfilment.",
            is_lagos=is_lagos,
        )

    # chronic, mixed (unknown drugs already resolved to chronic/mixed in classification)
    if classification in ("chronic", "mixed"):
        if is_lagos is True:
            return RoutingResult(
                destination="whatsapp_lagos",
                new_status="sent_whatsapp_lagos",
                reasoning=f"{classification.title()} request, member in Lagos. "
                          "Routed to Leadway WhatsApp (Lagos).",
                is_lagos=True,
            )
        elif is_lagos is False:
            return RoutingResult(
                destination="whatsapp_outside_lagos",
                new_status="sent_whatsapp_outside_lagos",
                reasoning=f"{classification.title()} request, member outside Lagos. "
                          "Routed to Leadway WhatsApp (Outside Lagos).",
                is_lagos=False,
            )
        else:
            # Location unknown — cannot route, send to review
            return RoutingResult(
                destination="manual_review",
                new_status="under_review",
                reasoning=f"{classification.title()} request, but member location "
                          "could not be determined. Sent to manual review for "
                          "location confirmation before routing.",
                is_lagos=None,
            )

    # Fallback (shouldn't reach here after Phase 3 changes, but safe)
    return RoutingResult(
        destination="manual_review",
        new_status="under_review",
        reasoning=f"Unexpected classification '{classification}'. Sent to manual review.",
        is_lagos=is_lagos,
    )


def run_routing(
    request_id: str,
    db: Session,
    actor: str = "system",
) -> RoutingDecision:
    """
    Run routing on a classified medication request and persist the decision.

    This is the main entry point called from the submission flow.
    It:
    1. Loads the request and its classification
    2. Determines the route
    3. Creates/updates RoutingDecision record
    4. Updates request status
    5. Creates status history entry
    6. Logs the audit event
    """
    request = (
        db.query(MedicationRequest)
        .filter(MedicationRequest.request_id == request_id)
        .first()
    )
    if not request:
        raise ValueError(f"Request {request_id} not found")

    # Get classification
    classification = (
        db.query(ClassificationResult)
        .filter(ClassificationResult.request_id == request_id)
        .first()
    )
    if not classification:
        raise ValueError(f"No classification found for request {request_id}")

    # Determine route
    result = determine_route(
        classification=classification.classification,
        is_lagos=request.is_lagos,
    )

    # Create or update routing decision
    existing = (
        db.query(RoutingDecision)
        .filter(RoutingDecision.request_id == request_id)
        .first()
    )

    if existing:
        existing.destination = result.destination
        existing.reasoning = result.reasoning
        existing.is_lagos = result.is_lagos
        routing_record = existing
    else:
        routing_record = RoutingDecision(
            request_id=request_id,
            destination=result.destination,
            reasoning=result.reasoning,
            is_lagos=result.is_lagos,
        )
        db.add(routing_record)

    # Update request status
    old_status = request.status
    request.status = result.new_status

    # Status history
    history = RequestStatusHistory(
        request_id=request_id,
        old_status=old_status,
        new_status=result.new_status,
        changed_by=actor,
        notes=result.reasoning,
    )
    db.add(history)

    # Audit log
    audit = MedicationAuditLog(
        event_type="routing_completed",
        request_id=request_id,
        actor=actor,
        detail=(
            f"Routed to {result.destination} | "
            f"Classification: {classification.classification} | "
            f"Lagos: {result.is_lagos} | "
            f"Status: {result.new_status}"
        ),
    )
    db.add(audit)

    db.flush()

    logger.info(
        "Routing complete: request=%s, destination=%s, status=%s, is_lagos=%s",
        request_id, result.destination, result.new_status, result.is_lagos,
    )

    return routing_record
