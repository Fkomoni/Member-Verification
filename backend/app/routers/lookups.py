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

        if resp.status_code == 200:
            data = resp.json()
            logger.info("Enrollee lookup raw response: %s", str(data)[:500])

            # Handle various response shapes
            rec = None
            if isinstance(data, list) and len(data) > 0:
                rec = data[0]
            elif isinstance(data, dict):
                # Try nested result/data fields
                for key in ("result", "Result", "data", "Data"):
                    nested = data.get(key)
                    if isinstance(nested, list) and len(nested) > 0:
                        rec = nested[0]
                        break
                    elif isinstance(nested, dict):
                        rec = nested
                        break
                if rec is None:
                    rec = data  # Use root dict directly

            if not rec or (isinstance(rec, dict) and not rec):
                raise HTTPException(404, "Enrollee not found")

            # Log the record keys for debugging
            if isinstance(rec, dict):
                logger.info("Enrollee record keys: %s", list(rec.keys()))

            # Extract fields using exact Prognosis field names from logs
            surname = rec.get("Member_Surname") or ""
            firstname = rec.get("Member_Firstname") or rec.get("Member_othernames") or ""
            name = f"{surname} {firstname}".strip() or "Unknown"

            # Calculate age from DOB
            age = None
            member_age = rec.get("Member_Age")
            if member_age:
                age = str(member_age)

            # Member status
            status = rec.get("Member_MemberStatus") or rec.get("Member_MemberStatusDescription") or ""
            status_desc = rec.get("Member_MemberStatusDescription") or status

            return {
                "found": True,
                "enrollee_id": enrollee_id,
                "name": name,
                "gender": rec.get("Member_Gender") or rec.get("Female") or "",
                "age": age,
                "dob": rec.get("Member_DateOfBirth"),
                "plan": rec.get("Product_schemeName") or rec.get("Member_AccountName") or "",
                "status": status,
                "status_description": status_desc,
                "phone": rec.get("Member_Phone_One") or rec.get("Member_Phone_Two") or rec.get("Member_Phone_Three") or "",
                "email": rec.get("Member_EmailAddress_Two") or rec.get("Member_EmailAddress_One") or "",
                "member_id": rec.get("Member_ParentMembershipID") or rec.get("Member_MembershipID") or "",
                "company": rec.get("Member_AccountName") or "",
                "location": rec.get("Member_Location") or "",
                "state": rec.get("Member_initialStatusDescription") or "",
                "country": rec.get("Member_Country") or "",
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
        return {"validated": False, "reason": "Google Maps not configured"}

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
