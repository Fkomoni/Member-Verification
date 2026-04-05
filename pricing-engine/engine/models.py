"""Data models for the Leadway Householder Pricing Engine."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ClientType(str, Enum):
    CORPORATE = "corporate"
    INDIVIDUAL = "individual"


class Peril(str, Enum):
    FIRE = "fire"
    THEFT = "theft"
    FLOOD = "flood"
    ALL_PERILS = "all_perils"  # Combined cover


class CoverType(str, Enum):
    BASIC = "basic"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    STANDARD = "standard"


class Location(str, Enum):
    LAGOS = "lagos"
    ABUJA = "abuja"
    PORT_HARCOURT = "port_harcourt"
    IBADAN = "ibadan"
    KADUNA = "kaduna"
    OTHER = "other"


@dataclass
class RiskProfile:
    """Input risk profile for pricing."""
    client_type: ClientType
    sum_insured: float
    location: Location
    cover_type: CoverType = CoverType.STANDARD
    perils: list[Peril] = field(default_factory=lambda: [Peril.FIRE])
    building_age_years: int = 0
    has_security: bool = False
    has_fire_extinguisher: bool = False
    claims_history_count: int = 0  # claims in last 3 years
    policy_duration_months: int = 12


@dataclass
class PremiumBreakdown:
    """Output premium breakdown."""
    base_premium: float
    peril_loadings: dict[str, float]
    location_adjustment: float
    cover_type_adjustment: float
    claims_loading: float
    security_discount: float
    fire_equipment_discount: float
    duration_adjustment: float
    gross_premium: float
    commission: float
    net_premium: float
    # Per-peril breakdown
    fire_premium: float = 0.0
    theft_premium: float = 0.0
    flood_premium: float = 0.0
