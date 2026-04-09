"""
Lookup APIs — enrollee search, diagnosis list, drug tariff.

Endpoints:
  GET /lookup/enrollee?enrollee_id=    — search enrollee by CIF
  GET /lookup/diagnoses                — pharmacy diagnosis list from Prognosis
  GET /lookup/drugs?q=&page=&pageSize= — drug tariff from WellaHealth
"""

import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_provider
from app.services.prognosis_client import _get_prognosis_token
from app.services.wellahealth_client import wellahealth_client

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Lookups"])

_TIMEOUT = httpx.Timeout(15.0)


# ── Enrollee Lookup ──────────────────────────────────────────────

@router.get("/lookup/enrollee")
async def lookup_enrollee(
    enrollee_id: str = Query(..., min_length=1),
    _provider=Depends(get_current_provider),
):
    """
    Look up an enrollee by CIF number from Prognosis.
    Returns enrollee name and details if found.
    """
    base_url = settings.PROGNOSIS_BASE_URL.rstrip("/")
    if not base_url:
        raise HTTPException(503, "Prognosis API not configured")

    token = await _get_prognosis_token()
    if not token:
        raise HTTPException(503, "Cannot authenticate with Prognosis")

    # Try the enrollee validation endpoint
    url = f"{base_url}/api/ProviderNetwork/ValidateEnrolleeProviderAccessList"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"cifno": enrollee_id, "providerid": _provider.prognosis_provider_id}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            resp = await client.get(url, params=params, headers=headers)

        if resp.status_code == 200:
            data = resp.json()
            # Extract enrollee info from response
            if isinstance(data, list) and len(data) > 0:
                rec = data[0]
            elif isinstance(data, dict):
                rec = data
            else:
                raise HTTPException(404, "Enrollee not found")

            return {
                "found": True,
                "enrollee_id": enrollee_id,
                "name": (
                    rec.get("MemberName") or rec.get("memberName") or
                    rec.get("Name") or rec.get("name") or
                    rec.get("Surname", "") + " " + rec.get("Firstname", "")
                ).strip(),
                "gender": rec.get("Gender") or rec.get("gender"),
                "dob": rec.get("DateOfBirth") or rec.get("dob"),
                "plan": rec.get("PlanName") or rec.get("planName"),
                "status": rec.get("Status") or rec.get("status"),
                "raw": rec,
            }
        elif resp.status_code == 404:
            raise HTTPException(404, "Enrollee not found")
        else:
            logger.warning("Enrollee lookup failed: %d %s", resp.status_code, resp.text[:200])
            raise HTTPException(resp.status_code, "Enrollee lookup failed")

    except httpx.RequestError as e:
        logger.error("Enrollee lookup error: %s", e)
        raise HTTPException(503, f"Cannot reach Prognosis: {e}")


# ── Diagnosis List ───────────────────────────────────────────────

_diagnosis_cache: list | None = None


@router.get("/lookup/diagnoses")
async def get_diagnosis_list(
    _provider=Depends(get_current_provider),
):
    """
    Get pharmacy diagnosis list from Prognosis.
    Cached after first call.
    """
    global _diagnosis_cache
    if _diagnosis_cache is not None:
        return {"diagnoses": _diagnosis_cache}

    base_url = settings.PROGNOSIS_BASE_URL.rstrip("/")
    if not base_url:
        return {"diagnoses": []}

    token = await _get_prognosis_token()
    if not token:
        return {"diagnoses": []}

    url = f"{base_url}/api/ListValues/GetPharmacyDiagnosisList"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            resp = await client.get(url, headers=headers)

        if resp.status_code == 200:
            data = resp.json()
            # Handle various response shapes
            if isinstance(data, list):
                _diagnosis_cache = data
            elif isinstance(data, dict):
                _diagnosis_cache = data.get("data") or data.get("result") or data.get("diagnoses") or []
            else:
                _diagnosis_cache = []

            logger.info("Loaded %d diagnoses from Prognosis", len(_diagnosis_cache))
            return {"diagnoses": _diagnosis_cache}
        else:
            logger.warning("Diagnosis list failed: %d", resp.status_code)
            return {"diagnoses": []}

    except httpx.RequestError as e:
        logger.error("Diagnosis list error: %s", e)
        return {"diagnoses": []}


# ── Drug Tariff (WellaHealth) ────────────────────────────────────

@router.get("/lookup/drugs")
async def search_drug_tariff(
    q: str = Query("", description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _provider=Depends(get_current_provider),
):
    """
    Search WellaHealth drug tariff.
    Returns drug names and prices from WellaHealth's formulary.
    """
    drugs = await wellahealth_client.get_drug_list(page=page, page_size=page_size)

    # Filter by search query if provided
    if q:
        q_lower = q.lower()
        drugs = [d for d in drugs if q_lower in d.name.lower()]

    return {
        "drugs": [
            {
                "id": d.external_id,
                "name": d.name,
                "generic_name": d.generic_name,
                "price": d.price,
                "in_stock": d.in_stock,
            }
            for d in drugs
        ],
        "total": len(drugs),
        "query": q,
    }
