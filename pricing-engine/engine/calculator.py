"""
Leadway Householder Premium Calculator.

Calculates premiums for Fire, Theft, and Flood perils
with separate logic for Corporate and Individual segments.
"""

from .models import (
    ClientType, CoverType, Peril, RiskProfile, PremiumBreakdown
)
from .rates import (
    BASE_RATES, LOCATION_FACTORS, FLOOD_LOCATION_SURCHARGE,
    COVER_TYPE_MULTIPLIERS, CLAIMS_LOADING, MAX_CLAIMS_LOADING,
    SECURITY_DISCOUNT, FIRE_EQUIPMENT_DISCOUNT,
    COMMISSION_RATES, MINIMUM_PREMIUMS,
    get_building_age_loading, get_volume_discount,
)


def calculate_premium(risk: RiskProfile) -> PremiumBreakdown:
    """Calculate premium for a given risk profile."""

    rates = BASE_RATES[risk.client_type]
    location_factor = LOCATION_FACTORS[risk.location]

    # --- Per-peril premium calculation ---
    fire_premium = 0.0
    theft_premium = 0.0
    flood_premium = 0.0
    peril_details = {}

    for peril in risk.perils:
        base_rate = rates[peril]
        peril_premium = risk.sum_insured * base_rate / 1000

        # Flood gets extra location surcharge
        if peril == Peril.FLOOD:
            flood_surcharge = FLOOD_LOCATION_SURCHARGE[risk.location]
            peril_premium *= (1 + flood_surcharge)

        peril_details[peril.value] = peril_premium

        if peril == Peril.FIRE:
            fire_premium = peril_premium
        elif peril == Peril.THEFT:
            theft_premium = peril_premium
        elif peril == Peril.FLOOD:
            flood_premium = peril_premium

    base_premium = sum(peril_details.values())

    # --- Location adjustment (non-flood) ---
    location_adj = base_premium * (location_factor - 1.0)
    adjusted = base_premium + location_adj

    # --- Cover type multiplier ---
    cover_mult = COVER_TYPE_MULTIPLIERS[risk.cover_type]
    cover_adj = adjusted * (cover_mult - 1.0)
    adjusted += cover_adj

    # --- Building age loading ---
    age_loading = get_building_age_loading(risk.building_age_years)
    age_adj = adjusted * age_loading
    adjusted += age_adj

    # --- Claims history loading ---
    claims_count = min(risk.claims_history_count, 4)
    if claims_count >= 4:
        claims_factor = MAX_CLAIMS_LOADING
    else:
        claims_factor = CLAIMS_LOADING.get(claims_count, 0.0)
    claims_adj = adjusted * claims_factor
    adjusted += claims_adj

    # --- Discounts ---
    security_disc = adjusted * SECURITY_DISCOUNT if risk.has_security else 0.0
    fire_disc = adjusted * FIRE_EQUIPMENT_DISCOUNT if risk.has_fire_extinguisher else 0.0
    adjusted -= (security_disc + fire_disc)

    # --- Volume discount ---
    vol_disc = get_volume_discount(risk.sum_insured, risk.client_type)
    adjusted *= (1 - vol_disc)

    # --- Duration adjustment (pro-rata for short period) ---
    duration_factor = risk.policy_duration_months / 12.0
    if duration_factor < 1.0:
        # Short period loading: less than 12 months costs proportionally more
        duration_factor = max(duration_factor, 0.25)  # minimum 3 months
        short_period_loading = 1.0 + (1.0 - duration_factor) * 0.15
        duration_factor *= short_period_loading
    duration_adj = adjusted * (duration_factor - 1.0)
    gross_premium = adjusted + duration_adj

    # --- Apply minimum premium ---
    minimum = MINIMUM_PREMIUMS[risk.client_type]
    gross_premium = max(gross_premium, minimum)

    # --- Commission ---
    comm_rate = COMMISSION_RATES[risk.client_type]
    commission = gross_premium * comm_rate
    net_premium = gross_premium - commission

    return PremiumBreakdown(
        base_premium=round(base_premium, 2),
        peril_loadings=peril_details,
        location_adjustment=round(location_adj, 2),
        cover_type_adjustment=round(cover_adj, 2),
        claims_loading=round(claims_adj, 2),
        security_discount=round(security_disc, 2),
        fire_equipment_discount=round(fire_disc, 2),
        duration_adjustment=round(duration_adj, 2),
        gross_premium=round(gross_premium, 2),
        commission=round(commission, 2),
        net_premium=round(net_premium, 2),
        fire_premium=round(fire_premium, 2),
        theft_premium=round(theft_premium, 2),
        flood_premium=round(flood_premium, 2),
    )
