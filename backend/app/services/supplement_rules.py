"""
Supplement Validation Rules — plan-based eligibility checks for supplements.

Some member plans allow medically necessary supplements. This module checks
whether a given supplement is allowed for a member's plan.
"""

import logging
import re

logger = logging.getLogger(__name__)

# Plans that allow medically necessary supplements (matched against Member_Plan field)
SUPPLEMENT_ALLOWED_PLAN_KEYWORDS = [
    "MTN", "MAX", "FIRSTBANK", "FIRST BANK", "NUPRC", "SHELF DRILL",
    "ATIAT", "TOTAL", "VFD", "ANCHORIA", "HEREL", "ARTSPLIT",
    "SHQ LEGAL", "AISL", "ASFALIZO", "TPA", "MAGNUM", "PROMAX",
    "BLACKCARD",
]

# Supplements that are always blocked regardless of plan
EXCLUDED_SUPPLEMENTS = [
    "WELL WOMAN",
    "WELLMAN",
    "RELOAD",
    "EVENING PRIMROSE",
]

# FirstBank-specific Pregnacare rules
FIRSTBANK_BLOCKED_PREGNACARE = [
    "PREGNACARE PLUS",
    "PREGNACARE MAX",
]

FIRSTBANK_ALLOWED_PREGNACARE = [
    "PREGNACARE ORIGINAL",
]


def _is_firstbank_plan(plan_upper: str) -> bool:
    """Check if the plan is a FirstBank plan."""
    return "FIRSTBANK" in plan_upper or "FIRST BANK" in plan_upper


def _plan_allows_supplements(plan_upper: str) -> bool:
    """Check if the member plan allows medically necessary supplements."""
    for keyword in SUPPLEMENT_ALLOWED_PLAN_KEYWORDS:
        if keyword in plan_upper:
            return True
    return False


def _is_excluded_supplement(drug_upper: str) -> bool:
    """Check if the drug is in the always-excluded supplements list."""
    for excluded in EXCLUDED_SUPPLEMENTS:
        if excluded in drug_upper:
            return True
    return False


def _is_supplement(drug_upper: str) -> bool:
    """
    Heuristic to detect if a drug is a supplement.

    Matches common supplement names and patterns.
    """
    supplement_indicators = [
        "WELL WOMAN", "WELLMAN", "RELOAD", "EVENING PRIMROSE",
        "PREGNACARE", "VITAMIN", "MULTIVITAMIN", "FOLIC ACID",
        "IRON SUPPLEMENT", "CALCIUM SUPPLEMENT", "OMEGA",
        "SUPPLEMENT", "PRENATAL", "POSTNATAL",
    ]
    for indicator in supplement_indicators:
        if indicator in drug_upper:
            return True
    return False


def check_supplement_eligibility(member_plan: str, drug_name: str) -> dict:
    """
    Check whether a supplement is allowed for the given member plan.

    Args:
        member_plan: The Member_Plan field from the enrollee profile.
        drug_name: The name of the drug/supplement being prescribed.

    Returns:
        dict with keys:
            - allowed (bool): Whether the supplement is permitted.
            - reason (str): Explanation of the decision.
    """
    plan_upper = (member_plan or "").upper().strip()
    drug_upper = (drug_name or "").upper().strip()

    # If the drug is not a supplement, it's allowed (not our concern)
    if not _is_supplement(drug_upper):
        return {"allowed": True, "reason": "Not a supplement — no restriction applies."}

    # Always-excluded supplements are blocked regardless of plan
    if _is_excluded_supplement(drug_upper):
        return {
            "allowed": False,
            "reason": f"'{drug_name}' is an excluded supplement and is not covered under any plan.",
        }

    # FirstBank-specific Pregnacare rules
    if _is_firstbank_plan(plan_upper):
        for blocked in FIRSTBANK_BLOCKED_PREGNACARE:
            if blocked in drug_upper:
                return {
                    "allowed": False,
                    "reason": f"'{drug_name}' is not covered under FirstBank plans. Only Pregnacare Original is allowed.",
                }
        for allowed in FIRSTBANK_ALLOWED_PREGNACARE:
            if allowed in drug_upper:
                return {
                    "allowed": True,
                    "reason": f"'{drug_name}' is allowed under FirstBank plans.",
                }

    # Check if the plan allows supplements at all
    if _plan_allows_supplements(plan_upper):
        return {
            "allowed": True,
            "reason": f"'{drug_name}' is allowed — plan '{member_plan}' covers medically necessary supplements.",
        }

    # Plan does not allow supplements
    return {
        "allowed": False,
        "reason": f"'{drug_name}' is a supplement and plan '{member_plan}' does not cover supplements.",
    }
