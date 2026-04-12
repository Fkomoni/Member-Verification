"""
WellaHealth Tariff Sync — fetches full drug tariff and stores locally.

Called:
  - On app startup (if table is empty)
  - Via admin endpoint POST /admin/sync-tariff
  - Can be scheduled as a daily cron job

Fetches from: GET /v1/tariff/full?pageIndex=1&pageSize=5000
Stores into: drug_master table with source='wellahealth'
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.medication import DrugAlias, DrugMaster
from app.services.wellahealth_client import wellahealth_client

logger = logging.getLogger(__name__)


async def fetch_full_tariff() -> list[dict]:
    """Fetch all drugs from WellaHealth /v1/tariff/full endpoint."""
    if wellahealth_client._mock_mode:
        logger.info("Tariff sync: WellaHealth in mock mode, skipping")
        return []

    all_drugs = []
    page = 1
    page_size = 1000  # Fetch large pages to minimize requests

    while True:
        data = await wellahealth_client._request(
            "GET", "/tariff/full",
            params={"pageIndex": page, "pageSize": page_size},
        )
        if not data:
            logger.warning("Tariff sync: no response on page %d", page)
            break

        items = data.get("data", []) if isinstance(data, dict) else data
        if not isinstance(items, list) or len(items) == 0:
            logger.info("Tariff sync: no more items on page %d", page)
            break

        all_drugs.extend(items)
        page_count = data.get("pageCount", 1) if isinstance(data, dict) else 1
        logger.info("Tariff sync: page %d/%d, got %d items (total %d)",
                     page, page_count, len(items), len(all_drugs))

        if page >= page_count or len(items) < page_size:
            break
        page += 1

    logger.info("Tariff sync: fetched %d total drugs from WellaHealth", len(all_drugs))
    return all_drugs


def sync_tariff_to_db(tariff_data: list[dict], db: Session) -> dict:
    """
    Upsert WellaHealth tariff data into drug_master.
    Matches on drug_name_display (the full drug name from WellaHealth).
    """
    created = 0
    updated = 0
    skipped = 0

    for item in tariff_data:
        drug_name = (item.get("drugName") or "").strip()
        if not drug_name:
            skipped += 1
            continue

        generic_name = (item.get("genericName") or "").strip()
        brand_name = (item.get("brandName") or "").strip()
        dosage_form = (item.get("dosageForm") or "").strip()
        strength = (item.get("strength") or "").strip()
        drug_class = (item.get("drugClass") or "").strip()

        # Extract strength from drug name if not provided
        if not strength:
            import re
            match = re.search(r'(\d+(?:[./]\d+)?(?:mg|mcg|ml|g|iu|%|mg/\d+ml))', drug_name, re.IGNORECASE)
            if match:
                strength = match.group(1).upper()

        # Check if already exists by display name or generic name
        existing = (
            db.query(DrugMaster)
            .filter(
                (func.lower(func.coalesce(DrugMaster.drug_name_display, "")) == drug_name.lower()) |
                (func.lower(DrugMaster.generic_name) == drug_name.lower()) |
                (func.lower(DrugMaster.generic_name) == generic_name.lower() if generic_name else False)
            )
            .first()
        )

        if existing:
            # Update — always set drug_name_display and strength
            existing.drug_name_display = drug_name
            if generic_name:
                existing.generic_name = generic_name
            if brand_name:
                existing.brand_name = brand_name
            if dosage_form:
                existing.dosage_form = dosage_form
            # Always update strength (even overwrite)
            if strength:
                existing.strength = strength
                existing.strength = strength
            if drug_class:
                existing.drug_class = drug_class
            existing.source = "wellahealth"
            existing.updated_at = datetime.now(timezone.utc)
            updated += 1
        else:
            # Create new
            drug = DrugMaster(
                generic_name=generic_name or drug_name,
                drug_name_display=drug_name,
                brand_name=brand_name or None,
                dosage_form=dosage_form or None,
                strength=strength or None,
                drug_class=drug_class or None,
                category="unknown",  # Will be classified later by AI/rules
                source="wellahealth",
                is_active=True,
            )
            db.add(drug)

            # Also create alias for brand name if different
            if brand_name and brand_name.lower() != (generic_name or "").lower():
                db.flush()
                alias = DrugAlias(
                    drug_id=drug.drug_id,
                    alias_name=brand_name,
                    alias_type="brand",
                )
                db.add(alias)

            created += 1

    db.commit()
    logger.info("Tariff sync complete: created=%d, updated=%d, skipped=%d", created, updated, skipped)
    return {"created": created, "updated": updated, "skipped": skipped, "total": len(tariff_data)}


def classify_unknown_drugs_from_seed(db: Session) -> int:
    """
    Cross-reference drugs with category='unknown' against the seed data.
    Match by generic_name (case-insensitive contains).
    Returns the number of drugs classified.
    """
    from app.services.drug_master_seed import SEED_DRUGS

    unknown_drugs = db.query(DrugMaster).filter(DrugMaster.category == "unknown").all()
    if not unknown_drugs:
        return 0

    classified = 0
    for drug in unknown_drugs:
        drug_generic = (drug.generic_name or "").lower()
        drug_display = (drug.drug_name_display or "").lower()

        for seed in SEED_DRUGS:
            seed_generic = seed["generic_name"].lower()
            # Check if seed generic_name is contained in tariff drug's generic_name or display name
            if seed_generic in drug_generic or seed_generic in drug_display:
                drug.category = seed["category"]
                classified += 1
                break

    if classified > 0:
        db.commit()
    logger.info("Seed classification: classified %d/%d unknown drugs", classified, len(unknown_drugs))
    return classified


async def run_tariff_sync(db: Session) -> dict:
    """Full sync: fetch from WellaHealth + store in DB, then classify unknowns."""
    tariff_data = await fetch_full_tariff()
    if not tariff_data:
        return {"message": "No tariff data fetched", "created": 0, "updated": 0}

    result = sync_tariff_to_db(tariff_data, db)

    # Cross-reference unknown drugs against seed data for classification
    classified = classify_unknown_drugs_from_seed(db)
    result["seed_classified"] = classified

    return result
