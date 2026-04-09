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
    logger.info("Database tables ready.")

    # Auto-sync WellaHealth tariff if drug_master has few records
    try:
        from app.core.database import SessionLocal
        from app.models.medication import DrugMaster
        from app.services.tariff_sync import run_tariff_sync
        db = SessionLocal()
        count = db.query(DrugMaster).filter(DrugMaster.source == "wellahealth").count()
        if count < 100:
            logger.info("Drug master has %d WellaHealth records — starting tariff sync...", count)
            result = await run_tariff_sync(db)
            logger.info("Tariff sync result: %s", result)
        else:
            logger.info("Drug master has %d WellaHealth records — skipping sync", count)
        db.close()
    except Exception as e:
        logger.error("Startup tariff sync failed (non-blocking): %s", e)


@app.get("/health")
def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
