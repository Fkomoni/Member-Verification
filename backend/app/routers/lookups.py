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


# ── Diagnosis List (Top 200 Nigerian ICD-10) ────────────────────

ICD10_DIAGNOSES_NIGERIA: list[str] = [
    "B50.9 - Plasmodium falciparum malaria, unspecified",
    "B51.9 - Plasmodium vivax malaria, unspecified",
    "B54 - Unspecified malaria",
    "I10 - Essential (primary) hypertension",
    "I11.9 - Hypertensive heart disease without heart failure",
    "I13.10 - Hypertensive heart and chronic kidney disease",
    "E11.9 - Type 2 diabetes mellitus without complications",
    "E11.65 - Type 2 diabetes mellitus with hyperglycemia",
    "E10.9 - Type 1 diabetes mellitus without complications",
    "E14.9 - Unspecified diabetes mellitus without complications",
    "A01.0 - Typhoid fever",
    "A01.1 - Paratyphoid fever A",
    "A09 - Infectious gastroenteritis and colitis, unspecified",
    "N39.0 - Urinary tract infection, site not specified",
    "J18.9 - Pneumonia, unspecified organism",
    "J18.0 - Bronchopneumonia, unspecified organism",
    "J15.9 - Unspecified bacterial pneumonia",
    "J45.9 - Asthma, unspecified",
    "J45.20 - Mild intermittent asthma, uncomplicated",
    "J45.40 - Moderate persistent asthma, uncomplicated",
    "K25.9 - Gastric ulcer, unspecified",
    "K27.9 - Peptic ulcer, site unspecified",
    "K29.70 - Gastritis, unspecified, without bleeding",
    "K21.0 - Gastro-esophageal reflux disease with esophagitis",
    "J06.9 - Acute upper respiratory infection, unspecified",
    "J02.9 - Acute pharyngitis, unspecified",
    "J03.9 - Acute tonsillitis, unspecified",
    "J00 - Acute nasopharyngitis (common cold)",
    "J20.9 - Acute bronchitis, unspecified",
    "J44.1 - Chronic obstructive pulmonary disease with acute exacerbation",
    "J44.9 - Chronic obstructive pulmonary disease, unspecified",
    "A06.9 - Amoebiasis, unspecified",
    "A06.0 - Acute amoebic dysentery",
    "A04.9 - Bacterial intestinal infection, unspecified",
    "A07.1 - Giardiasis",
    "K59.0 - Constipation, unspecified",
    "K58.9 - Irritable bowel syndrome without diarrhea",
    "K30 - Functional dyspepsia",
    "B37.9 - Candidiasis, unspecified",
    "B37.3 - Candidiasis of vulva and vagina",
    "N76.0 - Acute vaginitis",
    "N77.1 - Vaginitis in diseases classified elsewhere",
    "L30.9 - Dermatitis, unspecified",
    "L20.9 - Atopic dermatitis, unspecified",
    "L23.9 - Allergic contact dermatitis, unspecified cause",
    "B35.9 - Dermatophytosis, unspecified",
    "B35.1 - Tinea unguium (onychomycosis)",
    "B36.0 - Pityriasis versicolor",
    "M54.5 - Low back pain",
    "M54.9 - Dorsalgia, unspecified",
    "M79.3 - Panniculitis, unspecified",
    "M25.50 - Pain in unspecified joint",
    "M13.9 - Arthritis, unspecified",
    "M06.9 - Rheumatoid arthritis, unspecified",
    "M10.9 - Gout, unspecified",
    "G43.9 - Migraine, unspecified",
    "G44.1 - Vascular headache, not elsewhere classified",
    "R51 - Headache",
    "D50.9 - Iron deficiency anaemia, unspecified",
    "D64.9 - Anaemia, unspecified",
    "E55.9 - Vitamin D deficiency, unspecified",
    "E56.1 - Vitamin B deficiency, unspecified",
    "E61.1 - Iron deficiency",
    "J30.9 - Allergic rhinitis, unspecified",
    "J31.0 - Chronic rhinitis",
    "J32.9 - Chronic sinusitis, unspecified",
    "J01.9 - Acute sinusitis, unspecified",
    "H10.9 - Unspecified conjunctivitis",
    "H10.1 - Acute atopic conjunctivitis",
    "H66.9 - Otitis media, unspecified",
    "H65.9 - Unspecified nonsuppurative otitis media",
    "E03.9 - Hypothyroidism, unspecified",
    "E05.9 - Thyrotoxicosis, unspecified",
    "E04.9 - Nontoxic goitre, unspecified",
    "E78.5 - Hyperlipidaemia, unspecified",
    "E78.0 - Pure hypercholesterolaemia",
    "I25.10 - Atherosclerotic heart disease",
    "I48.91 - Atrial fibrillation, unspecified",
    "I50.9 - Heart failure, unspecified",
    "I63.9 - Cerebral infarction, unspecified",
    "I64 - Stroke, not specified as haemorrhage or infarction",
    "G40.9 - Epilepsy, unspecified",
    "G40.309 - Generalized idiopathic epilepsy",
    "F32.9 - Major depressive disorder, single episode, unspecified",
    "F33.9 - Major depressive disorder, recurrent, unspecified",
    "F41.9 - Anxiety disorder, unspecified",
    "F41.1 - Generalized anxiety disorder",
    "F10.20 - Alcohol dependence, uncomplicated",
    "F20.9 - Schizophrenia, unspecified",
    "G47.9 - Sleep disorder, unspecified",
    "G47.00 - Insomnia, unspecified",
    "B20 - Human immunodeficiency virus (HIV) disease",
    "A15.0 - Tuberculosis of lung",
    "A16.9 - Respiratory tuberculosis, unspecified",
    "B18.1 - Chronic viral hepatitis B",
    "B18.2 - Chronic viral hepatitis C",
    "B19.9 - Unspecified viral hepatitis",
    "A63.0 - Anogenital (venereal) warts",
    "A56.2 - Chlamydial infection of genitourinary tract",
    "A54.9 - Gonococcal infection, unspecified",
    "N40.0 - Benign prostatic hyperplasia without obstruction",
    "N41.0 - Acute prostatitis",
    "N18.9 - Chronic kidney disease, unspecified",
    "N17.9 - Acute kidney failure, unspecified",
    "K76.0 - Fatty (change of) liver, not elsewhere classified",
    "K74.6 - Other and unspecified cirrhosis of liver",
    "K70.30 - Alcoholic cirrhosis of liver",
    "K80.20 - Calculus of gallbladder without cholecystitis",
    "K81.0 - Acute cholecystitis",
    "O80 - Encounter for full-term uncomplicated delivery",
    "O26.9 - Pregnancy-related condition, unspecified",
    "O99.0 - Anaemia complicating pregnancy, childbirth and puerperium",
    "O24.9 - Gestational diabetes mellitus, unspecified",
    "O13 - Gestational hypertension",
    "O14.9 - Pre-eclampsia, unspecified",
    "Z34.00 - Encounter for supervision of normal first pregnancy",
    "B76.9 - Hookworm disease, unspecified",
    "B77.9 - Ascariasis, unspecified",
    "B82.0 - Intestinal helminthiasis, unspecified",
    "A00.9 - Cholera, unspecified",
    "A03.9 - Shigellosis, unspecified",
    "E46 - Unspecified protein-calorie malnutrition",
    "E44.0 - Moderate protein-calorie malnutrition",
    "R50.9 - Fever, unspecified",
    "R11.2 - Nausea with vomiting, unspecified",
    "R10.9 - Unspecified abdominal pain",
    "R05 - Cough",
    "R53.1 - Weakness",
    "R42 - Dizziness and giddiness",
    "R00.0 - Tachycardia, unspecified",
    "R07.9 - Chest pain, unspecified",
    "R60.0 - Localized oedema",
    "L02.9 - Cutaneous abscess, furuncle and carbuncle, unspecified",
    "L03.9 - Cellulitis, unspecified",
    "L08.9 - Local infection of skin, unspecified",
    "B02.9 - Zoster without complications (Herpes zoster)",
    "B00.9 - Herpesviral infection, unspecified",
    "B01.9 - Varicella without complication (Chickenpox)",
    "A46 - Erysipelas",
    "J10.1 - Influenza with other respiratory manifestations",
    "J11.1 - Influenza with other respiratory manifestations, virus not identified",
    "U07.1 - COVID-19",
    "N20.0 - Calculus of kidney",
    "N23 - Unspecified renal colic",
    "N30.0 - Acute cystitis",
    "N34.1 - Nonspecific urethritis",
    "N70.9 - Salpingitis and oophoritis, unspecified (PID)",
    "N73.0 - Acute parametritis and pelvic cellulitis",
    "N80.9 - Endometriosis, unspecified",
    "N92.0 - Excessive and frequent menstruation with regular cycle",
    "N91.2 - Amenorrhoea, unspecified",
    "N94.6 - Dysmenorrhoea, unspecified",
    "E66.9 - Obesity, unspecified",
    "E66.01 - Morbid obesity due to excess calories",
    "R73.9 - Hyperglycaemia, unspecified",
    "E16.2 - Hypoglycaemia, unspecified",
    "E87.6 - Hypokalaemia",
    "E87.1 - Hypo-osmolality and hyponatraemia",
    "L50.9 - Urticaria, unspecified",
    "T78.4 - Allergy, unspecified",
    "J45.0 - Predominantly allergic asthma",
    "J67.9 - Hypersensitivity pneumonitis due to unspecified organic dust",
    "K02.9 - Dental caries, unspecified",
    "K04.7 - Periapical abscess without sinus",
    "K05.1 - Chronic gingivitis",
    "M81.0 - Age-related osteoporosis without current pathological fracture",
    "M80.0 - Age-related osteoporosis with current pathological fracture",
    "M51.9 - Unspecified thoracic, thoracolumbar and lumbosacral disc disorder",
    "M47.9 - Spondylosis, unspecified",
    "G56.0 - Carpal tunnel syndrome",
    "M75.1 - Rotator cuff syndrome",
    "I83.9 - Varicose veins of lower extremities without ulcer or inflammation",
    "I84.9 - Unspecified haemorrhoids",
    "K60.0 - Acute anal fissure",
    "K62.5 - Haemorrhage of anus and rectum",
    "J98.4 - Other disorders of lung",
    "J96.9 - Respiratory failure, unspecified",
    "J84.9 - Interstitial pulmonary disease, unspecified",
    "C50.9 - Malignant neoplasm of breast, unspecified",
    "C61 - Malignant neoplasm of prostate",
    "C34.9 - Malignant neoplasm of bronchus or lung, unspecified",
    "D25.9 - Leiomyoma of uterus, unspecified (uterine fibroids)",
    "N85.0 - Endometrial glandular hyperplasia",
    "Z30.0 - Encounter for general counselling on contraception",
    "Z23 - Encounter for immunization",
    "Z00.0 - Encounter for general adult medical examination",
    "Z01.1 - Encounter for examination of eyes and vision",
    "Z96.1 - Presence of intraocular lens",
    "H40.9 - Unspecified glaucoma",
    "H25.9 - Unspecified age-related cataract",
    "H52.1 - Myopia",
    "E27.1 - Primary adrenocortical insufficiency",
    "E27.4 - Other and unspecified adrenocortical insufficiency",
    "S06.0 - Concussion",
    "S82.9 - Unspecified fracture of lower leg",
    "S52.9 - Unspecified fracture of forearm",
    "T14.9 - Injury, unspecified",
    "T30.0 - Burn of unspecified body region, unspecified degree",
    "W19 - Unspecified fall",
    "V89.2 - Person injured in unspecified motor-vehicle accident",
    "D57.1 - Sickle-cell disease without crisis",
    "D57.0 - Sickle-cell anaemia with crisis",
]


@router.get("/lookup/diagnoses")
async def get_diagnosis_list(
    _provider=Depends(get_current_provider),
):
    """
    Return top 200 ICD-10 diagnoses commonly used in Nigeria.
    """
    return {"diagnoses": ICD10_DIAGNOSES_NIGERIA}


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

    # Simple ILIKE search — works on PostgreSQL
    results = db.execute(
        text("""
            SELECT drug_id, drug_name_display, generic_name, brand_name,
                   strength, dosage_form, drug_class, category
            FROM drug_master
            WHERE is_active = true
              AND (
                drug_name_display ILIKE :q
                OR generic_name ILIKE :q
                OR brand_name ILIKE :q
              )
            ORDER BY drug_name_display
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
    """Search WellaHealth pharmacies by location."""
    results = await wellahealth_client.search_pharmacies(state, lga, area)
    return {"pharmacies": results, "total": len(results)}


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
