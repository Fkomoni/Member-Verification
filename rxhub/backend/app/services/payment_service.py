import httpx
import logging
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.payment import Payment

logger = logging.getLogger(__name__)


class PaymentService:
    """Paystack payment gateway integration."""

    PAYSTACK_BASE = "https://api.paystack.co"

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

    async def initialize_payment(
        self, payment: Payment, email: str, db: Session
    ) -> dict:
        """Initialize a Paystack transaction."""
        amount_kobo = int(payment.amount * 100)

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{self.PAYSTACK_BASE}/transaction/initialize",
                    headers=self.headers,
                    json={
                        "email": email or f"{payment.member_id}@rxhub.leadwayhmo.com",
                        "amount": amount_kobo,
                        "currency": payment.currency,
                        "reference": str(payment.id),
                        "metadata": {
                            "member_id": payment.member_id,
                            "payment_type": payment.payment_type,
                            "medication_id": str(payment.medication_id) if payment.medication_id else None,
                        },
                    },
                )
                data = resp.json()

                if data.get("status"):
                    payment.gateway_ref = data["data"]["reference"]
                    payment.status = "PROCESSING"
                    db.commit()
                    return {
                        "authorization_url": data["data"]["authorization_url"],
                        "reference": data["data"]["reference"],
                    }

                logger.error(f"Paystack init failed: {data}")
                return {"error": data.get("message", "Payment initialization failed")}

        except Exception as e:
            logger.error(f"Paystack error: {e}")
            return {"error": "Payment service unavailable"}

    async def verify_payment(self, reference: str, db: Session) -> dict:
        """Verify a Paystack transaction."""
        payment = db.query(Payment).filter(Payment.gateway_ref == reference).first()
        if not payment:
            return {"error": "Payment not found"}

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{self.PAYSTACK_BASE}/transaction/verify/{reference}",
                    headers=self.headers,
                )
                data = resp.json()

                if data.get("status") and data["data"]["status"] == "success":
                    payment.status = "SUCCESS"
                    payment.gateway_status = "success"
                    payment.paid_at = datetime.now(timezone.utc)
                    db.commit()
                    return {"status": "SUCCESS", "payment_id": str(payment.id)}

                payment.status = "FAILED"
                payment.gateway_status = data.get("data", {}).get("status", "unknown")
                db.commit()
                return {"status": "FAILED", "message": data.get("message")}

        except Exception as e:
            logger.error(f"Paystack verify error: {e}")
            return {"error": "Verification failed"}


payment_service = PaymentService()
