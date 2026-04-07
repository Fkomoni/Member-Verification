"""
Leadway Householder Premium Calculator.

Uses official Leadway rate tables:
- Pre-priced rates for Individual/Retail
- Underwritten rates (4 bands) for Corporate
- Separate Building vs Content sections
- Additional coverages: Accidental Damage, All Risks, PA, Alt Accommodation
"""

from .models import ClientType, CoverType, RiskProfile, PremiumBreakdown
from .rates import (
    get_rates, LOCATION_FACTORS, INDIVIDUAL_COVER_MULTIPLIERS,
    CLAIMS_LOADING, MAX_CLAIMS_LOADING,
    SECURITY_DISCOUNT, FIRE_EQUIPMENT_DISCOUNT,
    SECURITY_DISCOUNTS, MAX_SECURITY_DISCOUNT,
    COMMISSION_RATES, MINIMUM_PREMIUMS, ALL_RISKS_MAX_PCT,
    get_building_age_loading, get_volume_discount,
)


def calculate_premium(risk: RiskProfile) -> PremiumBreakdown:
    """Calculate premium for a given risk profile."""

    rates = get_rates(risk.client_type, risk.cover_type)
    total_si = risk.building_sum_insured + risk.content_sum_insured

    # --- Section premiums (rate x sum insured) ---
    building_prem = 0.0
    content_prem = 0.0
    accidental_prem = 0.0
    all_risks_prem = 0.0
    pa_prem = 0.0
    alt_acc_prem = 0.0

    if risk.include_building and risk.building_sum_insured > 0:
        building_prem = risk.building_sum_insured * rates["building"]

    if risk.include_content and risk.content_sum_insured > 0:
        content_prem = risk.content_sum_insured * rates["content"]

    if risk.include_accidental_damage and risk.content_sum_insured > 0:
        # Accidental Damage limited to 40% of content sum insured
        ad_limit = risk.content_sum_insured * 0.40
        accidental_prem = ad_limit * rates["accidental_damage"]

    if risk.include_all_risks and risk.content_sum_insured > 0:
        # All risks applies to max 10% of content sum insured
        all_risks_si = risk.content_sum_insured * ALL_RISKS_MAX_PCT
        all_risks_prem = all_risks_si * rates["all_risks"]

    if risk.include_personal_accident and total_si > 0:
        pa_prem = total_si * rates["personal_accident"]

    if risk.include_alt_accommodation and risk.building_sum_insured > 0:
        alt_acc_prem = risk.building_sum_insured * rates["alt_accommodation"]

    base_premium = (
        building_prem + content_prem + accidental_prem +
        all_risks_prem + pa_prem + alt_acc_prem
    )

    # --- Location adjustment ---
    location_factor = LOCATION_FACTORS[risk.location]
    location_adj = base_premium * (location_factor - 1.0)
    adjusted = base_premium + location_adj

    # --- Cover type adjustment (Individual only; Corporate uses rate bands) ---
    cover_adj = 0.0
    if risk.client_type == ClientType.INDIVIDUAL:
        cover_mult = INDIVIDUAL_COVER_MULTIPLIERS[risk.cover_type]
        cover_adj = adjusted * (cover_mult - 1.0)
        adjusted += cover_adj

    # --- Building age loading ---
    age_loading = get_building_age_loading(risk.building_age_years)
    age_adj = adjusted * age_loading
    adjusted += age_adj

    # --- Claims history loading ---
    claims_count = min(risk.claims_history_count, 4)
    claims_factor = MAX_CLAIMS_LOADING if claims_count >= 4 else CLAIMS_LOADING.get(claims_count, 0.0)
    claims_adj = adjusted * claims_factor
    adjusted += claims_adj

    # --- Security & Equipment Discounts ---
    if risk.security_items:
        # Use itemized security discounts
        total_sec_pct = sum(SECURITY_DISCOUNTS.get(item, 0) for item in risk.security_items)
        total_sec_pct = min(total_sec_pct, MAX_SECURITY_DISCOUNT)  # Cap at 10%
        security_disc = adjusted * total_sec_pct
        fire_disc = 0.0  # included in itemized
    else:
        # Legacy fallback
        security_disc = adjusted * SECURITY_DISCOUNT if risk.has_security else 0.0
        fire_disc = adjusted * FIRE_EQUIPMENT_DISCOUNT if risk.has_fire_extinguisher else 0.0
    adjusted -= (security_disc + fire_disc)

    # --- Volume discount ---
    vol_disc = get_volume_discount(total_si, risk.client_type)
    adjusted *= (1 - vol_disc)

    # --- Duration adjustment ---
    duration_factor = risk.policy_duration_months / 12.0
    if duration_factor < 1.0:
        duration_factor = max(duration_factor, 0.25)
        short_period_loading = 1.0 + (1.0 - duration_factor) * 0.15
        duration_factor *= short_period_loading
    duration_adj = adjusted * (duration_factor - 1.0)
    gross_premium = adjusted + duration_adj

    # --- Minimum premium ---
    minimum = MINIMUM_PREMIUMS[risk.client_type]
    gross_premium = max(gross_premium, minimum)

    # --- Commission ---
    comm_rate = COMMISSION_RATES[risk.client_type]
    commission = gross_premium * comm_rate
    net_premium = gross_premium - commission

    # Rate per mille
    rate_per_mille = (gross_premium / total_si * 1000) if total_si > 0 else 0

    return PremiumBreakdown(
        building_premium=round(building_prem, 2),
        content_premium=round(content_prem, 2),
        accidental_damage_premium=round(accidental_prem, 2),
        all_risks_premium=round(all_risks_prem, 2),
        personal_accident_premium=round(pa_prem, 2),
        alt_accommodation_premium=round(alt_acc_prem, 2),
        base_premium=round(base_premium, 2),
        location_adjustment=round(location_adj, 2),
        cover_type_adjustment=round(cover_adj, 2),
        claims_loading=round(claims_adj, 2),
        security_discount=round(security_disc, 2),
        fire_equipment_discount=round(fire_disc, 2),
        duration_adjustment=round(duration_adj, 2),
        gross_premium=round(gross_premium, 2),
        commission=round(commission, 2),
        net_premium=round(net_premium, 2),
        rate_per_mille=round(rate_per_mille, 4),
    )
