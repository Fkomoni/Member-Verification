"""
WellaHealth API Client — live integration with Basic Auth.

Auth: Basic (Client ID : Client Secret)
Base URL: https://staging.wellahealth.com/public/v1
Partner Code: sent as header or in payload per endpoint

Handles:
- Drug list retrieval
- Order submission (acute medication fulfilment)
- Order status tracking
- Retry logic (3 attempts with backoff)
- Full request/response logging
"""

import asyncio
import base64
import logging
from dataclasses import dataclass, field

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(30.0)


@dataclass
class WellaHealthDrug:
    external_id: str
    name: str
    generic_name: str | None = None
    category: str | None = None
    price: float | None = None
    in_stock: bool = True


@dataclass
class WellaHealthOrderResponse:
    success: bool
    order_id: str | None = None
    reference: str | None = None
    status: str | None = None
    message: str = ""
    raw_response: dict = field(default_factory=dict)


class WellaHealthClient:
    """
    WellaHealth API client with Basic Auth.
    Falls back to mock mode if credentials are not configured.
    """

    def __init__(self):
        self.base_url = settings.WELLAHEALTH_BASE_URL.rstrip("/")
        self.partner_code = settings.WELLAHEALTH_PARTNER_CODE
        self.client_id = settings.WELLAHEALTH_CLIENT_ID
        self.client_secret = settings.WELLAHEALTH_CLIENT_SECRET
        self._mock_mode = not (self.client_id and self.client_secret)

        if self._mock_mode:
            logger.warning("WellaHealth: credentials not set — running in mock mode")

    def _auth_header(self) -> dict:
        """Build Basic Auth header."""
        creds = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(creds.encode()).decode()
        return {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json",
            "X-Partner-Code": self.partner_code,
        }

    async def _request(
        self, method: str, path: str, json_data: dict | None = None, params: dict | None = None,
    ) -> dict | None:
        """Make an authenticated request with retry logic."""
        url = f"{self.base_url}{path}"
        headers = self._auth_header()

        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                    resp = await client.request(
                        method, url, headers=headers, json=json_data, params=params,
                    )

                logger.info(
                    "WellaHealth %s %s → %d", method, path, resp.status_code,
                )

                if resp.status_code in (200, 201):
                    return resp.json() if resp.text else {}
                elif resp.status_code == 429:
                    # Rate limited — backoff
                    wait = 2 ** (attempt + 1)
                    logger.warning("WellaHealth rate limited, waiting %ds", wait)
                    await asyncio.sleep(wait)
                    continue
                else:
                    logger.error(
                        "WellaHealth %s %s failed: %d %s",
                        method, path, resp.status_code, resp.text[:300],
                    )
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    return None

            except httpx.RequestError as e:
                logger.error("WellaHealth request error (attempt %d): %s", attempt + 1, e)
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None

        return None

    # ── Drug List (Tariff) ──────────────────────────────────────

    async def get_drug_list(self, page: int = 1, page_size: int = 100) -> list[WellaHealthDrug]:
        """
        Fetch available drugs from WellaHealth tariff.
        GET /tariff?pageIndex={page}&pageSize={page_size}
        """
        if self._mock_mode:
            logger.info("WellaHealth drug list: mock mode")
            return []

        data = await self._request(
            "GET", "/tariff",
            params={"pageIndex": page, "pageSize": page_size},
        )
        if not data:
            return []

        items = data if isinstance(data, list) else data.get("data", data.get("results", data.get("items", [])))
        return [
            WellaHealthDrug(
                external_id=str(item.get("id", item.get("Id", ""))),
                name=item.get("name", item.get("drugName", item.get("drug_name", ""))),
                generic_name=item.get("genericName", item.get("generic_name")),
                category=item.get("category"),
                price=item.get("price", item.get("unitPrice")),
                in_stock=item.get("inStock", item.get("in_stock", True)),
            )
            for item in (items if isinstance(items, list) else [])
        ]

    # ── Pharmacy Search ───────────────────────────────────────────

    # ── Pharmacy Search ───────────────────────────────────────────

    async def search_pharmacies(
        self, state_name: str, lga_name: str = "", area_name: str = "",
    ) -> list[dict]:
        """
        Search for WellaHealth pharmacies near a location.
        GET /Pharmacies/search?stateName=...&lgaName=...&areaName=...

        Returns an empty list if credentials are not configured or if the API
        returns no results. LGA→state fallback is handled in the API layer.
        """
        if self._mock_mode:
            logger.info(
                "WellaHealth pharmacy search: credentials not configured — returning empty list"
            )
            return []

        params: dict = {"stateName": state_name}
        if lga_name:
            params["lgaName"] = lga_name
        if area_name:
            params["areaName"] = area_name

        data = await self._request("GET", "/Pharmacies/search", params=params)
        if not data:
            logger.warning(
                "WellaHealth pharmacy search: no data returned for state=%s lga=%s",
                state_name, lga_name,
            )
            return []

        # Handle response shapes: {data:[...]}, {result:[...]}, {pharmacies:[...]}, or direct list
        if isinstance(data, dict):
            items = (
                data.get("data") or data.get("result") or
                data.get("pharmacies") or data.get("items") or []
            )
        else:
            items = data

        return items if isinstance(items, list) else []

    # ── Fulfilment Submission ────────────────────────────────────

    async def submit_fulfilment(self, payload: dict) -> dict:
        """
        Submit an acute medication fulfilment.
        POST /v1/fulfilments

        Payload format:
        {
            "refId": "RX-12345",
            "pharmacyCode": "WHPTest1002",
            "fulfilmentService": "Acute",
            "diagnosis": "Malaria",
            "notes": "From Leadway Portal",
            "isDelivery": true,
            "patientData": {
                "firstName": "John", "lastName": "Doe",
                "hmoId": "123456", "phoneNumber": "2348012345678",
                "gender": "Male", "dateOfBirth": "1990-01-01",
                "address": "Lekki Phase 1, Lagos"
            },
            "drugs": [
                {"refId": "1", "name": "Coartem", "dose": "Tab bd 3/7",
                 "strength": "20/120mg", "frequency": "bd", "duration": "3/7"}
            ]
        }
        """
        if self._mock_mode:
            return {
                "success": True, "mock": True,
                "trackingCode": "MOCK-TRK-" + payload.get("refId", ""),
                "trackingLink": "",
            }

        data = await self._request("POST", "/fulfilments", json_data=payload)
        if data is not None:
            return {"success": True, **data}
        return {"success": False, "error": "Fulfilment submission failed"}

    # ── Legacy methods (kept for compatibility) ──────────────────

    async def submit_order(self, payload: dict) -> WellaHealthOrderResponse:
        """
        Submit an acute medication fulfilment to WellaHealth.
        POST /fulfilments

        Payload:
        {
            "partnerCode": "WHPXTest10123",
            "memberName": "John Doe",
            "memberNumber": "CIF12345",
            "address": "123 Main St, Ikeja, Lagos",
            "medications": [
                {"name": "Amoxicillin 500mg", "quantity": 15},
                ...
            ],
            "reference": "RX-20260409-A3F2B1"
        }
        """
        if self._mock_mode:
            logger.info("WellaHealth submit_order: mock mode")
            return WellaHealthOrderResponse(
                success=True,
                order_id="MOCK-WH-" + payload.get("reference", "001"),
                reference=payload.get("reference", ""),
                status="pending",
                message="Mock order accepted (WellaHealth credentials not configured)",
                raw_response={"mock": True},
            )

        # Build WellaHealth-specific payload
        wh_payload = {
            "partnerCode": self.partner_code,
            "memberName": payload.get("member_name", ""),
            "memberNumber": payload.get("enrollee_id", ""),
            "address": payload.get("delivery_address", ""),
            "medications": [
                {
                    "name": f"{med.get('drug_name', '')} {med.get('strength', '')}".strip(),
                    "quantity": med.get("quantity", 1),
                }
                for med in payload.get("medications", [])
            ],
            "reference": payload.get("reference", ""),
        }

        data = await self._request("POST", "/fulfilments", json_data=wh_payload)
        if data is not None:
            order_id = (
                data.get("id") or data.get("Id") or
                data.get("orderId") or data.get("order_id") or
                data.get("fulfilmentId") or
                (data.get("data", {}).get("id") if isinstance(data.get("data"), dict) else None)
            )
            return WellaHealthOrderResponse(
                success=True,
                order_id=str(order_id) if order_id else None,
                reference=payload.get("reference"),
                status=data.get("status", "submitted"),
                message=data.get("message", "Order submitted to WellaHealth"),
                raw_response=data,
            )

        return WellaHealthOrderResponse(
            success=False,
            message="Failed to submit fulfilment to WellaHealth after retries",
        )

    # ── Fulfilment Status ────────────────────────────────────────

    async def get_fulfilments(self, page: int = 1, page_size: int = 50) -> dict:
        """
        List fulfilments from WellaHealth.
        GET /fulfilments?pageIndex={page}&pageSize={page_size}
        """
        if self._mock_mode:
            return {"data": [], "mock": True}

        data = await self._request(
            "GET", "/fulfilments",
            params={"pageIndex": page, "pageSize": page_size},
        )
        return data or {"data": []}

    async def get_order_status(self, order_id: str) -> dict:
        """Check fulfilment status by ID."""
        if self._mock_mode:
            return {"order_id": order_id, "status": "pending", "mock": True}

        data = await self._request("GET", f"/fulfilments/{order_id}")
        return data or {"order_id": order_id, "status": "unknown"}


# Module-level singleton
wellahealth_client = WellaHealthClient()
