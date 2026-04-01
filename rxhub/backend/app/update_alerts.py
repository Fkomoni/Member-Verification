"""
Update resource alerts with real drug scarcity and NAFDAC ban data.
Run on Render shell: python3 -m app.update_alerts
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
from app.core.database import SessionLocal
from app.models.resource import Resource


def update():
    db = SessionLocal()
    try:
        # ── Clear old scarcity alerts and drug alerts ─────────
        db.query(Resource).filter(Resource.category.in_(["SCARCITY_ALERT", "DRUG_ALERT"])).delete(synchronize_session=False)
        db.commit()
        print("[*] Cleared old scarcity alerts and drug alerts")

        resources = [
            # ── SCARCITY ALERTS ───────────────────────────────
            Resource(
                title="Epilim Syrup — Temporary Scarcity Notice",
                body="Due to supply chain disruptions, Epilim Syrup may be temporarily unavailable at most pharmacies. Alternative option would be to visit your doctor for an alternative prescription. We are actively working with suppliers to resolve this shortage.",
                category="SCARCITY_ALERT",
                diagnosis_tags=["Epilepsy", "Seizures"],
                is_published=True,
                published_at=datetime.now(timezone.utc),
            ),
            Resource(
                title="Micardis 40mg — Temporary Scarcity Notice",
                body="Micardis 40mg (Telmisartan) is currently experiencing supply shortages across most pharmacies. Please consult your doctor for alternative antihypertensive options. We apologize for the inconvenience.",
                category="SCARCITY_ALERT",
                diagnosis_tags=["Hypertension"],
                is_published=True,
                published_at=datetime.now(timezone.utc),
            ),
            Resource(
                title="Twynsta Brands — Temporary Scarcity Notice",
                body="Twynsta (Telmisartan/Amlodipine combination) brands are currently scarce due to supply chain disruptions. Please contact your prescribing doctor for alternative combination therapy options.",
                category="SCARCITY_ALERT",
                diagnosis_tags=["Hypertension"],
                is_published=True,
                published_at=datetime.now(timezone.utc),
            ),
            Resource(
                title="Atacand & Atacand Plus — Temporary Scarcity Notice",
                body="Atacand (Candesartan) and Atacand Plus (Candesartan/Hydrochlorothiazide) are temporarily unavailable at most pharmacies due to supply chain issues. Please visit your doctor for an alternative prescription. We are monitoring the situation closely.",
                category="SCARCITY_ALERT",
                diagnosis_tags=["Hypertension"],
                is_published=True,
                published_at=datetime.now(timezone.utc),
            ),

            # ── DRUG ALERTS (NAFDAC BAN) ──────────────────────
            Resource(
                title="NAFDAC Alert: Banned Medications — Immediate Action Required",
                body="""The National Agency for Food and Drug Administration and Control (NAFDAC) has blacklisted the following medications from the Nigerian market. These products are no longer authorized for sale or distribution in Nigeria.

If you are currently taking any of these medications, please contact your doctor immediately for a safe alternative. Do NOT stop taking your medication abruptly — your doctor will guide you on how to safely transition to an approved alternative.

BANNED MEDICATIONS:

Diabetes:
- Januvia 100mg Tablets
- Januvia 50mg Tablets
- Diamicron 30mg Tablets
- Diamicron 60mg Tablets

Hypertension (Blood Pressure):
- Natrilix (Indapamide)
- Natrixiam 1.5/10mg
- Natrixiam 1.5/5mg
- Coveram 10mg/10mg Tablets
- Coveram 10mg/5mg Tablets
- Coveram 5mg/10mg Tablets
- Coveram 5mg/5mg Tablets
- Coversyl 5mg Tablets
- Coversyl 10mg Tablets
- Coversyl Plus 10mg/2.5mg Tablets
- Coversyl Plus 5mg/1.25mg Tablets
- Coveram Plus 5mg/1.25mg/5mg
- Coveram Plus 5mg/1.25mg/10mg
- Coveram Plus 10mg/1.25mg/5mg
- Coveram Plus 10mg/1.25mg/10mg
- Coaprovel 300mg/25mg Tablets

Cardiac / Vascular:
- Vastarel 60MR
- Daflon 500mg
- Daflon 1000mg

Dermatology / Antifungal:
- Daktarin 2% 1x15g Cream

Ophthalmology (Eye Care):
- Betoptic Eye Drop
- Elisca Eye Drop

This is a regulatory directive. Leadway Health is working to ensure all affected members are transitioned to safe, NAFDAC-approved alternatives. If you have any of these medications at home, do not use them and consult your healthcare provider.""",
                category="DRUG_ALERT",
                diagnosis_tags=["Diabetes", "Hypertension", "Cardiac", "General"],
                is_published=True,
                published_at=datetime.now(timezone.utc),
            ),
        ]

        for r in resources:
            db.add(r)
        db.commit()

        scarcity_count = sum(1 for r in resources if r.category == "SCARCITY_ALERT")
        alert_count = sum(1 for r in resources if r.category == "DRUG_ALERT")
        print(f"[+] Created {scarcity_count} scarcity alerts:")
        for r in resources:
            if r.category == "SCARCITY_ALERT":
                print(f"    - {r.title}")

        print(f"[+] Created {alert_count} drug alert(s):")
        for r in resources:
            if r.category == "DRUG_ALERT":
                print(f"    - {r.title}")

        print("\n[OK] All alerts updated!")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    update()
