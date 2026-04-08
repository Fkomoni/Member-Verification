"""
Mock Member Service — member lookup with DB-first, mock-fallback strategy.

PLACEHOLDER: Replace mock data with real Prognosis API calls when available.
"""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.models import Member

log = logging.getLogger(__name__)

# ── Mock member data (for development without Prognosis API) ────────
_MOCK_MEMBERS: dict[str, dict] = {
    "LWH-001234": {
        "name": "Adebayo Ogunlesi",
        "dob": "1985-03-15",
        "gender": "Male",
        "phone": "08012345678",
        "plan": "Gold",
    },
    "LWH-005678": {
        "name": "Chioma Eze",
        "dob": "1990-07-22",
        "gender": "Female",
        "phone": "08098765432",
        "plan": "Silver",
    },
    "LWH-009012": {
        "name": "Fatima Abdullahi",
        "dob": "1978-11-08",
        "gender": "Female",
        "phone": "07033344455",
        "plan": "Platinum",
    },
}


def lookup_member(
    db: Session, *, enrollee_id: str
) -> dict | None:
    """
    Look up a member by enrollee ID.

    Strategy:
    1. Check local DB first
    2. Fall back to mock data (PLACEHOLDER for Prognosis API)

    Returns dict with member info or None if not found.
    """
    # 1. Check local database
    member = (
        db.query(Member)
        .filter(Member.enrollee_id == enrollee_id.strip())
        .first()
    )
    if member:
        log.info("Member found in DB: %s", enrollee_id)
        return {
            "member_id": str(member.member_id),
            "enrollee_id": member.enrollee_id,
            "name": member.name,
            "dob": member.dob.isoformat() if member.dob else None,
            "gender": member.gender,
            "phone": None,  # Not stored in existing schema
            "plan": None,
            "source": "database",
        }

    # 2. Mock fallback (PLACEHOLDER — replace with Prognosis API)
    mock = _MOCK_MEMBERS.get(enrollee_id.strip().upper())
    if mock:
        log.info("Member found in mock data: %s", enrollee_id)
        # Auto-create in local DB for consistency
        new_member = Member(
            enrollee_id=enrollee_id.strip().upper(),
            name=mock["name"],
            gender=mock.get("gender"),
        )
        db.add(new_member)
        db.commit()
        db.refresh(new_member)

        return {
            "member_id": str(new_member.member_id),
            "enrollee_id": new_member.enrollee_id,
            "name": mock["name"],
            "dob": mock.get("dob"),
            "gender": mock.get("gender"),
            "phone": mock.get("phone"),
            "plan": mock.get("plan"),
            "source": "mock",
        }

    log.warning("Member not found: %s", enrollee_id)
    return None


def validate_member_phone(
    db: Session, *, enrollee_id: str, phone: str
) -> tuple[bool, str, dict | None]:
    """
    Validate a member exists and the phone matches.

    PLACEHOLDER: Phone validation is mocked — always passes if member exists.
    Replace with real validation when Prognosis API provides phone data.

    Returns (is_valid, message, member_data_or_None).
    """
    member_data = lookup_member(db, enrollee_id=enrollee_id)
    if not member_data:
        return False, "Member not found. Please check your Enrollee ID.", None

    # PLACEHOLDER: Accept any phone for now (real API will validate)
    # In production, compare phone against Prognosis member record
    return True, "Member verified successfully.", member_data
