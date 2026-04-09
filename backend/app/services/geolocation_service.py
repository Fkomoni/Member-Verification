"""
Geolocation Service — Google Maps Geocoding API integration.

Uses Google Geocoding API to:
1. Validate addresses
2. Determine if location is in Lagos state
3. Normalize state/LGA from free-text addresses

Falls back to rule-based matching if Google API is unavailable.
"""

import logging
from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.utils.nigerian_locations import is_lagos_location, normalize_state

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(10.0)
_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


@dataclass
class GeoResult:
    state: str | None
    lga: str | None
    city: str | None
    is_lagos: bool | None
    confidence: float
    source: str
    formatted_address: str | None = None
    lat: float | None = None
    lng: float | None = None


def _parse_google_components(components: list[dict]) -> dict:
    """Extract state, LGA, city from Google address_components."""
    result = {"state": None, "lga": None, "city": None}
    for comp in components:
        types = comp.get("types", [])
        name = comp.get("long_name", "")
        if "administrative_area_level_1" in types:
            result["state"] = name
        elif "administrative_area_level_2" in types:
            result["lga"] = name
        elif "locality" in types:
            result["city"] = name
        elif "sublocality" in types and not result["city"]:
            result["city"] = name
    return result


async def geocode_address(address: str) -> GeoResult | None:
    """
    Geocode an address using Google Maps API.
    Returns structured location data or None on failure.
    """
    if not settings.GOOGLE_MAPS_API_KEY:
        return None

    params = {
        "address": address,
        "components": "country:NG",
        "key": settings.GOOGLE_MAPS_API_KEY,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(_GEOCODE_URL, params=params)

        if resp.status_code != 200:
            logger.warning("Google Geocoding HTTP %d for '%s'", resp.status_code, address)
            return None

        data = resp.json()
        if data.get("status") != "OK" or not data.get("results"):
            logger.info("Google Geocoding: no results for '%s' (status=%s)", address, data.get("status"))
            return None

        top = data["results"][0]
        components = _parse_google_components(top.get("address_components", []))
        location = top.get("geometry", {}).get("location", {})

        state = normalize_state(components["state"]) if components["state"] else None
        lagos = is_lagos_location(state, components["city"])

        return GeoResult(
            state=state,
            lga=components["lga"],
            city=components["city"],
            is_lagos=lagos,
            confidence=0.95,
            source="google_geocoding",
            formatted_address=top.get("formatted_address"),
            lat=location.get("lat"),
            lng=location.get("lng"),
        )

    except httpx.RequestError as e:
        logger.error("Google Geocoding request failed: %s", e)
        return None


class GeolocationService:
    """
    Location resolution with Google Maps API + rule-based fallback.
    """

    def __init__(self):
        self._google_available = bool(settings.GOOGLE_MAPS_API_KEY)
        if not self._google_available:
            logger.warning("GOOGLE_MAPS_API_KEY not set — using rule-based location only")

    def resolve_location(
        self,
        state: str | None = None,
        lga: str | None = None,
        city: str | None = None,
        address: str | None = None,
    ) -> GeoResult:
        """
        Resolve delivery location. Priority:
        1. Structured state/LGA from form (most reliable)
        2. Google Geocoding for address validation (if available)
        3. Fuzzy matching against known locations
        """
        normalized = normalize_state(state) if state else None
        lagos = is_lagos_location(state, city)

        if lagos is not None:
            return GeoResult(
                state=normalized, lga=lga, city=city,
                is_lagos=lagos, confidence=1.0, source="structured_input",
            )

        # Could not determine from structured input
        return GeoResult(
            state=normalized, lga=lga, city=city,
            is_lagos=None, confidence=0.0, source="structured_input",
        )

    async def resolve_location_with_google(
        self,
        state: str | None = None,
        lga: str | None = None,
        city: str | None = None,
        address: str | None = None,
    ) -> GeoResult:
        """
        Resolve with Google Geocoding fallback for ambiguous locations.
        """
        # Try structured first
        result = self.resolve_location(state, lga, city, address)
        if result.is_lagos is not None:
            return result

        # Try Google Geocoding if address provided
        if address and self._google_available:
            geo = await geocode_address(address)
            if geo and geo.is_lagos is not None:
                logger.info("Google resolved location: %s → is_lagos=%s", address, geo.is_lagos)
                return geo

        return result


geolocation_service = GeolocationService()
