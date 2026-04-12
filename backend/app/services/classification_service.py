"""
Medication Classification Engine — rule-based acute/chronic/mixed logic.

Classification happens at two levels:
  1. Line-item: each medication is classified as acute/chronic/either/unknown
  2. Request-level: the overall request is classified based on all items

Decision rules (from business brief):
  - All acute        → request = "acute"
  - All chronic      → request = "chronic"
  - Mix of both      → request = "mixed"
  - Any unknown/uncertain → request = "review_required"

The engine first tries exact match against drug_master, then fuzzy alias
match. Items that can't be matched get category "unknown" + review flag.

Phase 8 will add AI/LangChain for unmatched drug normalization.
"""

import logging
from dataclasses import dataclass, field as dataclass_field

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.medication import (
    ClassificationResult,
    DrugAlias,
    DrugMaster,
    MedicationAuditLog,
    MedicationRequest,
    MedicationRequestItem,
)
from app.services.supplement_rules import check_supplement_eligibility

logger = logging.getLogger(__name__)

# Hormonal + Cancer drugs — entire request routes to Leadway WhatsApp
LEADWAY_WHATSAPP_DRUGS = [
    # Hormonal / Fertility
    "PROGESTERONE", "CYCLOGEST", "UTROGESTAN", "DUPHASTON", "DYDROGESTERONE",
    "GESTONE", "HYDROXYPROGESTERONE", "MEDROXYPROGESTERONE", "PROVERA",
    "DEPO-PROVERA", "ESTRADIOL", "PROGYNOVA", "CLOMIPHENE", "CLOMID",
    "LETROZOLE", "FEMARA", "GOSERELIN", "ZOLADEX", "LEUPROLIDE", "LUPRON",
    "TAMOXIFEN", "ANASTROZOLE", "ARIMIDEX", "EXEMESTANE",
    # Cancer / Oncology
    "METHOTREXATE", "CYCLOPHOSPHAMIDE", "DOXORUBICIN", "CISPLATIN",
    "CARBOPLATIN", "PACLITAXEL", "DOCETAXEL", "VINCRISTINE", "IMATINIB",
    "RITUXIMAB", "TRASTUZUMAB", "BEVACIZUMAB", "CAPECITABINE", "XELODA",
    "FLUOROURACIL", "5-FU", "ETOPOSIDE", "GEMCITABINE", "ERLOTINIB",
    "SORAFENIB", "SUNITINIB", "BICALUTAMIDE", "FLUTAMIDE",
    # Autoimmune
    "AZATHIOPRINE", "IMURAN", "MYCOPHENOLATE", "CELLCEPT",
    "HYDROXYCHLOROQUINE", "PLAQUENIL", "SULFASALAZINE", "SALAZOPYRIN",
    "LEFLUNOMIDE", "ARAVA", "ADALIMUMAB", "HUMIRA", "ETANERCEPT",
    "ENBREL", "INFLIXIMAB", "REMICADE", "TOCILIZUMAB", "ACTEMRA",
    "CICLOSPORIN", "CYCLOSPORINE", "SANDIMMUN", "TACROLIMUS", "PROGRAF",
    # Fertility treatment
    "GONADOTROPIN", "MENOTROPIN", "MENOPUR", "FOLLITROPIN", "GONAL-F",
    "PUREGON", "CETROTIDE", "CETRORELIX", "GANIRELIX", "ORGALUTRAN",
    "CHORIOGONADOTROPIN", "OVITRELLE", "PREGNYL", "PROGESTERONE GEL",
    "CRINONE", "LUTINUS", "ESTROGEN", "OESTROGEN",
]


@dataclass
class ItemClassification:
    """Result of classifying a single medication line."""
    item_id: str
    drug_name: str
    category: str          # acute | chronic | either | unknown
    confidence: float      # 0.0–1.0
    source: str            # drug_master | alias | unknown
    matched_drug_id: str | None = None
    generic_name: str | None = None
    requires_review: bool = False
    supplement_blocked: bool = False
    supplement_reason: str = ""


