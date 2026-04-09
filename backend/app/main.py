"""
Biometric Member Verification Portal + Medication Routing Hub – FastAPI Application
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.models import medication as medication_models  # noqa: F401 — register models
from app.routers import admin_review, auth, biometrics, claims, drug_master, lookups, medication_requests, members, reports, visits

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
        "https://member-verification-portal.onrender.com",
        "https://leadway-rx-portal.onrender.com",
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
    """Create tables and sync tariff on startup."""
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
                    # Try drug_master columns
                    if col not in ("member_phone", "member_email"):
                        conn.execute(text(f"ALTER TABLE drug_master ADD COLUMN IF NOT EXISTS {col} {col_type}"))
                    else:
                        conn.execute(text(f"ALTER TABLE medication_requests ADD COLUMN IF NOT EXISTS {col} {col_type}"))
                except Exception:
                    pass
            conn.commit()
    except Exception as e:
        logger.warning("Column migration non-critical: %s", e)

    logger.info("Database tables ready.")

    # Auto-sync WellaHealth tariff if drug_master has few records
    try:
        from app.core.database import SessionLocal
        from app.models.medication import DrugMaster
        from app.services.tariff_sync import run_tariff_sync
        db = SessionLocal()
        # Check if drug_name_display is populated for searchability
        from sqlalchemy import text as sql_text
        try:
            row = db.execute(sql_text(
                "SELECT COUNT(*) FROM drug_master WHERE drug_name_display IS NOT NULL AND source = 'wellahealth'"
            )).scalar()
            count_display = row or 0
        except Exception:
            count_display = 0
        if count_display < 50:
            logger.info("Drug master has %d searchable WellaHealth records — starting tariff sync...", count_display)
            result = await run_tariff_sync(db)
            logger.info("Tariff sync result: %s", result)
        else:
            logger.info("Drug master has %d searchable WellaHealth records — skipping sync", count_display)
        db.close()
    except Exception as e:
        logger.error("Startup tariff sync failed (non-blocking): %s", e)


@app.get("/health")
def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
