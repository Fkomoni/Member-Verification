"""
Geolocation Service — Google Maps API integration point.

Phase 1: Mock implementation using Nigerian location utility.
Phase 4: Replace with live Google Geocoding / Places API calls.

Integration points marked with # TODO: GOOGLE_GEO_INTEGRATION
"""

import logging
from dataclasses import dataclass

from app.core.config import settings
from app.utils.nigerian_locations import is_lagos_location, normalize_state

logger = logging.getLogger(__name__)


@dataclass
class GeoResult:
    """Standardized geolocation result."""
    state: str | None
    lga: str | None
    city: str | None
    is_lagos: bool | None
    confidence: float  # 0.0–1.0
    source: str  # "structured_input" | "google_geocoding" | "google_places"
    raw_response: dict | None = None


class GeolocationService:
    """
    Adapter for geolocation resolution.

    Current: rule-based using structured input from the form.
    Future: Google Geocoding API for address validation & coordinate lookup.
    """

    def __init__(self):
        # TODO: GOOGLE_GEO_INTEGRATION — Initialize Google Maps client
        # self.google_api_key = settings.GOOGLE_MAPS_API_KEY
        # self.client = googlemaps.Client(key=self.google_api_key)
        self._mock_mode = True  # Flip to False when Google API is connected

    def resolve_location(
        self,
        state: str | None = None,
        lga: str | None = None,
        city: str | None = None,
        address: str | None = None,
    ) -> GeoResult:
        """
        Resolve a delivery location to determine Lagos vs outside Lagos.

        Priority:
        1. Structured state/LGA from form (most reliable)
        2. Google Geocoding API validation (future)
        3. Fuzzy matching against known locations (fallback)
        """
        # Step 1: Use structured input
        normalized = normalize_state(state) if state else None
        lagos = is_lagos_location(state, city)

        if lagos is not None:
            logger.info(
                "Location resolved via structured input: state=%s, is_lagos=%s",
                normalized, lagos,
            )
            return GeoResult(
                state=normalized,
                lga=lga,
                city=city,
                is_lagos=lagos,
                confidence=1.0,
                source="structured_input",
            )

        # TODO: GOOGLE_GEO_INTEGRATION — Step 2: Validate via Google Geocoding
        # if address and not self._mock_mode:
        #     try:
        #         geocode_result = self.client.geocode(
        #             address, components={"country": "NG"}
        #         )
        #         if geocode_result:
        #             # Parse state from address_components
        #             # Determine is_lagos from parsed state
        #             pass
        #     except Exception as e:
        #         logger.warning("Google Geocoding failed: %s", e)

        # Step 3: Could not determine — will trigger manual review
        logger.warning(
            "Could not resolve location: state=%s, city=%s, address=%s",
            state, city, address,
        )
        return GeoResult(
            state=normalized,
            lga=lga,
            city=city,
            is_lagos=None,
            confidence=0.0,
            source="structured_input",
        )

    # TODO: GOOGLE_GEO_INTEGRATION — Address autocomplete for frontend
    # def autocomplete_address(self, query: str) -> list[dict]:
    #     """Google Places autocomplete for Nigerian addresses."""
    #     results = self.client.places_autocomplete(
    #         query,
    #         components={"country": "ng"},
    #         types=["address"],
    #     )
    #     return [{"description": r["description"], "place_id": r["place_id"]}
    #             for r in results]

    # TODO: GOOGLE_GEO_INTEGRATION — Reverse geocode from coordinates
    # def reverse_geocode(self, lat: float, lng: float) -> GeoResult:
    #     """Convert coordinates to structured address."""
    #     result = self.client.reverse_geocode((lat, lng))
    #     ...


# Module-level singleton
geolocation_service = GeolocationService()