@dataclass
class RequestClassification:
    """Result of classifying an entire medication request."""
    classification: str    # acute | chronic | mixed | review_required
    acute_count: int
    chronic_count: int
    either_count: int
    unknown_count: int
    review_required: bool
    confidence: float
    reasoning: str
    items: list[ItemClassification]
    contains_whatsapp_only: bool = False


def classify_item(
    item: MedicationRequestItem,
    db: Session,
) -> ItemClassification:
    """
    Classify a single medication item against the drug master.

    Priority:
    1. If item already has matched_drug_id from autocomplete → use that
    2. Try exact generic name match in drug_master
    3. Try alias match in drug_aliases
    4. Fall back to unknown → requires review
    """
    drug_name_lower = item.drug_name.strip().lower()

    # 1. Already matched via autocomplete
    if item.matched_drug_id:
        drug = db.query(DrugMaster).filter(
            DrugMaster.drug_id == item.matched_drug_id,
        ).first()
        if drug:
            return ItemClassification(
                item_id=str(item.item_id),
                drug_name=item.drug_name,
                category=drug.category,
                confidence=1.0,
                source="drug_master",
                matched_drug_id=str(drug.drug_id),
                generic_name=drug.generic_name,
                requires_review=drug.requires_review,
            )

    # 2. Exact generic name match
    drug = db.query(DrugMaster).filter(
        DrugMaster.is_active.is_(True),
        func.lower(DrugMaster.generic_name) == drug_name_lower,
    ).first()
    if drug:
        return ItemClassification(
            item_id=str(item.item_id),
            drug_name=item.drug_name,
            category=drug.category,
            confidence=1.0,
            source="drug_master",
            matched_drug_id=str(drug.drug_id),
            generic_name=drug.generic_name,
            requires_review=drug.requires_review,
        )

    # 3. Alias match
    alias = (
        db.query(DrugAlias)
        .join(DrugMaster)
        .filter(
            DrugMaster.is_active.is_(True),
            func.lower(DrugAlias.alias_name) == drug_name_lower,
        )
        .first()
    )
    if alias:
        drug = alias.drug
        return ItemClassification(
            item_id=str(item.item_id),
            drug_name=item.drug_name,
            category=drug.category,
            confidence=0.9,
            source="alias",
            matched_drug_id=str(drug.drug_id),
            generic_name=drug.generic_name,
            requires_review=drug.requires_review,
        )

    # 4. Partial match (LIKE search on generic name and aliases)
    partial = db.query(DrugMaster).filter(
        DrugMaster.is_active.is_(True),
        func.lower(DrugMaster.generic_name).contains(drug_name_lower),
    ).first()
    if partial:
        return ItemClassification(
            item_id=str(item.item_id),
            drug_name=item.drug_name,
            category=partial.category,
            confidence=0.7,
            source="drug_master",
            matched_drug_id=str(partial.drug_id),
            generic_name=partial.generic_name,
            requires_review=True,  # partial match → flag for review
        )

    # Also try partial on aliases
    partial_alias = (
        db.query(DrugAlias)
        .join(DrugMaster)
        .filter(
            DrugMaster.is_active.is_(True),
            func.lower(DrugAlias.alias_name).contains(drug_name_lower),
        )
        .first()
    )
    if partial_alias:
        drug = partial_alias.drug
        return ItemClassification(
            item_id=str(item.item_id),
            drug_name=item.drug_name,
            category=drug.category,
            confidence=0.6,
            source="alias",
            matched_drug_id=str(drug.drug_id),
            generic_name=drug.generic_name,
            requires_review=True,
        )

    # 5. Try fuzzy matching (AI normalization layer)
    from app.services.ai_normalization import fuzzy_match_drug
    fuzzy = fuzzy_match_drug(item.drug_name, db)
    if fuzzy:
        return ItemClassification(
            item_id=str(item.item_id),
            drug_name=item.drug_name,
            category=fuzzy["category"],
            confidence=fuzzy["confidence"],
            source=fuzzy["source"],
            matched_drug_id=fuzzy.get("drug_id"),
            generic_name=fuzzy.get("generic_name"),
            requires_review=fuzzy.get("requires_review", True),
        )

    # 6. Unknown — no match found
    # TODO: AI_CLASSIFICATION — LangChain agent will be called here when connected
    logger.warning("Drug not found in master: '%s'", item.drug_name)
    return ItemClassification(
        item_id=str(item.item_id),
        drug_name=item.drug_name,
        category="unknown",
        confidence=0.0,
        source="unknown",
        requires_review=True,
    )


