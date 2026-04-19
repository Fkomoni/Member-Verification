from datetime import datetime, time
from enum import Enum
from typing import Optional
from zoneinfo import ZoneInfo


NIGERIA_TZ = ZoneInfo("Africa/Lagos")
BUSINESS_START = time(8, 0)
BUSINESS_END = time(17, 0)


class MedicationType(str, Enum):
    ACUTE = "acute"
    CHRONIC = "chronic"
    MIXED = "mixed"
    HORMONAL = "hormonal"
    CANCER = "cancer"


class Destination(str, Enum):
    LEADWAY_WHATSAPP = "leadway whatsapp"
    WELLAHEALTH = "wellahealth"
    WHATSAPP = "whatsapp"


def _is_business_hours(now: datetime) -> bool:
    local = now.astimezone(NIGERIA_TZ)
    if local.weekday() >= 5:
        return False
    return BUSINESS_START <= local.time() < BUSINESS_END


def _normalize_location(location: str) -> str:
    return (location or "").strip().lower()


def route_prescription(
    medication_type: MedicationType,
    location: str,
    now: Optional[datetime] = None,
) -> Destination:
    now = now or datetime.now(tz=NIGERIA_TZ)
    is_lagos = _normalize_location(location) == "lagos"

    if medication_type == MedicationType.ACUTE:
        if is_lagos and _is_business_hours(now):
            return Destination.LEADWAY_WHATSAPP
        return Destination.WELLAHEALTH

    return Destination.WHATSAPP
