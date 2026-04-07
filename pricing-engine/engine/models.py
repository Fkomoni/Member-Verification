"""Data models for the Leadway Householder Pricing Engine."""

from dataclasses import dataclass, field
from enum import Enum


class ClientType(str, Enum):
    CORPORATE = "corporate"
    INDIVIDUAL = "individual"


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
    building_sum_insured: float  # Sum insured for building
    content_sum_insured: float   # Sum insured for household contents
    location: Location
    cover_type: CoverType = CoverType.STANDARD
    # Coverage selections
    include_building: bool = True            # Section 1: Fire & Special Perils on building
    include_content: bool = True             # Section 2: Fire, Special Perils & Burglary on content
    include_accidental_damage: bool = False  # Accidental damage to content
    include_all_risks: bool = False          # All risks extension (max 10% of content SI)
    include_personal_accident: bool = False  # Personal accident cover
    include_alt_accommodation: bool = False  # Alternative accommodation
    # Risk factors
    building_age_years: int = 0
    has_security: bool = False
    has_fire_extinguisher: bool = False
    security_items: list[str] = field(default_factory=list)  # e.g. ["cctv", "electric_fence", "fire_alarm"]
    claims_history_count: int = 0
    policy_duration_months: int = 12


@dataclass
class PremiumBreakdown:
    """Output premium breakdown."""
    # Section premiums
    building_premium: float
    content_premium: float
    accidental_damage_premium: float
    all_risks_premium: float
    personal_accident_premium: float
    alt_accommodation_premium: float
    # Base = sum of all section premiums
    base_premium: float
    # Adjustments
    location_adjustment: float
    cover_type_adjustment: float
    claims_loading: float
    security_discount: float
    fire_equipment_discount: float
    duration_adjustment: float
    # Totals
    gross_premium: float
    commission: float
    net_premium: float
    # Meta
    rate_per_mille: float = 0.0