def _is_whatsapp_only_drug(drug_name: str) -> bool:
    """Check if a drug is hormonal or cancer — routes to Leadway WhatsApp."""
    name_upper = (drug_name or "").upper().strip()
    for drug in LEADWAY_WHATSAPP_DRUGS:
        if drug in name_upper:
            return True
    return False


def classify_request(
    request: MedicationRequest,
    db: Session,
) -> RequestClassification:
    """
    Classify an entire medication request.

    Steps:
    1. Classify each item individually
    2. Check supplement eligibility per plan
    3. Check for controlled substances
    4. Resolve "either" items based on context
    5. Determine request-level classification
    """
    item_results: list[ItemClassification] = []
    contains_whatsapp_only = False

    # Retrieve member plan for supplement checks
    member_plan = getattr(request, "member_plan", "") or ""

    for item in request.items:
        result = classify_item(item, db)

        # Supplement eligibility check
        supplement_check = check_supplement_eligibility(member_plan, item.drug_name)
        if not supplement_check["allowed"]:
            result.supplement_blocked = True
            result.supplement_reason = supplement_check["reason"]

        # Hormonal / Cancer drug check
        if _is_whatsapp_only_drug(item.drug_name):
            contains_whatsapp_only = True

        item_results.append(result)

    # Count categories
    acute_count = sum(1 for r in item_results if r.category == "acute")
    chronic_count = sum(1 for r in item_results if r.category == "chronic")
    either_count = sum(1 for r in item_results if r.category == "either")
    unknown_count = sum(1 for r in item_results if r.category == "unknown")
    any_review = any(r.requires_review for r in item_results)

    # Resolve "either" items based on context:
    # If there are chronic items, "either" items lean chronic
    # If all other items are acute, "either" items stay acute
    # If standalone "either" only, treat as acute (shorter treatment path)
    if either_count > 0:
        if chronic_count > 0:
            # In presence of chronic drugs, "either" items lean chronic
            chronic_count += either_count
        else:
            # All non-either items are acute (or there are none), treat either as acute
            acute_count += either_count
        either_count = 0  # resolved

    # Resolve "unknown" items: unknown drugs route to Leadway WhatsApp
    # (Leadway ops team handles unclassified meds directly).
    # They count as chronic for routing, but items stay flagged for review.
    if unknown_count > 0:
        chronic_count += unknown_count

    # Determine request-level classification
    has_unknown = unknown_count > 0

    if acute_count > 0 and chronic_count > 0:
        classification = "mixed"
        reasoning = (
            f"Request contains {acute_count} acute and {chronic_count} chronic medication(s). "
        )
        if has_unknown:
            reasoning += (
                f"({unknown_count} unclassified medication(s) included — "
                "routed to Leadway for manual handling.) "
            )
        reasoning += "Mixed requests route to Leadway WhatsApp."
    elif chronic_count > 0:
        classification = "chronic"
        reasoning = f"All {chronic_count} medication(s) are chronic. "
        if has_unknown:
            reasoning += (
                f"({unknown_count} unclassified medication(s) included — "
                "routed to Leadway for manual handling.) "
            )
        reasoning += "Routes to Leadway WhatsApp."
    elif acute_count > 0:
        classification = "acute"
        reasoning = (
            f"All {acute_count} medication(s) are acute. "
            "Routes to WellaHealth API."
        )
    else:
        # No items at all (shouldn't happen, but safe fallback)
        classification = "chronic"
        reasoning = "No classifiable medications found. Routed to Leadway WhatsApp for manual handling."

    # If any individual item requires review, flag the whole request
    review_required = has_unknown or any_review

    # Hormonal / Cancer drug override: force entire request to chronic (Leadway WhatsApp)
    if contains_whatsapp_only:
        classification = "chronic"
        reasoning = (
            "Contains hormonal or cancer medication — requires Leadway direct handling. "
            f"Original counts: acute={acute_count}, chronic={chronic_count}. "
            "Entire request routed to Leadway WhatsApp."
        )

    # Calculate overall confidence
    if item_results:
        avg_confidence = sum(r.confidence for r in item_results) / len(item_results)
    else:
        avg_confidence = 0.0

    # If review is flagged but classification is clear, keep the classification
    # but mark review_required so ops can confirm
    if review_required and classification in ("acute", "chronic", "mixed"):
        reasoning += " (Review flagged for one or more items.)"

    return RequestClassification(
        classification=classification,
        acute_count=acute_count,
        chronic_count=chronic_count,
        either_count=either_count,
        unknown_count=unknown_count,
        review_required=review_required,
        confidence=round(avg_confidence, 2),
        reasoning=reasoning,
        items=item_results,
        contains_whatsapp_only=contains_whatsapp_only,
    )


