"""
Biometric Member Verification Portal – FastAPI Application
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.middleware import SecurityHeadersMiddleware
from app.routers import (
    agent_auth,
    auth,
    authorization,
    biometrics,
    claims,
    claims_portal,
    members,
    reimbursement,
    visits,
)

log = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware (order matters: last added = first executed) ───

# Security headers on every response
app.add_middleware(SecurityHeadersMiddleware)

# CORS – allow Render + localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # permissive for now — tighten after confirmed working
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────

PREFIX = "/api/v1"
app.include_router(auth.router, prefix=PREFIX)
app.include_router(members.router, prefix=PREFIX)
app.include_router(biometrics.router, prefix=PREFIX)
app.include_router(visits.router, prefix=PREFIX)
app.include_router(claims.router, prefix=PREFIX)
app.include_router(agent_auth.router, prefix=PREFIX)
app.include_router(authorization.router, prefix=PREFIX)
app.include_router(reimbursement.router, prefix=PREFIX)
app.include_router(claims_portal.router, prefix=PREFIX)


# ── Startup Events ───────────────────────────────────────────


@app.on_event("startup")
def on_startup():
    """Auto-create tables, seed agents, and expire stale codes on boot."""
    from app.core.database import Base, SessionLocal, engine
    from app.core.security import hash_password
    from app.models.models import Agent
    from app.services.authorization_service import expire_stale_codes

    # 1. Auto-create all tables (safe — skips existing)
    try:
        from app.models import models  # noqa: ensure all models are imported
        Base.metadata.create_all(bind=engine)
        log.info("Startup: database tables ensured")
    except Exception as e:
        log.error("Startup: failed to create tables: %s", e)

    db = SessionLocal()
    try:
        # 2. Auto-seed default agents if none exist
        agent_count = db.query(Agent).count()
        if agent_count == 0:
            log.info("Startup: no agents found — seeding defaults")
            db.add(Agent(name="Call Center Agent", email="agent@leadwayhealth.com", hashed_password=hash_password("agent123"), role="call_center"))
            db.add(Agent(name="Claims Officer", email="claims@leadwayhealth.com", hashed_password=hash_password("claims123"), role="claims_officer"))
            db.add(Agent(name="Admin User", email="admin@leadwayhealth.com", hashed_password=hash_password("admin123"), role="admin"))
            db.commit()
            log.info("Startup: 3 default agents created")

        # 3. Expire stale authorization codes
        count = expire_stale_codes(db)
        if count:
            log.info("Startup: expired %d stale authorization codes", count)
    except Exception as e:
        log.warning("Startup: error during init: %s", e)
    finally:
        db.close()


@app.get("/health")
def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}


@app.get("/api/v1/debug/db")
def debug_db():
    """Check database connectivity and table status."""
    from app.core.database import SessionLocal
    from app.models.models import Agent

    try:
        db = SessionLocal()
        agent_count = db.query(Agent).count()
        agents = [
            {"email": a.email, "role": a.role, "active": a.is_active}
            for a in db.query(Agent).all()
        ]
        db.close()
        return {
            "db_connected": True,
            "agents_count": agent_count,
            "agents": agents,
        }
    except Exception as e:
        return {"db_connected": False, "error": str(e)}


@app.post("/api/v1/debug/init")
def debug_init():
    """Force-create all tables and seed agents. Call once after deploy."""
    from sqlalchemy import text

    from app.core.database import Base, SessionLocal, engine
    from app.core.security import hash_password
    from app.models import models  # noqa: ensure all models loaded
    from app.models.models import Agent

    results = []

    # Create enum types first (ignore if they already exist)
    db = SessionLocal()
    enum_sqls = [
        "DO $$ BEGIN CREATE TYPE agent_role_enum AS ENUM ('call_center', 'claims_officer', 'admin'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;",
        "DO $$ BEGIN CREATE TYPE auth_code_status_enum AS ENUM ('active', 'used', 'expired'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;",
        "DO $$ BEGIN CREATE TYPE claim_status_enum AS ENUM ('submitted', 'under_review', 'pending_info', 'approved', 'rejected', 'payment_processing', 'paid'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;",
    ]
    for sql in enum_sqls:
        try:
            db.execute(text(sql))
            db.commit()
        except Exception as e:
            db.rollback()
            results.append(f"Enum: {e}")

    db.close()

    # Create all tables
    try:
        Base.metadata.create_all(bind=engine)
        results.append("Tables created successfully")
    except Exception as e:
        results.append(f"Table creation error: {e}")
        return {"success": False, "results": results}

    # Seed agents
    db = SessionLocal()
    try:
        agent_count = db.query(Agent).count()
        if agent_count == 0:
            db.add(Agent(name="Call Center Agent", email="agent@leadwayhealth.com", hashed_password=hash_password("agent123"), role="call_center"))
            db.add(Agent(name="Claims Officer", email="claims@leadwayhealth.com", hashed_password=hash_password("claims123"), role="claims_officer"))
            db.add(Agent(name="Admin User", email="admin@leadwayhealth.com", hashed_password=hash_password("admin123"), role="admin"))
            db.commit()
            results.append("3 agents seeded")
        else:
            results.append(f"{agent_count} agents already exist")
    except Exception as e:
        results.append(f"Seed error: {e}")
    finally:
        db.close()

    return {"success": True, "results": results}
