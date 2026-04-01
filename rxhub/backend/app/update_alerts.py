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
        # ── Clear old alerts and newsletters ──────────────
        db.query(Resource).filter(
            Resource.category.in_(["SCARCITY_ALERT", "DRUG_ALERT", "NEWSLETTER"])
        ).delete(synchronize_session=False)
        db.commit()
        print("[*] Cleared old scarcity alerts, drug alerts, and newsletters")

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

        # ── NEWSLETTERS ────────────────────────────────────
        newsletters = [
            Resource(
                title="Health Newsletter: Managing Hypertension",
                body="High blood pressure (hypertension) is one of the most common chronic conditions among Nigerians — yet with the right daily habits it can be managed very effectively. Learn about blood pressure targets, medication adherence, dietary changes (the DASH diet), exercise recommendations, and when to seek emergency care. Read the full newsletter for detailed guidance on living well with hypertension.",
                category="NEWSLETTER",
                diagnosis_tags=["Hypertension"],
                thumbnail_url="/newsletters/hypertension.html",
                is_published=True,
                published_at=datetime.now(timezone.utc),
            ),
            Resource(
                title="Health Newsletter: Living with Type 2 Diabetes",
                body="Type 2 diabetes is increasingly common in Nigeria, particularly in urban areas. It does not have to control your life. With the right knowledge and day-to-day habits, you can keep your blood sugar stable and reduce your risk of complications. This newsletter covers blood sugar targets, HbA1c monitoring, medication management, diet tips, and foot care essentials.",
                category="NEWSLETTER",
                diagnosis_tags=["Diabetes"],
                thumbnail_url="/newsletters/diabetes.html",
                is_published=True,
                published_at=datetime.now(timezone.utc),
            ),
            Resource(
                title="Health Newsletter: Sickle Cell Disease — Daily Care Guide",
                body="Nigeria carries the highest burden of sickle cell disease in the world. Living with SCD requires specific daily care, but with the right approach — and the right support — many people with sickle cell lead fulfilling lives. Learn about crisis prevention, hydration, folic acid supplementation, pain management, and when to go to the emergency room.",
                category="NEWSLETTER",
                diagnosis_tags=["Sickle Cell"],
                thumbnail_url="/newsletters/sickle-cell.html",
                is_published=True,
                published_at=datetime.now(timezone.utc),
            ),
            Resource(
                title="Health Newsletter: Understanding Hypercholesterolaemia",
                body="Hypercholesterolaemia — high levels of cholesterol in the blood — typically has no symptoms at all, yet it is a leading driver of heart attacks and strokes. The encouraging news is that diet and lifestyle changes, combined with medication when needed, can dramatically reduce your risk. Learn about cholesterol targets, statins, heart-healthy eating, and monitoring your levels.",
                category="NEWSLETTER",
                diagnosis_tags=["Hypercholesterolaemia", "Cardiac"],
                thumbnail_url="/newsletters/hypercholesterolaemia.html",
                is_published=True,
                published_at=datetime.now(timezone.utc),
            ),
            Resource(
                title="Health Newsletter: Managing Spondylosis",
                body="Spondylosis refers to the natural wear and tear of the spine — affecting the neck (cervical), mid-back (thoracic), or lower back (lumbar). It is extremely common in adults over 40 and, with the right approach, most people can manage symptoms effectively and stay active. This newsletter covers causes, posture tips, exercise recommendations, pain management, and when to see a specialist.",
                category="NEWSLETTER",
                diagnosis_tags=["Spondylosis", "Musculoskeletal"],
                thumbnail_url="/newsletters/spondylosis.html",
                is_published=True,
                published_at=datetime.now(timezone.utc),
            ),
        ]

        resources.extend(newsletters)

        for r in resources:
            db.add(r)
        db.commit()

        for cat in ["SCARCITY_ALERT", "DRUG_ALERT", "NEWSLETTER"]:
            items = [r for r in resources if r.category == cat]
            print(f"[+] Created {len(items)} {cat.replace('_', ' ').lower()}(s):")
            for r in items:
                print(f"    - {r.title}")

        print(f"\n[OK] All resources updated! ({len(resources)} total)")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    update()
