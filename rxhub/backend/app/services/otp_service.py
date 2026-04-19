import httpx
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import generate_otp, hash_otp, verify_otp
from app.models.otp import OTPLog

logger = logging.getLogger(__name__)


class OTPService:
    """OTP generation, delivery via SMS, and verification."""

    async def send_otp(self, member_id: str, phone: str, db: Session) -> dict:
        """Generate OTP, store hash, send via SMS."""
        # Invalidate previous unused OTPs
        db.query(OTPLog).filter(
            OTPLog.member_id == member_id,
            OTPLog.is_used.is_(False),
            OTPLog.expires_at > datetime.now(timezone.utc),
        ).update({"is_used": True})

        plain_otp = generate_otp(settings.OTP_LENGTH)

        otp_log = OTPLog(
            member_id=member_id,
            phone=phone,
            otp_hash=hash_otp(plain_otp),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
            max_attempts=settings.OTP_MAX_ATTEMPTS,
        )
        db.add(otp_log)
        db.commit()

        await self._send_sms(phone, plain_otp)

        masked = phone[:4] + "****" + phone[-2:]
        return {"message": "OTP sent successfully", "phone_masked": masked}

    async def verify(self, member_id: str, otp: str, db: Session) -> bool:
        """Verify OTP against stored hash."""
        otp_log = (
            db.query(OTPLog)
            .filter(
                OTPLog.member_id == member_id,
                OTPLog.is_used.is_(False),
                OTPLog.expires_at > datetime.now(timezone.utc),
            )
            .order_by(OTPLog.created_at.desc())
            .first()
        )

        if not otp_log:
            return False

        otp_log.attempts += 1

        if otp_log.attempts > otp_log.max_attempts:
            otp_log.is_used = True
            db.commit()
            return False

        if verify_otp(otp, otp_log.otp_hash):
            otp_log.is_used = True
            db.commit()
            return True

        db.commit()
        return False

    async def _send_sms(self, phone: str, otp: str):
        """Send OTP via SMS gateway (Termii)."""
        if not settings.SMS_API_KEY:
            logger.warning(f"SMS not configured. OTP for {phone}: {otp}")
            return

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                await client.post(
                    "https://api.ng.termii.com/api/sms/send",
                    json={
                        "to": phone,
                        "from": settings.SMS_SENDER_ID,
                        "sms": f"Your LeadwayHMO RxHub verification code is {otp}. Valid for {settings.OTP_EXPIRE_MINUTES} minutes.",
                        "type": "plain",
                        "channel": "generic",
                        "api_key": settings.SMS_API_KEY,
                    },
                )
        except Exception as e:
            logger.error(f"SMS send failed: {e}")


otp_service = OTPService()
