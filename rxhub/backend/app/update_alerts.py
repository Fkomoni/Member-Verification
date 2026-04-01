"""
Update scarcity alerts with real drug scarcity data.
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
        # Delete old scarcity alerts
        db.query(Resource).filter(Resource.category == "SCARCITY_ALERT").delete()
        db.commit()
        print("[*] Cleared old scarcity alerts")

        alerts = [
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
        ]

        for a in alerts:
            db.add(a)
        db.commit()
        print(f"[+] Created {len(alerts)} scarcity alerts:")
        for a in alerts:
            print(f"    - {a.title}")

        print("\n[OK] Scarcity alerts updated!")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    update()
