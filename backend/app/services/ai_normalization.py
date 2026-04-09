"""
AI Drug Normalization Service — hybrid rules + AI for drug name resolution.

Uses a layered approach:
  1. Exact match against drug_master (confidence 1.0)
  2. Alias match (confidence 0.9)
  3. Fuzzy string matching (confidence 0.6-0.8)
  4. AI/LangChain classification (confidence varies)

Phase 8: fuzzy matching + LangChain mock with integration point.
When LangChain is connected, unmatched drugs get AI classification.

Integration point: TODO: LANGCHAIN_INTEGRATION
"""

import logging
import re
from difflib import SequenceMatcher

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.medication import DrugAlias, DrugMaster, MedicationAuditLog, MedicationRequestItem

logger = logging.getLogger(__name__)


# ── Common drug name normalization rules ─────────────────────────

# Noise words to strip before matching
_NOISE = re.compile(
    r'\b(tabs?|tablets?|caps?|capsules?|syrup|susp|suspension|inj|injection|'
    r'cream|ointment|drops|inhaler|sachets?|amp|ampoule|vial|'
    r'mg|ml|mcg|iu|%|bd|tds|od|qds|prn|stat|x|for|days?|weeks?|months?|'
    r'\d+)\b',
    re.IGNORECASE,
)

_BRAND_SEPARATORS = re.compile(r'[/\-\+\(\)]')


