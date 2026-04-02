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
                entity_id=endpoint[:100],
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
        Prognosis wraps data in {"status": 200, "result": [{...}], ...}
        """
        url = f"{self.base_url}/EnrolleeProfile/GetEnrolleeBioDataByEnrolleeID?enrolleeid={enrollee_id}"
        data = await self._request("GET", url, db=db)

        if "error" in data:
            return data

        # Unwrap Prognosis response: data is inside "result" field
        result = data.get("result") or data.get("Result") or data
        if isinstance(result, list):
            result = result[0] if result else {}

        logger.info(f"Prognosis enrollee data keys: {list(result.keys())[:20]}")
        return result

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

        # Log all keys for debugging
        logger.info(f"Prognosis enrollee keys: {list(enrollee.keys())}")

        # Extract phone — try every possible field name
        stored_phone = ""
        phone_fields = [
            "Member_MobileNo", "Member_MobileNumber", "Member_Phone",
            "Member_PhoneNumber", "Member_Telephone", "Member_GSM", "Member_CellPhone",
            "phone", "Phone", "phoneNumber", "PhoneNumber",
            "mobileNumber", "MobileNumber", "telephone", "Telephone",
            "mobileNo", "MobileNo", "phoneNo", "PhoneNo",
            "mobile", "Mobile", "tel", "Tel",
            "contactPhone", "ContactPhone", "cellPhone", "CellPhone",
            "gsm", "GSM", "gsmNumber", "GsmNumber",
        ]
        for field in phone_fields:
            val = enrollee.get(field)
            if val and str(val).strip():
                stored_phone = str(val).strip()
                logger.info(f"Found phone in field '{field}': {self._mask_phone(stored_phone)}")
                break

        if not stored_phone:
            # No phone found in any field — log all values for debugging and allow login
            logger.warning(f"No phone field found in Prognosis data for {member_id}. Keys: {list(enrollee.keys())}")
            # Log first 5 values to help identify the right field
            for k, v in list(enrollee.items())[:15]:
                logger.info(f"  Prognosis field: {k} = {str(v)[:50]}")
            return {**enrollee, "valid": True, "phone_match": False, "phone_on_file": ""}

        # Normalize phones for comparison (strip spaces, +234 → 0, etc.)
        input_normalized = self._normalize_phone(phone)
        stored_normalized = self._normalize_phone(stored_phone)

        logger.info(f"Phone comparison: input={input_normalized} vs stored={stored_normalized}")

        if input_normalized == stored_normalized:
            return {**enrollee, "valid": True, "phone_match": True}
        else:
            return {"valid": False, "error": f"Phone number does not match our records. Please use the phone number registered with your HMO plan.", "phone_on_file_masked": self._mask_phone(stored_phone)}

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
        GET /PharmacyDelivery/GetPbmMedication?enrolleeid={id}
        Fetches real medication list with refill dates, delivery info, etc.
        Prognosis wraps data in {"status": 200, "result": [...]}
        """
        url = f"{self.base_url}/PharmacyDelivery/GetPbmMedication?enrolleeid={member_id}"
        data = await self._request("GET", url, db=db)

        if "error" in data:
            return data

        # Unwrap Prognosis response
        result = data.get("result") or data.get("Result") or data
        if not isinstance(result, list):
            result = [result] if result else []

        logger.info(f"Prognosis medications: {len(result)} items for {member_id}")
        if result:
            logger.info(f"Medication fields: {list(result[0].keys())[:25]}")
            # Log first medication for field discovery
            for k, v in list(result[0].items())[:20]:
                if v and 'pic' not in str(k).lower():
                    logger.info(f"  Med field: {k} = {str(v)[:80]}")

        # Also extract delivery info and diagnosis from first record if available
        delivery_info = {}
        if result:
            first = result[0]
            delivery_info = {
                "delivery_phone": self._find_field(first, [
                    "DeliveryPhone", "Delivery_Phone", "deliveryPhone", "delivery_phone",
                    "Phone", "phone", "MobileNo", "mobileNo",
                    "Member_MobileNo", "Member_Phone",
                ]),
                "delivery_address": self._find_field(first, [
                    "DeliveryAddress", "Delivery_Address", "deliveryAddress", "delivery_address",
                    "Address", "address", "Member_Address",
                ]),
                "diagnosis": self._find_field(first, [
                    "Diagnosis", "diagnosis", "Member_Diagnosis", "PrimaryDiagnosis",
                ]),
            }

        return {"medications": result, "delivery_info": delivery_info}

    def _find_field(self, data: dict, fields: list) -> str:
        """Try multiple field names and return the first non-empty value."""
        for f in fields:
            val = data.get(f)
            if val and str(val).strip():
                return str(val).strip()
        return ""

    async def submit_change_request(self, payload: dict, db: Session = None) -> dict:
        """POST change request to Prognosis (when available)."""
        # TODO: Integrate with actual Prognosis change request endpoint when provided
        logger.info(f"Change request queued for PBM sync: {payload}")
        return {"status": "queued", "message": "Request queued for PBM processing"}


prognosis_client = PrognosisClient()
