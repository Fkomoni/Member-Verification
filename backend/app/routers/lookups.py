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
from sqlalchemy import func, or_
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
    Look up an enrollee by CIF number using Prognosis GetEnrolleeBioDataByEnrolleeID.
    """
    base_url = settings.PROGNOSIS_BASE_URL.rstrip("/")
    if not base_url:
        raise HTTPException(503, "Prognosis API not configured")

    token = await _get_prognosis_token()
    if not token:
        raise HTTPException(503, "Cannot authenticate with Prognosis")

    url = f"{base_url}/api/EnrolleeProfile/GetEnrolleeBioDataByEnrolleeID"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"enrolleeid": enrollee_id}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            resp = await client.get(url, params=params, headers=headers)

        if resp.status_code != 200:
            logger.warning("Enrollee lookup HTTP %d: %s", resp.status_code, resp.text[:200])
            raise HTTPException(resp.status_code, "Enrollee lookup failed")

        data = resp.json()
        logger.info("Enrollee lookup raw type=%s keys=%s", type(data).__name__,
                     list(data.keys()) if isinstance(data, dict) else "N/A")

        # Extract record from response
        rec = None
        if isinstance(data, dict):
            # Try {"status": ..., "result": [{...}]}
            for key in ("result", "Result", "data", "Data"):
                nested = data.get(key)
                if isinstance(nested, list) and len(nested) > 0:
                    rec = nested[0]
                    break
                elif isinstance(nested, dict) and nested:
                    rec = nested
                    break
            if rec is None and "Member_Surname" in data:
                rec = data
        elif isinstance(data, list) and len(data) > 0:
            rec = data[0]

        if not rec:
            logger.warning("Enrollee not found or empty response for %s", enrollee_id)
            raise HTTPException(404, "Enrollee not found")

        logger.info("Enrollee record keys: %s", list(rec.keys())[:20])

        # Extract fields using exact Prognosis field names
        surname = str(rec.get("Member_Surname") or "").strip()
        firstname = str(rec.get("Member_Firstname") or rec.get("Member_othernames") or "").strip()
        name = f"{surname} {firstname}".strip() or f"Member {enrollee_id}"

        age = str(rec["Member_Age"]) if rec.get("Member_Age") else None
        gender = str(rec.get("Member_Gender") or "").strip()
        # Map member status code to description
        MEMBER_STATUS_MAP = {
            "1": "Active", 1: "Active",
            "2": "Suspended", 2: "Suspended",
            "3": "Terminated", 3: "Terminated",
            "4": "Expired", 4: "Expired",
            "5": "Inactive", 5: "Inactive",
            "0": "Inactive", 0: "Inactive",
            "6": "Cancelled", 6: "Cancelled",
        }

        raw_status = rec.get("Member_MemberStatus")
        status_desc = rec.get("Member_MemberStatusDescription") or ""
        if not status_desc and raw_status is not None:
            status_desc = MEMBER_STATUS_MAP.get(raw_status, MEMBER_STATUS_MAP.get(str(raw_status), f"Unknown ({raw_status})"))
        if not status_desc:
            status_desc = "Unknown"

        is_active = status_desc.lower() == "active" or str(raw_status) == "1"

        plan = str(rec.get("Product_schemeName") or rec.get("Member_Plan") or rec.get("Member_AccountName") or "").strip()
        phone = str(rec.get("Member_Phone_One") or rec.get("Member_Phone_Two") or "").strip()
        email = str(rec.get("Member_EmailAddress_Two") or rec.get("Member_EmailAddress_One") or "").strip()

        logger.info("Enrollee parsed: name=%s, gender=%s, age=%s, plan=%s, status=%s",
                     name, gender, age, plan, status_desc)

        return {
            "found": True,
            "enrollee_id": enrollee_id,
            "name": name,
            "gender": gender,
            "age": age,
            "dob": rec.get("Member_DateOfBirth"),
            "plan": plan,
            "status": status_desc,
            "status_code": raw_status,
            "is_active": is_active,
            "status_description": status_desc,
            "phone": phone,
            "email": email,
            "company": str(rec.get("Member_AccountName") or "").strip(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Enrollee lookup unexpected error: %s", e, exc_info=True)
        raise HTTPException(500, f"Enrollee lookup error: {str(e)}")


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

# ── Medication Search (local DB — synced from WellaHealth tariff) ─

@router.get("/medications/search")
def search_medications(
    q: str = Query(..., min_length=2, description="Search drug name"),
    limit: int = Query(15, ge=1, le=50),
    db: Session = Depends(get_db),
    _provider=Depends(get_current_provider),
):
    """
    Fast typeahead search against local drug_master (synced from WellaHealth tariff).
    Uses ILIKE for case-insensitive search across drug_name_display, generic_name, brand_name.
    """
    from app.models.medication import DrugMaster
    from sqlalchemy import cast, String, text

    search_term = f"%{q.strip()}%"

    # ILIKE search — works on PostgreSQL.
    # Seed drugs (source='seed') are prioritized because they have accurate
    # acute/chronic classification. WellaHealth tariff drugs default to 'unknown'.
    # Use a subquery with DISTINCT ON to deduplicate across the aliases JOIN,
    # then outer ORDER BY ranks classified drugs first.
    results = db.execute(
        text("""
            SELECT * FROM (
                SELECT DISTINCT ON (dm.drug_id)
                    dm.drug_id,
                    COALESCE(dm.drug_name_display, dm.generic_name) AS display_name,
                    dm.generic_name,
                    dm.brand_name,
                    dm.strength,
                    dm.dosage_form,
                    dm.drug_class,
                    dm.category,
                    dm.common_brand_names
                FROM drug_master dm
                LEFT JOIN drug_aliases da ON da.drug_id = dm.drug_id
                WHERE dm.is_active = true
                  AND (
                    dm.drug_name_display ILIKE :q
                    OR dm.generic_name   ILIKE :q
                    OR dm.brand_name     ILIKE :q
                    OR dm.common_brand_names ILIKE :q
                    OR da.alias_name     ILIKE :q
                  )
                ORDER BY dm.drug_id
            ) sub
            ORDER BY
                CASE WHEN category != 'unknown' THEN 0 ELSE 1 END,
                CASE WHEN display_name IS NOT NULL THEN 0 ELSE 1 END,
                COALESCE(display_name, generic_name)
            LIMIT :lim
        """),
        {"q": search_term, "lim": limit},
    ).fetchall()

    return {
        "results": [
            {
                "drug_id": str(r[0]),
                "drug_name": r[1] or r[2] or "",
                "generic_name": r[2] or "",
                "brand_name": r[3] or "",
                "strength": r[4] or "",
                "dosage_form": r[5] or "",
                "category": r[7] or "unknown",
                # brand_hint lets the frontend show "Artemether/Lumefantrine (Coartem, Lonart)"
                "brand_hint": r[8] or "",
            }
            for r in results
        ],
        "total": len(results),
        "query": q,
    }


# ── Pharmacy Search (WellaHealth) ────────────────────────────────

@router.get("/lookup/pharmacies")
async def search_pharmacies(
    state: str = Query(..., min_length=1),
    lga: str = Query(""),
    area: str = Query(""),
    _provider=Depends(get_current_provider),
):
    """
    Search WellaHealth pharmacies by location.
    If a narrowed LGA search returns no results, automatically retries at
    state level so the provider always sees options when they exist.
    """
    results = await wellahealth_client.search_pharmacies(state, lga, area)
    fallback_used = False

    # LGA search came back empty — retry at state level
    if not results and lga:
        results = await wellahealth_client.search_pharmacies(state, "", area)
        fallback_used = bool(results)
        if fallback_used:
            logger.info(
                "Pharmacy search: LGA '%s' returned no results for state '%s' — showing all state results",
                lga, state,
            )

    return {
        "pharmacies": results,
        "total": len(results),
        "lga_searched": lga if not fallback_used else "",
        "fallback_to_state": fallback_used,
    }


# ── Google Maps Address Validation ───────────────────────────────

@router.get("/lookup/validate-address")
async def validate_address(
    address: str = Query(..., min_length=3),
    state: str = Query("", description="State for context"),
    _provider=Depends(get_current_provider),
):
    """
    Validate an address using Google Maps Geocoding API.
    Returns formatted address, coordinates, and Lagos determination.
    """
    if not settings.GOOGLE_MAPS_API_KEY:
        # No Google Maps key — do a soft validation using the state the user provided.
        # This still lets pharmacy search run and is_lagos gets determined from the state name.
        from app.utils.nigerian_locations import is_lagos_location
        is_lagos = is_lagos_location(state) if state else None
        return {
            "validated": True,
            "formatted_address": f"{address}, {state}, Nigeria" if state else f"{address}, Nigeria",
            "state": state or None,
            "lga": None,
            "is_lagos": is_lagos,
            "source": "user_input",
        }

    # Append state and Nigeria for better results
    full_query = f"{address}, {state}, Nigeria" if state else f"{address}, Nigeria"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": full_query, "key": settings.GOOGLE_MAPS_API_KEY},
            )

        if resp.status_code != 200:
            return {"validated": False, "reason": "Google API error"}

        data = resp.json()
        if data.get("status") != "OK" or not data.get("results"):
            return {"validated": False, "reason": "Address not found"}

        top = data["results"][0]
        components = top.get("address_components", [])
        location = top.get("geometry", {}).get("location", {})

        # Extract state from Google result
        google_state = None
        google_lga = None
        for comp in components:
            types = comp.get("types", [])
            if "administrative_area_level_1" in types:
                google_state = comp.get("long_name", "")
            if "administrative_area_level_2" in types:
                google_lga = comp.get("long_name", "")

        from app.utils.nigerian_locations import is_lagos_location
        is_lagos = is_lagos_location(google_state)

        return {
            "validated": True,
            "formatted_address": top.get("formatted_address"),
            "lat": location.get("lat"),
            "lng": location.get("lng"),
            "state": google_state,
            "lga": google_lga,
            "is_lagos": is_lagos,
        }

    except Exception as e:
        logger.error("Google Maps validation error: %s", e)
        return {"validated": False, "reason": str(e)}


