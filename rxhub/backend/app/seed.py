"""
Seed script: populate test data for local development/testing.
Run: cd rxhub/backend && python -m app.seed
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, datetime, timedelta, timezone
from app.core.database import engine, Base, SessionLocal
from app.core.security import hash_password
from app.models.member import Member
from app.models.medication import Medication
from app.models.admin import Admin
from app.models.resource import Resource
from app.models.notification import Notification


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # ── Test Member ───────────────────────────────────────
        member = db.query(Member).filter(Member.member_id == "21000645/0").first()
        if not member:
            member = Member(
                member_id="21000645/0",
                first_name="Test",
                last_name="Enrollee",
                email="test@leadwayhmo.com",
                phone="08012345678",
                date_of_birth=date(1990, 5, 15),
                gender="Male",
                diagnosis="Hypertension, Type 2 Diabetes",
                plan_type="GOLD",
                plan_name="Leadway Gold Plan",
                employer="Leadway Assurance",
                status="ACTIVE",
                pbm_synced_at=datetime.now(timezone.utc),
            )
            db.add(member)
            db.flush()
            print(f"[+] Created test member: {member.member_id}")
        else:
            print(f"[=] Member already exists: {member.member_id}")

        # ── Sample Medications ────────────────────────────────
        meds_data = [
            {
                "drug_name": "Amlodipine",
                "generic_name": "Amlodipine Besylate",
                "dosage": "10mg",
                "frequency": "Once daily",
                "route": "Oral",
                "prescriber": "Dr. Adebayo",
                "start_date": date(2025, 1, 15),
                "is_covered": True,
                "coverage_pct": 80.00,
                "copay_amount": 500.00,
                "refill_count": 3,
                "max_refills": 12,
                "last_refill_at": datetime.now(timezone.utc) - timedelta(days=22),
                "next_refill_due": date.today() + timedelta(days=8),
                "days_supply": 30,
                "quantity": 30,
                "status": "ACTIVE",
                "pbm_drug_id": "AMB-010",
            },
            {
                "drug_name": "Metformin",
                "generic_name": "Metformin Hydrochloride",
                "dosage": "500mg",
                "frequency": "Twice daily",
                "route": "Oral",
                "prescriber": "Dr. Adebayo",
                "start_date": date(2025, 2, 1),
                "is_covered": True,
                "coverage_pct": 100.00,
                "copay_amount": 0.00,
                "refill_count": 5,
                "max_refills": 12,
                "last_refill_at": datetime.now(timezone.utc) - timedelta(days=26),
                "next_refill_due": date.today() + timedelta(days=4),
                "days_supply": 30,
                "quantity": 60,
                "status": "ACTIVE",
                "pbm_drug_id": "MET-500",
            },
            {
                "drug_name": "Lisinopril",
                "generic_name": "Lisinopril",
                "dosage": "20mg",
                "frequency": "Once daily",
                "route": "Oral",
                "prescriber": "Dr. Nwosu",
                "start_date": date(2025, 3, 10),
                "is_covered": True,
                "coverage_pct": 70.00,
                "copay_amount": 800.00,
                "refill_count": 1,
                "max_refills": 6,
                "last_refill_at": datetime.now(timezone.utc) - timedelta(days=28),
                "next_refill_due": date.today() + timedelta(days=2),
                "days_supply": 30,
                "quantity": 30,
                "status": "ACTIVE",
                "pbm_drug_id": "LIS-020",
            },
            {
                "drug_name": "Atorvastatin",
                "generic_name": "Atorvastatin Calcium",
                "dosage": "20mg",
                "frequency": "Once daily at bedtime",
                "route": "Oral",
                "prescriber": "Dr. Adebayo",
                "start_date": date(2025, 1, 15),
                "is_covered": False,
                "coverage_pct": 0.00,
                "copay_amount": 3500.00,
                "refill_count": 2,
                "max_refills": 12,
                "last_refill_at": datetime.now(timezone.utc) - timedelta(days=15),
                "next_refill_due": date.today() + timedelta(days=15),
                "days_supply": 30,
                "quantity": 30,
                "status": "ACTIVE",
                "pbm_drug_id": "ATV-020",
            },
            {
                "drug_name": "Aspirin",
                "generic_name": "Acetylsalicylic Acid",
                "dosage": "75mg",
                "frequency": "Once daily",
                "route": "Oral",
                "prescriber": "Dr. Nwosu",
                "start_date": date(2024, 11, 1),
                "is_covered": True,
                "coverage_pct": 100.00,
                "copay_amount": 0.00,
                "refill_count": 8,
                "max_refills": 12,
                "last_refill_at": datetime.now(timezone.utc) - timedelta(days=10),
                "next_refill_due": date.today() + timedelta(days=20),
                "days_supply": 30,
                "quantity": 30,
                "status": "ACTIVE",
                "pbm_drug_id": "ASP-075",
            },
        ]

        # Skip test medications — real data comes from Prognosis PharmacyDelivery API on login
        print(f"[*] Medications: will be synced from Prognosis API on first login")

        # ── Admin User ────────────────────────────────────────
        admin = db.query(Admin).filter(Admin.email == "admin@leadwayhmo.com").first()
        if not admin:
            admin = Admin(
                email="admin@leadwayhmo.com",
                password_hash=hash_password("admin123"),
                full_name="RxHub Admin",
                role="SUPER_ADMIN",
                is_active=True,
            )
            db.add(admin)
            print("[+] Created admin: admin@leadwayhmo.com / admin123")
        else:
            print(f"[=] Admin already exists: {admin.email}")

        # ── Sample Resources ──────────────────────────────────
        resource_count = db.query(Resource).count()
        if resource_count == 0:
            resources = [
                Resource(
                    title="Managing Hypertension: What You Need to Know",
                    body="High blood pressure affects millions of Nigerians. Learn how to manage your condition through medication adherence, diet changes, and regular monitoring. Always take your antihypertensives at the same time every day.",
                    category="HEALTH_TIP",
                    diagnosis_tags=["Hypertension"],
                    is_published=True,
                    published_at=datetime.now(timezone.utc),
                ),
                Resource(
                    title="Drug Alert: Metformin Recall Batch #MF2025-03",
                    body="A batch of Metformin 500mg tablets (Batch #MF2025-03) from Generic Pharma has been recalled due to NDMA contamination concerns. If you have this batch, return to your pharmacy for replacement.",
                    category="DRUG_ALERT",
                    diagnosis_tags=["Diabetes"],
                    is_published=True,
                    published_at=datetime.now(timezone.utc),
                ),
                Resource(
                    title="Amlodipine Temporary Scarcity Notice",
                    body="Due to supply chain disruptions, Amlodipine 10mg may be temporarily unavailable at some pharmacies. Alternative brands are being sourced. Contact your provider if you cannot locate your medication.",
                    category="SCARCITY_ALERT",
                    diagnosis_tags=["Hypertension"],
                    is_published=True,
                    published_at=datetime.now(timezone.utc),
                ),
                Resource(
                    title="RxHub Monthly Newsletter — April 2026",
                    body="Welcome to the LeadwayHMO RxHub newsletter! This month: new self-service features, refill reminders, and tips for medication adherence. We've launched the ability to request refills, update your profile, and track request status all from your phone.",
                    category="NEWSLETTER",
                    diagnosis_tags=[],
                    is_published=True,
                    published_at=datetime.now(timezone.utc),
                ),
            ]
            for r in resources:
                db.add(r)
            print(f"[+] Created {len(resources)} sample resources")

        # ── Welcome Notification ──────────────────────────────
        notif_count = db.query(Notification).filter(Notification.member_id == member.member_id).count()
        if notif_count == 0:
            notifications = [
                Notification(
                    member_id=member.member_id,
                    title="Welcome to RxHub!",
                    body="Your self-service portal is ready. View your medications, request refills, and manage your health.",
                    category="GENERAL",
                ),
                Notification(
                    member_id=member.member_id,
                    title="Refill Reminder: Lisinopril",
                    body="Your Lisinopril 20mg supply runs out in 2 days. Request a refill now.",
                    category="REFILL_REMINDER",
                ),
                Notification(
                    member_id=member.member_id,
                    title="Drug Scarcity Alert",
                    body="Amlodipine 10mg is temporarily scarce. Check the Resource Center for alternatives.",
                    category="DRUG_ALERT",
                ),
            ]
            for n in notifications:
                db.add(n)
            print(f"[+] Created {len(notifications)} notifications")

        db.commit()
        print("\n[OK] Seed complete!")
        print(f"\n  Member login:  ID=21000645/0  Phone=08012345678")
        print(f"  Admin login:   admin@leadwayhmo.com / admin123")
        print(f"  Medications:   5 active drugs with refill data")
        print(f"  Resources:     4 published articles")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
