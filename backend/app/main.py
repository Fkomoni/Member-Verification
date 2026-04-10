"""
Biometric Member Verification Portal + Medication Routing Hub – FastAPI Application
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.models import medication as medication_models  # noqa: F401 — register models
from app.routers import (
    admin_review, auth, biometrics, claims,
    drug_master, lookups, medication_requests,
    members, reports, visits,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS – tighten origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://leadway-rx-portal.onrender.com",
        "https://member-verification-portal.onrender.com",
        "https://leadway-rx-api.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers under /api/v1
PREFIX = "/api/v1"
app.include_router(auth.router, prefix=PREFIX)
app.include_router(members.router, prefix=PREFIX)
app.include_router(biometrics.router, prefix=PREFIX)
app.include_router(visits.router, prefix=PREFIX)
app.include_router(claims.router, prefix=PREFIX)
app.include_router(drug_master.router, prefix=PREFIX)
app.include_router(medication_requests.router, prefix=PREFIX)
app.include_router(admin_review.router, prefix=PREFIX)
app.include_router(reports.router, prefix=PREFIX)
app.include_router(lookups.router, prefix=PREFIX)


@app.on_event("startup")
async def on_startup():
    """Create tables, seed drug master, and sync WellaHealth tariff on startup."""
    logger.info("Creating database tables (if not exist)...")
    Base.metadata.create_all(bind=engine)

    # Ensure new columns exist (for existing tables)
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            for col, col_type in [
                ("drug_name_display", "VARCHAR(400)"),
                ("brand_name", "VARCHAR(300)"),
                ("dosage_form", "VARCHAR(100)"),
                ("strength", "VARCHAR(100)"),
                ("drug_class", "VARCHAR(200)"),
                ("member_phone", "VARCHAR(30)"),
                ("member_email", "VARCHAR(200)"),
            ]:
                try:
                    if col not in ("member_phone", "member_email"):
                        conn.execute(text(f"ALTER TABLE drug_master ADD COLUMN IF NOT EXISTS {col} {col_type}"))
                    else:
                        conn.execute(text(f"ALTER TABLE medication_requests ADD COLUMN IF NOT EXISTS {col} {col_type}"))
                except Exception:
                    pass
            # Make delivery_lga nullable
            try:
                conn.execute(text("ALTER TABLE medication_requests ALTER COLUMN delivery_lga DROP NOT NULL"))
            except Exception:
                pass
            # Make quantity nullable (WellaHealth format doesn't require quantity)
            try:
                conn.execute(text("ALTER TABLE medication_request_items ALTER COLUMN quantity DROP NOT NULL"))
            except Exception:
                pass
            # Add pharmacy_code column for WellaHealth fulfilment tracking
            try:
                conn.execute(text("ALTER TABLE medication_requests ADD COLUMN IF NOT EXISTS pharmacy_code VARCHAR(100)"))
            except Exception:
                pass
            conn.commit()
    except Exception as e:
        logger.warning("Column migration non-critical: %s", e)

    logger.info("Database tables ready.")

    # ── Auto-seed drug master from built-in seed data ─────────────
    # Runs every startup — idempotent (skips drugs that already exist).
    # Ensures paracetamol and all common Nigerian drugs are always
    # pre-classified (acute/chronic) from the very first boot.
    try:
        from sqlalchemy import func
        from app.core.database import SessionLocal
        from app.models.medication import DrugAlias, DrugMaster
        from app.services.drug_master_seed import get_seed_drugs

        db = SessionLocal()
        try:
            seed_data = get_seed_drugs()
            created = 0
            for entry in seed_data:
                existing = db.query(DrugMaster).filter(
                    func.lower(DrugMaster.generic_name) == entry["generic_name"].lower()
                ).first()
                if existing:
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
                db.flush()
                for alias_name in entry.get("aliases", []):
                    db.add(DrugAlias(
                        drug_id=drug.drug_id,
                        alias_name=alias_name,
                        alias_type="brand",
                    ))
                created += 1
            db.commit()
            total = db.query(DrugMaster).count()
            logger.info("Drug master seed: %d new drugs added, %d total in database", created, total)
        finally:
            db.close()
    except Exception as e:
        logger.error("Drug master seed failed (non-blocking): %s", e, exc_info=True)

    # ── Auto-sync WellaHealth tariff if drug_master has few searchable records ─
    try:
        from sqlalchemy import text as sql_text
        from app.core.database import SessionLocal
        from app.services.tariff_sync import run_tariff_sync

        db = SessionLocal()
        try:
            row = db.execute(sql_text(
                "SELECT COUNT(*) FROM drug_master WHERE drug_name_display IS NOT NULL AND source = 'wellahealth'"
            )).scalar()
            count_display = row or 0
        except Exception:
            count_display = 0

        if count_display < 50:
            logger.info("Drug master has %d WellaHealth records — starting tariff sync...", count_display)
            result = await run_tariff_sync(db)
            logger.info("Tariff sync result: %s", result)
        else:
            logger.info("Drug master has %d WellaHealth records — skipping sync", count_display)
        db.close()
    except Exception as e:
        logger.error("Startup tariff sync failed (non-blocking): %s", e)


@app.get("/health")
def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}


@app.post("/admin/seed-drugs")
def force_seed_drugs():
    """
    Manually seed the drug master with pre-classified Nigerian medications.
    Idempotent — safe to call multiple times, skips drugs that already exist.
    Call this once after a fresh deploy if the startup seed didn't run.
    """
    from sqlalchemy import func
    from app.core.database import SessionLocal
    from app.models.medication import DrugAlias, DrugMaster
    from app.services.drug_master_seed import get_seed_drugs

    db = SessionLocal()
    try:
        seed_data = get_seed_drugs()
        created = 0
        skipped = 0
        for entry in seed_data:
            existing = db.query(DrugMaster).filter(
                func.lower(DrugMaster.generic_name) == entry["generic_name"].lower()
            ).first()
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
            db.flush()
            for alias_name in entry.get("aliases", []):
                db.add(DrugAlias(
                    drug_id=drug.drug_id,
                    alias_name=alias_name,
                    alias_type="brand",
                ))
            created += 1
        db.commit()
        total = db.query(DrugMaster).count()
        logger.info("Manual seed: created=%d, skipped=%d, total=%d", created, skipped, total)
        return {
            "message": "Drug master seeded",
            "created": created,
            "skipped": skipped,
            "total_in_db": total,
        }
    except Exception as e:
        db.rollback()
        logger.error("Manual seed failed: %s", e, exc_info=True)
        return {"error": str(e)}
    finally:
        db.close()
