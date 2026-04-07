"""
Official Leadway Householder Pricing Rates.

Source: PRICING.xlsx (official rate table from Leadway)

Two pricing tiers:
1. PRE-PRICED (Individual/Retail) — fixed rates
2. UNDERWRITTEN (Corporate) — variable rates by contingency band

Sections:
- Section 1: Building (Fire & Special Perils)
- Section 2: Content (Fire, Special Perils & Burglary)
- Accidental Damage to content
- All Risks Extension (max 10% of content SI)
- Personal Accident
- Alternative Accommodation
"""

from .models import ClientType, CoverType, Location

# =============================================================
# PRE-PRICED RATES (Individual/Retail) — from "Pre-Priced Rates"
# Expressed as decimal (e.g., 0.001 = 0.1% = 1.0 per mille)
# =============================================================

INDIVIDUAL_RATES = {
    "building":              0.001,    # 0.10% — Building: Fire & Special Perils
    "content":               0.002,    # 0.20% — Content: Fire, Special Perils & Burglary
    "accidental_damage":     0.00125,  # 0.125% — Accidental Damage to content
    "all_risks":             0.02,     # 2.0% — All Risks Extension (max 10% of content SI)
    "personal_accident":     0.00185,  # 0.185% — Personal Accident
    "alt_accommodation":     0.002,    # 0.20% — Alternative Accommodation
}

# =============================================================
# UNDERWRITTEN RATES (Corporate) — from "Pricing" sheet
# Four rate bands; we use Band 1 (lowest) as base for standard,
# and apply cover type multipliers for higher bands
# =============================================================

# Band mapping: Band 1=Basic, Band 2=Standard, Band 3=Enhanced, Band 4=Premium
CORPORATE_RATES = {
    "building": {
        "band_1": 0.00125,   # 0.125%
        "band_2": 0.0015,    # 0.15%
        "band_3": 0.00175,   # 0.175%
        "band_4": 0.00185,   # 0.185%
    },
    "content": {
        "band_1": 0.003,     # 0.30%
        "band_2": 0.0035,    # 0.35%
        "band_3": 0.0045,    # 0.45%
        "band_4": 0.005,     # 0.50%
    },
}

# Map cover types to corporate rate bands
CORPORATE_BAND_MAP: dict[CoverType, str] = {
    CoverType.BASIC:    "band_1",
    CoverType.BRONZE:   "band_1",
    CoverType.SILVER:   "band_2",
    CoverType.STANDARD: "band_2",
    CoverType.GOLD:     "band_3",
    CoverType.PLATINUM: "band_4",
}

# Corporate uses same rates as individual for additional coverages
CORPORATE_ADDITIONAL_RATES = {
    "accidental_damage":  0.00125,
    "all_risks":          0.02,
    "personal_accident":  0.00185,
    "alt_accommodation":  0.002,
}


def get_rates(client_type: ClientType, cover_type: CoverType) -> dict[str, float]:
    """Get applicable rates based on client type and cover."""
    if client_type == ClientType.INDIVIDUAL:
        return INDIVIDUAL_RATES.copy()
    else:
        band = CORPORATE_BAND_MAP.get(cover_type, "band_2")
        return {
            "building": CORPORATE_RATES["building"][band],
            "content": CORPORATE_RATES["content"][band],
            **CORPORATE_ADDITIONAL_RATES,
        }


# =============================================================
# LOCATION FACTORS
# Based on claims analysis: Lagos has highest exposure
# =============================================================

LOCATION_FACTORS: dict[Location, float] = {
    Location.LAGOS:         1.15,
    Location.ABUJA:         1.05,
    Location.PORT_HARCOURT: 1.10,
    Location.IBADAN:        0.95,
    Location.KADUNA:        0.90,
    Location.OTHER:         1.00,
}

# =============================================================
# COVER TYPE MULTIPLIERS (Individual only — Corporate uses bands)
# =============================================================

INDIVIDUAL_COVER_MULTIPLIERS: dict[CoverType, float] = {
    CoverType.BASIC:    0.85,
    CoverType.BRONZE:   0.90,
    CoverType.SILVER:   0.95,
    CoverType.STANDARD: 1.00,
    CoverType.GOLD:     1.10,
    CoverType.PLATINUM: 1.20,
}

# =============================================================
# CLAIMS HISTORY LOADING
# =============================================================

CLAIMS_LOADING: dict[int, float] = {
    0: 0.00,
    1: 0.10,
    2: 0.25,
    3: 0.50,
}
MAX_CLAIMS_LOADING = 0.75

# =============================================================
# DISCOUNTS
# =============================================================

# Individual security item discounts
SECURITY_DISCOUNTS = {
    "cctv": 0.02,            # 2%
    "electric_fence": 0.02,  # 2%
    "fire_alarm": 0.02,      # 2%
    "fire_extinguisher": 0.015,  # 1.5%
    "security_guard": 0.015, # 1.5%
    "burglar_proof": 0.01,   # 1%
}
# Maximum total security discount cap
MAX_SECURITY_DISCOUNT = 0.10  # 10%

# Legacy compatibility
SECURITY_DISCOUNT = 0.05
FIRE_EQUIPMENT_DISCOUNT = 0.03

# =============================================================
# BUILDING AGE LOADING
# =============================================================

def get_building_age_loading(age_years: int) -> float:
    if age_years <= 5:
        return 0.00
    elif age_years <= 15:
        return 0.05
    elif age_years <= 30:
        return 0.10
    else:
        return 0.20

# =============================================================
# COMMISSION & MINIMUMS
# =============================================================

COMMISSION_RATES: dict[ClientType, float] = {
    ClientType.CORPORATE: 0.15,
    ClientType.INDIVIDUAL: 0.15,
}

def get_volume_discount(total_si: float, client_type: ClientType) -> float:
    if client_type == ClientType.CORPORATE:
        if total_si >= 1_000_000_000:
            return 0.10
        elif total_si >= 500_000_000:
            return 0.07
        elif total_si >= 100_000_000:
            return 0.04
    else:
        if total_si >= 100_000_000:
            return 0.05
        elif total_si >= 50_000_000:
            return 0.03
    return 0.00

MINIMUM_PREMIUMS: dict[ClientType, float] = {
    ClientType.CORPORATE: 25_000.0,
    ClientType.INDIVIDUAL: 5_000.0,
}

# All Risks Extension cap: max 10% of content sum insured
ALL_RISKS_MAX_PCT = 0.10