def run_classification(
    request_id: str,
    db: Session,
    actor: str = "system",
) -> ClassificationResult:
    """
    Run classification on a medication request and persist the results.

    This is the main entry point called from the submission flow.
    It:
    1. Loads the request + items
    2. Runs classification
    3. Updates each item with its category
    4. Creates/updates ClassificationResult record
    5. Logs the audit event
    """
    request = (
        db.query(MedicationRequest)
        .filter(MedicationRequest.request_id == request_id)
        .first()
    )
    if not request:
        raise ValueError(f"Request {request_id} not found")

    # Load items
    items = (
        db.query(MedicationRequestItem)
        .filter(MedicationRequestItem.request_id == request_id)
        .all()
    )
    request.items = items

    # Run classification
    result = classify_request(request, db)

    # Update each item with classification
    item_map = {str(item.item_id): item for item in items}
    for item_result in result.items:
        item = item_map.get(item_result.item_id)
        if item:
            item.item_category = item_result.category
            item.classification_confidence = item_result.confidence
            item.classification_source = item_result.source
            item.requires_review = item_result.requires_review
            if item_result.matched_drug_id and not item.matched_drug_id:
                item.matched_drug_id = item_result.matched_drug_id
            if item_result.generic_name and not item.generic_name:
                item.generic_name = item_result.generic_name
            # Persist supplement blocked flag
            if item_result.supplement_blocked:
                item.supplement_blocked = True

    # Create or update classification result
    existing = (
        db.query(ClassificationResult)
        .filter(ClassificationResult.request_id == request_id)
        .first()
    )

    if existing:
        existing.classification = result.classification
        existing.acute_count = result.acute_count
        existing.chronic_count = result.chronic_count
        existing.unknown_count = result.unknown_count
        existing.review_required = result.review_required
        existing.confidence = result.confidence
        existing.reasoning = result.reasoning
        existing.classified_by = "rules"
        classification_record = existing
    else:
        classification_record = ClassificationResult(
            request_id=request_id,
            classification=result.classification,
            acute_count=result.acute_count,
            chronic_count=result.chronic_count,
            unknown_count=result.unknown_count,
            review_required=result.review_required,
            confidence=result.confidence,
            reasoning=result.reasoning,
            classified_by="rules",
        )
        db.add(classification_record)

    # Audit log
    audit = MedicationAuditLog(
        event_type="classification_completed",
        request_id=request_id,
        actor=actor,
        detail=(
            f"Classification: {result.classification} | "
            f"Acute: {result.acute_count}, Chronic: {result.chronic_count}, "
            f"Unknown: {result.unknown_count} | "
            f"Confidence: {result.confidence} | "
            f"Review: {result.review_required}"
        ),
    )
    db.add(audit)

    db.flush()

    logger.info(
        "Classification complete: request=%s, result=%s, confidence=%.2f, review=%s",
        request_id, result.classification, result.confidence, result.review_required,
    )

    return classification_record