def _normalize_drug_name(raw: str) -> str:
    """Strip dosage, frequency, and noise from a drug name for matching."""
    cleaned = _BRAND_SEPARATORS.sub(' ', raw)
    cleaned = _NOISE.sub('', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip().lower()
    return cleaned


def _similarity(a: str, b: str) -> float:
    """String similarity ratio between 0 and 1."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


# ── Fuzzy matching against drug master ───────────────────────────

def fuzzy_match_drug(
    drug_name: str,
    db: Session,
    threshold: float = 0.65,
) -> dict | None:
    """
    Try fuzzy matching a drug name against the drug master + aliases.

    Returns dict with drug_id, generic_name, category, confidence, source
    or None if no match above threshold.
    """
    normalized = _normalize_drug_name(drug_name)
    if not normalized:
        return None

    best_match = None
    best_score = 0.0

    # Check generic names
    drugs = db.query(DrugMaster).filter(DrugMaster.is_active.is_(True)).all()
    for drug in drugs:
        score = _similarity(normalized, drug.generic_name.lower())
        if score > best_score:
            best_score = score
            best_match = {
                "drug_id": str(drug.drug_id),
                "generic_name": drug.generic_name,
                "category": drug.category,
                "confidence": round(score, 2),
                "source": "fuzzy_generic",
                "requires_review": score < 0.85,
            }

        # Also check brand names
        if drug.common_brand_names:
            for brand in drug.common_brand_names.split(","):
                brand = brand.strip()
                score = _similarity(normalized, brand.lower())
                if score > best_score:
                    best_score = score
                    best_match = {
                        "drug_id": str(drug.drug_id),
                        "generic_name": drug.generic_name,
                        "category": drug.category,
                        "confidence": round(score, 2),
                        "source": "fuzzy_brand",
                        "requires_review": score < 0.85,
                    }

    # Check aliases
    aliases = (
        db.query(DrugAlias)
        .join(DrugMaster)
        .filter(DrugMaster.is_active.is_(True))
        .all()
    )
    for alias in aliases:
        score = _similarity(normalized, alias.alias_name.lower())
        if score > best_score:
            best_score = score
            drug = alias.drug
            best_match = {
                "drug_id": str(drug.drug_id),
                "generic_name": drug.generic_name,
                "category": drug.category,
                "confidence": round(score, 2),
                "source": "fuzzy_alias",
                "requires_review": score < 0.85,
            }

    if best_score >= threshold:
        return best_match
    return None


# ── AI Classification (LangChain mock) ──────────────────────────

async def ai_classify_drug(drug_name: str) -> dict | None:
    """
    Use AI/LangChain to classify an unrecognized drug.

    TODO: LANGCHAIN_INTEGRATION
    When connected, this will:
    1. Send drug name to LangChain agent
    2. Agent uses tool calling to:
       - Normalize drug name (strip dosage/frequency)
       - Map brand name to generic
       - Classify as acute/chronic/either
    3. Return classification with confidence score

    Inputs: raw drug name string
    Outputs: { generic_name, category, confidence, reasoning }
    Confidence handling: < 0.7 → flag for review
    Fallback: if AI fails, return None (item stays unknown)
    Manual review trigger: all AI classifications with confidence < 0.7
    """
    # TODO: LANGCHAIN_INTEGRATION — Replace mock with live LangChain agent
    #
    # from langchain.chat_models import ChatOpenAI
    # from langchain.agents import create_tool_calling_agent
    #
    # llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    # prompt = f"""
    # You are a pharmaceutical classification assistant.
    # Given a drug name (possibly a brand name, abbreviation, or misspelling),
    # determine:
    # 1. The correct generic name
    # 2. Whether it is "acute" (short-term treatment like antibiotics, antimalarials)
    #    or "chronic" (long-term treatment like antihypertensives, diabetes meds)
    #    or "either" (can be used for both)
    # 3. Your confidence level (0.0 to 1.0)
    #
    # Drug name: {drug_name}
    #
    # Respond in JSON: {{"generic_name": "...", "category": "acute|chronic|either", "confidence": 0.X, "reasoning": "..."}}
    # """
    # response = await llm.ainvoke(prompt)
    # return parse_response(response)

    logger.info("AI classification requested for '%s' — mock mode", drug_name)
    return None  # Mock returns None; classification_service handles fallback


# ── Main normalization entry point ───────────────────────────────

def normalize_and_classify_item(
    item: MedicationRequestItem,
    db: Session,
) -> dict:
    """
    Full normalization pipeline for a single medication item.

    1. Try exact/alias match (already done by classification_service)
    2. Try fuzzy match
    3. Try AI classification (future)
    4. Return best result

    Returns dict with: category, confidence, source, generic_name, drug_id, requires_review
    """
    # Skip if already confidently classified
    if item.matched_drug_id and item.classification_confidence and item.classification_confidence >= 0.9:
        return {
            "category": item.item_category,
            "confidence": item.classification_confidence,
            "source": item.classification_source,
            "generic_name": item.generic_name,
            "drug_id": str(item.matched_drug_id),
            "requires_review": item.requires_review,
            "changed": False,
        }

    # Try fuzzy match
    fuzzy = fuzzy_match_drug(item.drug_name, db)
    if fuzzy:
        logger.info(
            "Fuzzy match for '%s' → %s (%s, confidence %.2f)",
            item.drug_name, fuzzy["generic_name"], fuzzy["category"], fuzzy["confidence"],
        )
        return {**fuzzy, "changed": True}

    # TODO: LANGCHAIN_INTEGRATION — Try AI classification here
    # ai_result = await ai_classify_drug(item.drug_name)
    # if ai_result:
    #     return {**ai_result, "source": "ai", "changed": True}

    # No match found
    return {
        "category": "unknown",
        "confidence": 0.0,
        "source": "unknown",
        "generic_name": None,
        "drug_id": None,
        "requires_review": True,
        "changed": False,
    }


def run_ai_normalization(
    request_id: str,
    db: Session,
    actor: str = "system",
) -> int:
    """
    Run AI normalization on all items in a request.
    Returns count of items that were updated.
    """
    items = (
        db.query(MedicationRequestItem)
        .filter(MedicationRequestItem.request_id == request_id)
        .all()
    )

    updated = 0
    for item in items:
        result = normalize_and_classify_item(item, db)
        if result.get("changed"):
            item.item_category = result["category"]
            item.classification_confidence = result["confidence"]
            item.classification_source = result["source"]
            item.requires_review = result.get("requires_review", True)
            if result.get("generic_name"):
                item.generic_name = result["generic_name"]
            if result.get("drug_id"):
                item.matched_drug_id = result["drug_id"]
            updated += 1

    if updated > 0:
        db.add(MedicationAuditLog(
            event_type="ai_normalization_completed",
            request_id=request_id,
            actor=actor,
            detail=f"AI normalization updated {updated}/{len(items)} items",
        ))
        db.flush()

    logger.info("AI normalization: request=%s, updated=%d/%d", request_id, updated, len(items))
    return updated
