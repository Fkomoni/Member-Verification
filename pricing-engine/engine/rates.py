"""
Rate tables derived from Leadway Householder Report analysis.

Data source: Householder Report.xlsx (2022-2025)
- 8,906 production records, N845.5M total premium
- 342 claims, N219M total paid
- Overall loss ratio: 34.6%

Key findings:
- Corporate loss ratio: 13.4% (low risk)
- Individual loss ratio: 31.5% (higher risk)
- Corporate median rate: 0.65 per mille
- Individual median rate: 1.95 per mille
"""

from .models import ClientType, CoverType, Location, Peril

# === BASE RATES (per mille of sum insured) ===
# Derived from actual premium/sum_insured analysis
# Separated by client type and peril

BASE_RATES: dict[ClientType, dict[Peril, float]] = {
    ClientType.CORPORATE: {
        # Corporate: lower frequency, moderate severity
        # Fire: 5 claims, N5M paid, N265M premium base
        Peril.FIRE: 0.45,
        # Theft: 4 claims, N1.1M paid — low severity for corporate
        Peril.THEFT: 0.25,
        # Flood: 1 claim (via "various"), rare but catastrophic
        Peril.FLOOD: 0.35,
    },
    ClientType.INDIVIDUAL: {
        # Individual: higher frequency across all perils
        # Fire: 12 claims, N27.8M paid — high severity
        Peril.FIRE: 1.20,
        # Theft: 44 claims, N39.3M — highest volume peril
        Peril.THEFT: 0.95,
        # Flood: 12 claims, N36.2M — highest avg severity (N3M/claim)
        Peril.FLOOD: 1.50,
    },
}

# === LOCATION FACTORS ===
# Based on branch premium concentration and claims distribution
# Lagos (Corp Office + Ikeja + Lekki + Festac + Ikorodu) = ~78% of premium
LOCATION_FACTORS: dict[Location, float] = {
    Location.LAGOS: 1.15,          # Highest exposure — flood, theft risk
    Location.ABUJA: 1.05,          # Moderate — fire risk from power surges
    Location.PORT_HARCOURT: 1.10,  # Flood-prone, industrial exposure
    Location.IBADAN: 0.95,         # Lower claims frequency
    Location.KADUNA: 0.90,         # Lower exposure
    Location.OTHER: 1.00,          # Baseline
}

# Flood-specific location surcharges (flood is location-sensitive)
FLOOD_LOCATION_SURCHARGE: dict[Location, float] = {
    Location.LAGOS: 0.30,          # High flood risk
    Location.PORT_HARCOURT: 0.25,  # Coastal/riverine
    Location.ABUJA: 0.05,
    Location.IBADAN: 0.10,
    Location.KADUNA: 0.05,
    Location.OTHER: 0.10,
}

# === COVER TYPE MULTIPLIERS ===
# Derived from actual avg premium by cover type
# Standard = 1.0 baseline (N98K avg premium)
COVER_TYPE_MULTIPLIERS: dict[CoverType, float] = {
    CoverType.BASIC: 0.50,      # N5K avg — minimal cover
    CoverType.BRONZE: 0.65,     # N19K avg
    CoverType.SILVER: 0.80,     # N31K avg
    CoverType.STANDARD: 1.00,   # N98K avg — baseline
    CoverType.GOLD: 1.15,       # N54K avg but broader cover
    CoverType.PLATINUM: 1.30,   # N76K avg — comprehensive
}

# === CLAIMS HISTORY LOADING ===
# Penalize repeat claimants (data shows some insureds with 5+ claims)
CLAIMS_LOADING: dict[int, float] = {
    0: 0.00,    # No claims — no loading
    1: 0.10,    # 1 claim — 10% loading
    2: 0.25,    # 2 claims — 25% loading
    3: 0.50,    # 3 claims — 50% loading
}
MAX_CLAIMS_LOADING = 0.75  # Cap at 75% for 4+ claims

# === DISCOUNT FACTORS ===
SECURITY_DISCOUNT = 0.05          # 5% discount for security systems
FIRE_EQUIPMENT_DISCOUNT = 0.03    # 3% discount for fire extinguishers

# === BUILDING AGE LOADING ===
# Older buildings = higher fire/structural risk
def get_building_age_loading(age_years: int) -> float:
    if age_years <= 5:
        return 0.00
    elif age_years <= 15:
        return 0.05
    elif age_years <= 30:
        return 0.10
    else:
        return 0.20

# === COMMISSION RATES ===
# From data: commission ~15-20% of gross premium
COMMISSION_RATES: dict[ClientType, float] = {
    ClientType.CORPORATE: 0.15,   # 15% for corporate (broker-driven)
    ClientType.INDIVIDUAL: 0.15,  # 15% for individual (agent-driven)
}

# === SUM INSURED BANDS (for volume discount) ===
def get_volume_discount(sum_insured: float, client_type: ClientType) -> float:
    """Large sum insured gets a volume discount."""
    if client_type == ClientType.CORPORATE:
        if sum_insured >= 1_000_000_000:  # 1B+
            return 0.10
        elif sum_insured >= 500_000_000:  # 500M+
            return 0.07
        elif sum_insured >= 100_000_000:  # 100M+
            return 0.04
    else:
        if sum_insured >= 100_000_000:   # 100M+
            return 0.05
        elif sum_insured >= 50_000_000:  # 50M+
            return 0.03
    return 0.00

# === MINIMUM PREMIUMS ===
MINIMUM_PREMIUMS: dict[ClientType, float] = {
    ClientType.CORPORATE: 25_000.0,   # N25K minimum
    ClientType.INDIVIDUAL: 5_000.0,   # N5K minimum
}
