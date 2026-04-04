import asyncio
import logging
from datetime import datetime, date, timedelta, timezone
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.medication import Medication
from app.models.notification import Notification
from app.models.request import Request
from app.services.sync_service import push_approved_request_to_pbm

logger = logging.getLogger(__name__)


async def process_approved_requests():
    """Background task: push approved, un-synced requests to PBM."""
    db: Session = SessionLocal()
    try:
        pending = (
            db.query(Request)
            .filter(Request.status == "APPROVED", Request.pbm_synced.is_(False))
            .limit(50)
            .all()
        )
        for req in pending:
            try:
                await push_approved_request_to_pbm(str(req.id), db)
            except Exception as e:
                logger.error(f"Failed to sync request {req.id}: {e}")
    finally:
        db.close()


async def generate_refill_reminders():
    """Background task: create notifications for upcoming refills."""
    db: Session = SessionLocal()
    try:
        threshold = date.today() + timedelta(days=7)
        meds = (
            db.query(Medication)
            .filter(
                Medication.status == "ACTIVE",
                Medication.next_refill_due <= threshold,
                Medication.next_refill_due >= date.today(),
            )
            .all()
        )

        for med in meds:
            days_left = (med.next_refill_due - date.today()).days
            existing = (
                db.query(Notification)
                .filter(
                    Notification.member_id == med.member_id,
                    Notification.category == "REFILL_REMINDER",
                    Notification.created_at >= datetime.now(timezone.utc) - timedelta(days=1),
                )
                .first()
            )
            if existing:
                continue

            notification = Notification(
                member_id=med.member_id,
                title="Refill Reminder",
                body=f"Your {med.drug_name} supply runs out in {days_left} day(s). Request a refill now.",
                category="REFILL_REMINDER",
                action_url=f"/medications/{med.id}/refill",
            )
            db.add(notification)

        db.commit()
    finally:
        db.close()


async def run_background_loop():
    """Main loop that runs periodic tasks."""
    while True:
        try:
            await process_approved_requests()
            await generate_refill_reminders()
        except Exception as e:
            logger.error(f"Background task error: {e}")
        await asyncio.sleep(300)  # Run every 5 minutes
