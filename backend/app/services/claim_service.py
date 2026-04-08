"""
Claim Service — handles claim creation, reference generation, and status management.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.models import (
    AuthorizationCode,
    ClaimServiceLine,
    ReimbursementClaim,
)

log = logging.getLogger(__name__)


def generate_claim_ref(db: Session) -> str:
    """Generate a human-readable claim reference: LH-RC-XXXXXX."""
    count = db.query(ReimbursementClaim).count()
    return f"LH-RC-{count + 1:06d}"


def create_claim(
    db: Session,
    *,
    auth_code: AuthorizationCode,
    member_name: str,
    member_phone: str,
    hospital_name: str,
    visit_date: datetime,
    reason_for_visit: str,
    reimbursement_reason: str,
    claim_amount: float,
    medications: str | None,
    lab_investigations: str | None,
    comments: str | None,
    bank_name: str,
    account_number: str,
    account_name: str,
    service_lines: list[dict],
) -> ReimbursementClaim:
    """
    Create a reimbursement claim and its service lines.
    Marks the authorization code as used.
    """
    claim_ref = generate_claim_ref(db)

    claim = ReimbursementClaim(
        claim_ref=claim_ref,
        authorization_code_id=auth_code.id,
        member_id=auth_code.member_id,
        enrollee_id=auth_code.enrollee_id,
        member_name=member_name,
        member_phone=member_phone,
        hospital_name=hospital_name,
        visit_date=visit_date,
        reason_for_visit=reason_for_visit,
        reimbursement_reason=reimbursement_reason,
        claim_amount=claim_amount,
        medications=medications,
        lab_investigations=lab_investigations,
        comments=comments,
        bank_name=bank_name,
        account_number=account_number,
        account_name=account_name,
        status="submitted",
        approved_amount=float(auth_code.approved_amount),
    )
    db.add(claim)
    db.flush()  # Get claim_id before adding service lines

    # Create service lines
    for line in service_lines:
        total = line["quantity"] * float(line["unit_price"])
        db.add(
            ClaimServiceLine(
                claim_id=claim.claim_id,
                service_name=line["service_name"],
                quantity=line["quantity"],
                unit_price=float(line["unit_price"]),
                total=total,
            )
        )

    # Mark authorization code as used
    auth_code.status = "used"
    auth_code.linked_claim_id = claim.claim_id

    db.commit()
    db.refresh(claim)
    log.info(
        "Claim created: ref=%s enrollee=%s amount=%s code=%s",
        claim.claim_ref,
        claim.enrollee_id,
        claim.claim_amount,
        auth_code.code,
    )
    return claim
