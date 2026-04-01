import httpx
import logging
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.config import settings
from app.models.sync_log import SyncLog

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAYS = [2, 4, 8]


class PrognosisClient:
    """Client for the Leadway Health Prognosis API."""

    def __init__(self):
        self.base_url = settings.PROGNOSIS_API_BASE_URL
        self.timeout = settings.PROGNOSIS_API_TIMEOUT
        self._token: Optional[str] = None
        self._token_expires: Optional[datetime] = None

    async def _authenticate(self) -> str:
        """Login to Prognosis API and cache the bearer token."""
        if self._token and self._token_expires and datetime.now(timezone.utc) < self._token_expires:
            return self._token

        url = f"{self.base_url}/ApiUsers/Login"
        payload = {
            "Username": settings.PROGNOSIS_USERNAME,
            "Password": settings.PROGNOSIS_PASSWORD,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                response = await client.post(url, json=payload)
                if response.is_success:
                    data = response.json()
                    # Prognosis returns token directly or in a token field
                    token = data if isinstance(data, str) else data.get("token") or data.get("Token") or data.get("access_token", "")
                    self._token = token
                    # Cache token for 55 minutes (assume 1hr expiry)
                    from datetime import timedelta
                    self._token_expires = datetime.now(timezone.utc) + timedelta(minutes=55)
                    logger.info("Prognosis API authenticated successfully")
                    return self._token
                else:
                    logger.error(f"Prognosis login failed: {response.status_code} {response.text}")
                    return ""
        except Exception as e:
            logger.error(f"Prognosis login error: {e}")
            return ""

    async def _request(
        self, method: str, url: str, db: Optional[Session] = None, **kwargs
    ) -> dict:
        """Make authenticated request to Prognosis API with retry logic."""
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                token = await self._authenticate()
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                }

                async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                    response = await client.request(method, url, headers=headers, **kwargs)

                    # Try to parse JSON, handle empty or non-JSON responses
                    data = {}
                    if response.content:
                        try:
                            data = response.json()
                        except Exception:
                            data = {"raw_response": response.text}

                    if db:
                        self._log_sync(db, url, method, kwargs.get("json"), data, response.status_code, response.is_success)

                    if response.is_success:
                        return data

                    # If 401, clear token and retry
                    if response.status_code == 401:
                        self._token = None
                        self._token_expires = None
                        last_error = "Authentication expired, retrying..."
                        continue

                    last_error = f"HTTP {response.status_code}: {data}"
                    if response.status_code < 500:
                        break

            except httpx.TimeoutException as e:
                last_error = f"Timeout: {str(e)}"
                logger.warning(f"Prognosis API timeout (attempt {attempt + 1}): {url}")
            except httpx.RequestError as e:
                last_error = f"Connection error: {str(e)}"
                logger.warning(f"Prognosis API error (attempt {attempt + 1}): {url} - {e}")

            if attempt < MAX_RETRIES - 1:
                import asyncio
                await asyncio.sleep(RETRY_DELAYS[attempt])

        logger.error(f"Prognosis API failed after {MAX_RETRIES} retries: {url} - {last_error}")
        return {"error": last_error, "success": False}

    def _log_sync(
        self, db: Session, endpoint: str, method: str,
        request_body: Optional[dict], response_body: dict,
        status_code: int, success: bool,
    ):
        try:
            log = SyncLog(
                entity_type="PROGNOSIS_API",
                entity_id=endpoint,
                direction="OUTBOUND",
                endpoint=f"{method} {endpoint}",
                request_body=request_body,
                response_body=response_body,
                status_code=status_code,
                success=success,
            )
            db.add(log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log sync: {e}")

    # ── Enrollee Endpoints ───────────────────────────────────

    async def get_enrollee_by_id(self, enrollee_id: str, db: Session = None) -> dict:
        """
        GET /EnrolleeProfile/GetEnrolleeBioDataByEnrolleeID?enrolleeid={id}
        Fetches full enrollee bio data including name, phone, diagnosis, plan, etc.
        """
        url = f"{self.base_url}/EnrolleeProfile/GetEnrolleeBioDataByEnrolleeID?enrolleeid={enrollee_id}"
        return await self._request("GET", url, db=db)

    async def validate_member(self, member_id: str, phone: str, db: Session = None) -> dict:
        """
        Validate member by fetching their bio data from Prognosis
        and comparing the phone number on file.
        Returns enrollee data if phone matches, error otherwise.
        """
        data = await self.get_enrollee_by_id(member_id, db=db)

        if "error" in data:
            return data

        # Handle both single object and list response formats
        enrollee = data
        if isinstance(data, list):
            enrollee = data[0] if data else {}

        # Extract phone from Prognosis response (field names may vary)
        stored_phone = (
            enrollee.get("phone") or enrollee.get("Phone") or
            enrollee.get("phoneNumber") or enrollee.get("PhoneNumber") or
            enrollee.get("mobileNumber") or enrollee.get("MobileNumber") or
            enrollee.get("telephone") or enrollee.get("Telephone") or ""
        )

        # Normalize phones for comparison (strip spaces, +234 → 0, etc.)
        input_normalized = self._normalize_phone(phone)
        stored_normalized = self._normalize_phone(stored_phone)

        if not stored_normalized:
            # No phone on file — allow login if enrollee exists (they proved they know their ID)
            return {**enrollee, "valid": True, "phone_match": False, "phone_on_file": ""}

        if input_normalized == stored_normalized:
            return {**enrollee, "valid": True, "phone_match": True}
        else:
            return {"valid": False, "error": "Phone number does not match records", "phone_on_file_masked": self._mask_phone(stored_phone)}

    def _normalize_phone(self, phone: str) -> str:
        """Normalize Nigerian phone number to 0XXXXXXXXXX format."""
        if not phone:
            return ""
        phone = phone.strip().replace(" ", "").replace("-", "")
        if phone.startswith("+234"):
            phone = "0" + phone[4:]
        elif phone.startswith("234") and len(phone) > 10:
            phone = "0" + phone[3:]
        return phone

    def _mask_phone(self, phone: str) -> str:
        """Mask phone number for display: 0801****78"""
        if not phone or len(phone) < 6:
            return "****"
        return phone[:4] + "****" + phone[-2:]

    async def get_member(self, member_id: str, db: Session = None) -> dict:
        """Fetch member profile from Prognosis (alias for get_enrollee_by_id)."""
        data = await self.get_enrollee_by_id(member_id, db=db)
        if isinstance(data, list):
            return data[0] if data else {"error": "No enrollee data found"}
        return data

    async def get_member_medications(self, member_id: str, db: Session = None) -> dict:
        """
        Fetch member medications from Prognosis.
        Uses enrollee bio data — medications may be nested in the response.
        """
        data = await self.get_enrollee_by_id(member_id, db=db)
        if "error" in data:
            return data

        enrollee = data if not isinstance(data, list) else (data[0] if data else {})

        # Extract medications if present in enrollee data
        medications = (
            enrollee.get("medications") or enrollee.get("Medications") or
            enrollee.get("drugs") or enrollee.get("Drugs") or []
        )

        return {"medications": medications}

    async def submit_change_request(self, payload: dict, db: Session = None) -> dict:
        """POST change request to Prognosis (when available)."""
        # TODO: Integrate with actual Prognosis change request endpoint when provided
        logger.info(f"Change request queued for PBM sync: {payload}")
        return {"status": "queued", "message": "Request queued for PBM processing"}


prognosis_client = PrognosisClient()
