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

# CORS – tighten origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://member-verification-portal.onrender.com",
    ],
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
    """Run cleanup tasks on application startup."""
    from app.core.database import SessionLocal
    from app.services.authorization_service import expire_stale_codes

    db = SessionLocal()
    try:
        count = expire_stale_codes(db)
        if count:
            log.info("Startup: expired %d stale authorization codes", count)
    except Exception as e:
        log.warning("Startup: failed to expire stale codes: %s", e)
    finally:
        db.close()


@app.get("/health")
def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
