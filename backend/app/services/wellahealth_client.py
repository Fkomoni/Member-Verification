"""
WellaHealth API Client — integration adapter.

Phase 1: Mock implementation with clearly marked integration points.
Phase 6: Replace with live WellaHealth API calls.

Integration points marked with # TODO: WELLAHEALTH_INTEGRATION
"""

import logging
from dataclasses import dataclass, field

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class WellaHealthDrug:
    """Standardized drug representation from WellaHealth."""
    external_id: str
    name: str
    generic_name: str | None = None
    category: str | None = None  # WellaHealth's own classification if any
    price: float | None = None
    in_stock: bool = True


@dataclass
class WellaHealthOrderResponse:
    """Response from a WellaHealth order submission."""
    success: bool
    order_id: str | None = None
    reference: str | None = None
    status: str | None = None
    message: str = ""
    raw_response: dict = field(default_factory=dict)


class WellaHealthClient:
    """
    Adapter for the WellaHealth API.

    Handles:
    - Drug list retrieval (for syncing with drug_master)
    - Acute medication order submission
    - Order status tracking
    - Retry logic and error handling

    All methods currently return mock data.
    """

    def __init__(self):
        # TODO: WELLAHEALTH_INTEGRATION — Set from environment
        # self.base_url = settings.WELLAHEALTH_BASE_URL
        # self.api_key = settings.WELLAHEALTH_API_KEY
        # self.timeout = 30
        self._mock_mode = True

    # ── Drug List (for drug_master sync) ─────────────────────────

    async def get_drug_list(self) -> list[WellaHealthDrug]:
        """
        Fetch available drugs from WellaHealth.

        TODO: WELLAHEALTH_INTEGRATION
        When WellaHealth Postman collection is available, implement:
        - GET {base_url}/drugs or /products or /formulary
        - Map response to WellaHealthDrug objects
        - Use for syncing into drug_master table
        """
        if self._mock_mode:
            logger.info("WellaHealth drug list: returning mock data")
            return []

        # TODO: WELLAHEALTH_INTEGRATION — Live implementation
        # async with httpx.AsyncClient(timeout=self.timeout) as client:
        #     response = await client.get(
        #         f"{self.base_url}/drugs",
        #         headers={"Authorization": f"Bearer {self.api_key}"},
        #     )
        #     response.raise_for_status()
        #     data = response.json()
        #     return [WellaHealthDrug(**item) for item in data["drugs"]]

    # ── Order Submission (acute prescriptions) ───────────────────

    async def submit_order(self, payload: dict) -> WellaHealthOrderResponse:
        """
        Submit an acute medication order to WellaHealth.

        TODO: WELLAHEALTH_INTEGRATION
        Expected payload structure (to be confirmed):
        {
            "reference": "RX-20260409-0001",
            "enrollee_id": "CIF12345",
            "member_name": "John Doe",
            "medications": [
                {
                    "drug_name": "Amoxicillin",
                    "dosage": "500mg",
                    "quantity": 15,
                    "duration": "5 days"
                }
            ],
            "delivery_address": {...},
            "provider": {...},
            "urgency": "routine"
        }
        """
        if self._mock_mode:
            logger.info("WellaHealth order submission: mock mode, payload=%s", payload)
            return WellaHealthOrderResponse(
                success=True,
                order_id="MOCK-WH-001",
                reference=payload.get("reference", ""),
                status="pending",
                message="Mock order accepted",
                raw_response={"mock": True},
            )

        # TODO: WELLAHEALTH_INTEGRATION — Live implementation
        # async with httpx.AsyncClient(timeout=self.timeout) as client:
        #     for attempt in range(3):  # retry up to 3 times
        #         try:
        #             response = await client.post(
        #                 f"{self.base_url}/orders",
        #                 json=payload,
        #                 headers={
        #                     "Authorization": f"Bearer {self.api_key}",
        #                     "Content-Type": "application/json",
        #                 },
        #             )
        #             response.raise_for_status()
        #             data = response.json()
        #             return WellaHealthOrderResponse(
        #                 success=True,
        #                 order_id=data.get("order_id"),
        #                 reference=data.get("reference"),
        #                 status=data.get("status"),
        #                 message="Order submitted",
        #                 raw_response=data,
        #             )
        #         except httpx.HTTPStatusError as e:
        #             logger.error("WellaHealth API error (attempt %d): %s", attempt+1, e)
        #             if attempt == 2:
        #                 return WellaHealthOrderResponse(
        #                     success=False,
        #                     message=f"API error: {e.response.status_code}",
        #                 )

    # ── Order Status ─────────────────────────────────────────────

    async def get_order_status(self, order_id: str) -> dict:
        """
        Check fulfilment status of a WellaHealth order.

        TODO: WELLAHEALTH_INTEGRATION
        """
        if self._mock_mode:
            return {"order_id": order_id, "status": "pending", "mock": True}

        # TODO: WELLAHEALTH_INTEGRATION
        # GET {base_url}/orders/{order_id}/status


# Module-level singleton
wellahealth_client = WellaHealthClient()
