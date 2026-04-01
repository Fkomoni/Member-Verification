from datetime import date, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.models.medication import Medication
from app.schemas.refill import RefillIntelligence


def calculate_days_remaining(med: Medication) -> Optional[int]:
    """Calculate days until medication runs out based on last refill + days_supply."""
    if not med.last_refill_at:
        if med.next_refill_due:
            delta = med.next_refill_due - date.today()
            return max(0, delta.days)
        return None

    refill_date = med.last_refill_at.date() if hasattr(med.last_refill_at, 'date') else med.last_refill_at
    runout_date = refill_date + timedelta(days=med.days_supply or 30)
    remaining = (runout_date - date.today()).days
    return max(0, remaining)


def get_refill_intelligence(member_id: str, db: Session) -> list[RefillIntelligence]:
    """Build refill intelligence alerts for all active medications."""
    meds = (
        db.query(Medication)
        .filter(Medication.member_id == member_id, Medication.status == "ACTIVE")
        .all()
    )

    results = []
    for med in meds:
        days_remaining = calculate_days_remaining(med)
        refills_left = max(0, med.max_refills - med.refill_count)

        alert = None
        if days_remaining is not None:
            if days_remaining <= 0:
                alert = "URGENT: You have run out of this medication!"
            elif days_remaining <= 3:
                alert = f"CRITICAL: Only {days_remaining} day(s) of supply left."
            elif days_remaining <= 7:
                alert = f"WARNING: {days_remaining} days of supply remaining."
            elif days_remaining <= 14:
                alert = f"REMINDER: Refill due in {days_remaining} days."

        if refills_left == 0:
            alert = (alert + " " if alert else "") + "No refills remaining — contact your prescriber."

        results.append(RefillIntelligence(
            medication_id=str(med.id),
            drug_name=med.drug_name,
            days_remaining=days_remaining,
            next_refill_due=med.next_refill_due,
            refills_remaining=refills_left,
            status=med.status,
            alert=alert,
        ))

    return results
