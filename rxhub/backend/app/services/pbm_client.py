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
                    "PhoneNumber", "AlternativePhoneNumber",
                    "DeliveryPhone", "Delivery_Phone", "deliveryPhone",
                    "Phone", "phone", "MobileNo", "mobileNo",
                    "Member_MobileNo", "Member_Phone",
                ]),
                "delivery_address": self._find_field(first, [
                    "DeliveryAddress", "Delivery_Address", "deliveryAddress",
                    "Address", "address", "Member_Address",
                ]),
                "diagnosis": self._find_field(first, [
                    "diagnosisname", "Diagnosis", "diagnosis",
                    "DiagnosisName", "Member_Diagnosis", "PrimaryDiagnosis",
                ]),
                "email": self._find_field(first, [
                    "EmailAdress", "EmailAddress", "Email", "email",
                    "Member_Email",
                ]),
                "scheme": self._find_field(first, [
                    "scheme", "Scheme", "Scheme_type",
                    "SchemeName", "Member_SchemeName",
                ]),
                "company": self._find_field(first, [
                    "Company", "company", "Employer",
                    "Member_Employer", "Member_Company",
                ]),
                "pharmacy": self._find_field(first, [
                    "pharmacyname", "PharmacyName", "Pharmacy",
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

    async def search_medications(self, search_term: str, db: Session = None) -> list:
        """
        GET /ListValues/GetProceduresByFilter_pbm?filtertype=0&providerid=8520&searchbyname={term}
        Search for medications by name from the Prognosis drug database.
        """
        url = f"{self.base_url}/ListValues/GetProceduresByFilter_pbm"

        # Use params dict for proper URL encoding
        token = await self._authenticate()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                response = await client.get(url, headers=headers, params={
                    "filtertype": "0",
                    "providerid": "8520",
                    "searchbyname": search_term,
                })

                logger.info(f"Medication search '{search_term}': HTTP {response.status_code}")

                if not response.is_success:
                    logger.error(f"Medication search failed: {response.status_code} {response.text[:200]}")
                    return []

                data = response.json() if response.content else {}

                # Unwrap Prognosis response
                result = data.get("result") or data.get("Result") or data
                if not isinstance(result, list):
                    # Maybe the result IS the list directly
                    if isinstance(data, list):
                        result = data
                    else:
                        result = [result] if result and not isinstance(result, (str, int, bool)) else []

                logger.info(f"Medication search '{search_term}': {len(result)} results")
                if result:
                    logger.info(f"Search result sample keys: {list(result[0].keys())[:10]}")
                    # Log first result for debugging
                    for k, v in list(result[0].items())[:8]:
                        logger.info(f"  Search field: {k} = {str(v)[:60]}")

                return result

        except Exception as e:
            logger.error(f"Medication search error: {e}")
            return []

    async def search_diagnoses(self, search_term: str = "", db: Session = None) -> list:
        """
        GET /ListValues/GetPharmacyDiagnosisList
        Fetch diagnosis list from Prognosis for autocomplete.
        """
        url = f"{self.base_url}/ListValues/GetPharmacyDiagnosisList"

        token = await self._authenticate()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                response = await client.get(url, headers=headers)
                if not response.is_success:
                    logger.error(f"Diagnosis search failed: {response.status_code}")
                    return []

                data = response.json() if response.content else {}
                result = data.get("result") or data.get("Result") or data
                if not isinstance(result, list):
                    if isinstance(data, list):
                        result = data
                    else:
                        result = []

                # Filter by search term if provided
                if search_term and result:
                    term_lower = search_term.lower()
                    result = [r for r in result if term_lower in str(r.get("diagnosisName", r.get("DiagnosisName", r.get("name", "")))).lower()]

                logger.info(f"Diagnosis search '{search_term}': {len(result)} results")
                if result and len(result) > 0:
                    logger.info(f"Diagnosis fields: {list(result[0].keys())}")

                return result[:20]

        except Exception as e:
            logger.error(f"Diagnosis search error: {e}")
            return []

    async def delete_member_medication(self, entry_no: int, comment: str, db: Session = None) -> dict:
        """
        POST /PharmacyDelivery/DeletedByMember
        Delete a medication from the member's PBM record.
        """
        url = f"{self.base_url}/PharmacyDelivery/DeletedByMember"
        body = {
            "EntryNo": entry_no,
            "Comment": comment,
        }

        logger.info(f"Deleting medication from Prognosis:")
        logger.info(f"  URL: {url}")
        logger.info(f"  Payload: {body}")
        result = await self._request("POST", url, db=db, json=body)
        logger.info(f"  Response: {result}")

        if "error" in result:
            logger.error(f"Prognosis medication delete FAILED: {result}")
        else:
            logger.info(f"Prognosis medication delete SUCCESS: EntryNo={entry_no}")

        return result

    async def update_member_profile(self, enrollee_id: str, payload: dict, db: Session = None) -> dict:
        """
        POST /Member/UpdatePharmacyMemberInfo
        Push profile changes (email, address, phone) to Prognosis.
        """
        url = f"{self.base_url}/Member/UpdatePharmacyMemberInfo"
        body = {"EnrolleeID": enrollee_id}

        # Map our fields to Prognosis fields
        if payload.get("email") or payload.get("Email"):
            body["Email"] = payload.get("email", {}).get("requested") if isinstance(payload.get("email"), dict) else payload.get("email") or payload.get("Email", "")

        if payload.get("phone") or payload.get("Phone"):
            phone_val = payload.get("phone", {}).get("requested") if isinstance(payload.get("phone"), dict) else payload.get("phone") or payload.get("Phone", "")
            body["PhoneNumber"] = phone_val

        if payload.get("address") or payload.get("Address"):
            addr_val = payload.get("address", {}).get("requested") if isinstance(payload.get("address"), dict) else payload.get("address") or payload.get("Address", "")
            body["Address"] = addr_val

        if payload.get("city") or payload.get("City"):
            body["City"] = payload.get("city") or payload.get("City", "")

        if payload.get("state") or payload.get("State"):
            body["State"] = payload.get("state") or payload.get("State", "")

        if payload.get("alternative_phone") or payload.get("AlternativePhone"):
            body["AlternativePhone"] = payload.get("alternative_phone") or payload.get("AlternativePhone", "")

        logger.info(f"Pushing profile update to Prognosis for {enrollee_id}:")
        logger.info(f"  URL: {url}")
        logger.info(f"  Payload: {body}")
        result = await self._request("POST", url, db=db, json=body)
        logger.info(f"  Response: {result}")

        if "error" in result:
            logger.error(f"Prognosis profile update FAILED: {result}")
        else:
            logger.info(f"Prognosis profile update SUCCESS for {enrollee_id}")

        return result

    async def insert_or_update_medication(self, enrollee_id: str, payload: dict, db: Session = None) -> dict:
        """
        POST /PharmacyDelivery/InsertMemberDelivery
        Add new medication or update existing one in Prognosis.
        - Without EntryNo = new medication
        - With EntryNo = update existing medication
        """
        url = f"{self.base_url}/PharmacyDelivery/InsertMemberDelivery"
        body = {
            "EnrolleeId": enrollee_id,
        }

        # Map fields
        if payload.get("diagnosis_name") or payload.get("DiagnosisName"):
            body["DiagnosisName"] = payload.get("diagnosis_name") or payload.get("DiagnosisName", "")
        if payload.get("diagnosis_id") or payload.get("DiagnosisId"):
            body["DiagnosisId"] = payload.get("diagnosis_id") or payload.get("DiagnosisId", "")

        # Drug/Procedure info
        drug_name = (payload.get("drug_name") or payload.get("ProcedureName") or
                     payload.get("procedure_name") or payload.get("medication_name") or "")
        if drug_name:
            body["ProcedureName"] = drug_name

        procedure_id = payload.get("procedure_id") or payload.get("ProcedureId") or ""
        if procedure_id:
            body["ProcedureId"] = procedure_id

        quantity = payload.get("quantity") or payload.get("ProcedureQuantity") or payload.get("procedure_quantity")
        if quantity:
            body["ProcedureQuantity"] = int(quantity) if str(quantity).isdigit() else 1

        # Dosage / Directions
        dosage_val = payload.get("Dosage") or payload.get("dosage") or payload.get("DosageDescription") or payload.get("directions") or ""
        if dosage_val:
            body["DosageDescription"] = dosage_val

        # EntryNo for updates only (not for new medications)
        entry_no = payload.get("entry_no") or payload.get("EntryNo")
        if entry_no:
            body["EntryNo"] = int(entry_no)

        # Comment from member
        comment_val = payload.get("Comment") or payload.get("comment") or ""
        if comment_val:
            body["Comment"] = comment_val

        logger.info(f"Pushing medication {'update' if entry_no else 'insert'} to Prognosis for {enrollee_id}")
        logger.info(f"  Prognosis payload: {body}")
        result = await self._request("POST", url, db=db, json=body)

        logger.info(f"  Prognosis response: {result}")

        if "error" in result:
            logger.error(f"Prognosis medication push failed: {result}")
        else:
            logger.info(f"Prognosis medication push successful for {enrollee_id}")

        return result

    async def submit_change_request(self, payload: dict, db: Session = None) -> dict:
        """Route change requests to the appropriate Prognosis API."""
        request_type = payload.get("request_type", "")
        member_id = payload.get("member_id", "")
        action = payload.get("action", "")
        data = payload.get("payload", {})

        if request_type == "PROFILE_UPDATE":
            return await self.update_member_profile(member_id, data, db=db)

        elif request_type == "MEDICATION_CHANGE" and action in ("ADD", "MODIFY"):
            return await self.insert_or_update_medication(member_id, data, db=db)

        elif request_type == "MEDICATION_CHANGE" and action == "REMOVE":
            # For removal, we log it but Prognosis may not have a delete endpoint
            logger.info(f"Medication removal request for {member_id}: {data}")
            return {"status": "logged", "message": "Removal request logged for manual processing"}

        elif request_type == "REFILL_ACTION":
            # Refill requests may need a separate endpoint — log for now
            logger.info(f"Refill action for {member_id}: {action} - {data}")
            return {"status": "logged", "message": f"Refill {action} logged for processing"}

        else:
            logger.info(f"Unhandled request type {request_type}/{action} for {member_id}")
            return {"status": "queued", "message": "Request queued for manual processing"}


prognosis_client = PrognosisClient()
