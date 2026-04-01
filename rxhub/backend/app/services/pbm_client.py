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


class PBMClient:
    """Client for the external PBM system API."""

    def __init__(self):
        self.base_url = settings.PBM_API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {settings.PBM_API_KEY}",
            "Content-Type": "application/json",
        }
        self.timeout = settings.PBM_API_TIMEOUT

    async def _request(
        self, method: str, path: str, db: Optional[Session] = None, **kwargs
    ) -> dict:
        url = f"{self.base_url}{path}"
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(
                        method, url, headers=self.headers, **kwargs
                    )
                    data = response.json() if response.content else {}

                    if db:
                        self._log_sync(db, path, method, kwargs.get("json"), data, response.status_code, response.is_success)

                    if response.is_success:
                        return data

                    last_error = f"HTTP {response.status_code}: {data}"
                    if response.status_code < 500:
                        break  # Don't retry client errors

            except httpx.TimeoutException as e:
                last_error = f"Timeout: {str(e)}"
                logger.warning(f"PBM API timeout (attempt {attempt + 1}): {path}")
            except httpx.RequestError as e:
                last_error = f"Connection error: {str(e)}"
                logger.warning(f"PBM API error (attempt {attempt + 1}): {path} - {e}")

            if attempt < MAX_RETRIES - 1:
                import asyncio
                await asyncio.sleep(RETRY_DELAYS[attempt])

        logger.error(f"PBM API failed after {MAX_RETRIES} retries: {path} - {last_error}")
        return {"error": last_error, "success": False}

    def _log_sync(
        self, db: Session, endpoint: str, method: str,
        request_body: dict, response_body: dict,
        status_code: int, success: bool,
    ):
        log = SyncLog(
            entity_type="PBM_API",
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

    async def validate_member(self, member_id: str, phone: str, db: Session = None) -> dict:
        """POST /external-api/member/validate — primary login."""
        return await self._request(
            "POST", "/external-api/member/validate",
            db=db,
            json={"member_id": member_id, "phone": phone},
        )

    async def get_member(self, member_id: str, db: Session = None) -> dict:
        """GET /external-api/member/{member_id} — fetch member profile."""
        return await self._request("GET", f"/external-api/member/{member_id}", db=db)

    async def get_member_medications(self, member_id: str, db: Session = None) -> dict:
        """GET /external-api/member/{member_id}/medications."""
        return await self._request("GET", f"/external-api/member/{member_id}/medications", db=db)

    async def submit_change_request(self, payload: dict, db: Session = None) -> dict:
        """POST /external-api/requests — push approved request to PBM."""
        return await self._request("POST", "/external-api/requests", db=db, json=payload)

    async def sync_member_data(self, member_id: str, db: Session = None) -> dict:
        """Full member data sync from PBM."""
        return await self._request("GET", f"/external-api/member/{member_id}/full-sync", db=db)


pbm_client = PBMClient()
