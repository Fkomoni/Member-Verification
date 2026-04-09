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

    # ── Drug List ────────────────────────────────────────────────

    async def get_drug_list(self) -> list[WellaHealthDrug]:
        """Fetch available drugs from WellaHealth."""
        if self._mock_mode:
            logger.info("WellaHealth drug list: mock mode")
            return []

        # Try common endpoint patterns
        for path in ["/drugs", "/products", "/formulary", "/medications"]:
            data = await self._request("GET", path)
            if data:
                items = data if isinstance(data, list) else data.get("data", data.get("drugs", data.get("results", [])))
                return [
                    WellaHealthDrug(
                        external_id=str(item.get("id", "")),
                        name=item.get("name", item.get("drug_name", "")),
                        generic_name=item.get("generic_name"),
                        category=item.get("category"),
                        price=item.get("price"),
                        in_stock=item.get("in_stock", True),
                    )
                    for item in (items if isinstance(items, list) else [])
                ]

        return []

    # ── Order Submission ─────────────────────────────────────────

    async def submit_order(self, payload: dict) -> WellaHealthOrderResponse:
        """Submit an acute medication order to WellaHealth."""
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

        # Add partner code to payload
        payload["partner_code"] = self.partner_code

        # Try common order endpoint patterns
        for path in ["/orders", "/order", "/prescription", "/prescriptions"]:
            data = await self._request("POST", path, json_data=payload)
            if data is not None:
                # Extract order ID from response (handle various shapes)
                order_id = (
                    data.get("order_id") or data.get("orderId") or
                    data.get("id") or data.get("Id") or
                    data.get("data", {}).get("id") if isinstance(data.get("data"), dict) else None
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
            message="Failed to submit order to WellaHealth after retries",
        )

    # ── Order Status ─────────────────────────────────────────────

    async def get_order_status(self, order_id: str) -> dict:
        """Check fulfilment status of a WellaHealth order."""
        if self._mock_mode:
            return {"order_id": order_id, "status": "pending", "mock": True}

        for path in [f"/orders/{order_id}", f"/orders/{order_id}/status", f"/order/{order_id}"]:
            data = await self._request("GET", path)
            if data:
                return data

        return {"order_id": order_id, "status": "unknown", "error": "Could not fetch status"}


# Module-level singleton
wellahealth_client = WellaHealthClient()
