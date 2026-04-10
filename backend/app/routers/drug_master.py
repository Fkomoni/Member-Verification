"""
Drug Master API — search, list, and manage the medication reference table.

Endpoints:
  GET  /drugs              — paginated list of all drugs
  GET  /drugs/search       — search drugs by name (generic or alias)
  GET  /drugs/{drug_id}    — get a single drug by ID
  POST /drugs/seed         — seed the drug master (admin, idempotent)
  GET  /locations/states   — list Nigerian states
  GET  /locations/lgas     — list LGAs for a state
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_provider
from app.models.medication import DrugAlias, DrugMaster
from app.schemas.medication import (
    DrugMasterListOut,
    DrugMasterOut,
    DrugSearchResponse,
    DrugSearchResult,
    LgaListOut,
    LocationListOut,
    StateOut,
)
from app.services.drug_master_seed import get_seed_drugs
from app.utils.nigerian_locations import get_lgas, get_states

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Drug Master"])


# ── List Drugs (paginated) ───────────────────────────────────────

@router.get("/drugs", response_model=DrugMasterListOut)
def list_drugs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    category: str | None = Query(None, description="Filter: acute, chronic, either, unknown"),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    _provider=Depends(get_current_provider),
):
    """Return a paginated list of drugs from the master table."""
    query = db.query(DrugMaster)

    if active_only:
        query = query.filter(DrugMaster.is_active.is_(True))
    if category:
        query = query.filter(DrugMaster.category == category)

    total = query.count()
    drugs = (
        query
        .options(joinedload(DrugMaster.aliases))
        .order_by(DrugMaster.generic_name)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return DrugMasterListOut(
        total=total,
        page=page,
        per_page=per_page,
        drugs=[DrugMasterOut.model_validate(d) for d in drugs],
    )


# ── Search Drugs ─────────────────────────────────────────────────

@router.get("/drugs/search", response_model=DrugSearchResponse)
def search_drugs(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    _provider=Depends(get_current_provider),
):
    """
    Search drugs by generic name or alias.
    Used for autocomplete in the medication request form.
    """
    search_term = f"%{q.strip().lower()}%"

    # Search generic names
    generic_matches = (
        db.query(DrugMaster)
        .filter(
            DrugMaster.is_active.is_(True),
            func.lower(DrugMaster.generic_name).like(search_term),
        )
        .limit(limit)
        .all()
    )

    results: list[DrugSearchResult] = []
    seen_ids: set[uuid.UUID] = set()

    for drug in generic_matches:
        seen_ids.add(drug.drug_id)
        results.append(DrugSearchResult(
            drug_id=drug.drug_id,
            generic_name=drug.generic_name,
            category=drug.category,
            common_brand_names=drug.common_brand_names,
            therapeutic_class=drug.therapeutic_class,
            requires_review=drug.requires_review,
            match_type="generic",
        ))

    # Search aliases
    alias_matches = (
        db.query(DrugAlias)
        .join(DrugMaster)
        .filter(
            DrugMaster.is_active.is_(True),
            func.lower(DrugAlias.alias_name).like(search_term),
        )
        .options(joinedload(DrugAlias.drug))
        .limit(limit)
        .all()
    )

    for alias in alias_matches:
        if alias.drug_id not in seen_ids:
            seen_ids.add(alias.drug_id)
            drug = alias.drug
            results.append(DrugSearchResult(
                drug_id=drug.drug_id,
                generic_name=drug.generic_name,
                category=drug.category,
                common_brand_names=drug.common_brand_names,
                therapeutic_class=drug.therapeutic_class,
                requires_review=drug.requires_review,
                match_type="alias",
            ))

    # Search brand names field
    if len(results) < limit:
        brand_matches = (
            db.query(DrugMaster)
            .filter(
                DrugMaster.is_active.is_(True),
                DrugMaster.common_brand_names.isnot(None),
                func.lower(DrugMaster.common_brand_names).like(search_term),
            )
            .limit(limit - len(results))
            .all()
        )
        for drug in brand_matches:
            if drug.drug_id not in seen_ids:
                seen_ids.add(drug.drug_id)
                results.append(DrugSearchResult(
                    drug_id=drug.drug_id,
                    generic_name=drug.generic_name,
                    category=drug.category,
                    common_brand_names=drug.common_brand_names,
                    therapeutic_class=drug.therapeutic_class,
                    requires_review=drug.requires_review,
                    match_type="brand",
                ))

    return DrugSearchResponse(query=q, results=results[:limit], total=len(results))


# ── Get Single Drug ──────────────────────────────────────────────

@router.get("/drugs/{drug_id}", response_model=DrugMasterOut)
def get_drug(
    drug_id: uuid.UUID,
    db: Session = Depends(get_db),
    _provider=Depends(get_current_provider),
):
    """Return a single drug with its aliases."""
    drug = (
        db.query(DrugMaster)
        .options(joinedload(DrugMaster.aliases))
        .filter(DrugMaster.drug_id == drug_id)
        .first()
    )
    if not drug:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drug not found",
        )
    return DrugMasterOut.model_validate(drug)


# ── Seed Drug Master (idempotent) ────────────────────────────────

@router.post("/drugs/seed", status_code=status.HTTP_200_OK)
def seed_drug_master(
    db: Session = Depends(get_db),
):
    """
    Seed the drug master table with common medications.
    Idempotent: skips drugs that already exist (by generic_name).
    """
    seed_data = get_seed_drugs()
    created = 0
    skipped = 0

    for entry in seed_data:
        existing = (
            db.query(DrugMaster)
            .filter(func.lower(DrugMaster.generic_name) == entry["generic_name"].lower())
            .first()
        )
        if existing:
            skipped += 1
            continue

        drug = DrugMaster(
            generic_name=entry["generic_name"],
            category=entry["category"],
            common_brand_names=entry.get("common_brand_names"),
            therapeutic_class=entry.get("therapeutic_class"),
            requires_review=entry.get("requires_review", False),
            source="seed",
        )
        db.add(drug)
        db.flush()  # Get the drug_id for alias creation

        # Create aliases
        for alias_name in entry.get("aliases", []):
            alias = DrugAlias(
                drug_id=drug.drug_id,
                alias_name=alias_name,
                alias_type="brand",
            )
            db.add(alias)

        created += 1

    db.commit()
    logger.info("Drug master seed: created=%d, skipped=%d", created, skipped)
    return {
        "message": "Drug master seeded",
        "created": created,
        "skipped": skipped,
        "total_in_seed": len(seed_data),
    }


# ── Nigerian Location Endpoints ──────────────────────────────────

@router.get("/locations/states", response_model=LocationListOut)
def list_states(
    _provider=Depends(get_current_provider),
):
    """Return all Nigerian states with is_lagos flag."""
    states_data = get_states()
    return LocationListOut(
        states=[StateOut(**s) for s in states_data],
    )


@router.get("/locations/lgas", response_model=LgaListOut)
def list_lgas(
    state: str = Query(..., description="Nigerian state name"),
    _provider=Depends(get_current_provider),
):
    """Return LGAs for a given Nigerian state."""
    lgas = get_lgas(state)
    return LgaListOut(state=state, lgas=lgas)
