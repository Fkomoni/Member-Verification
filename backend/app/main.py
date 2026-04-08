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
    from app.core.database import SessionLocal

    log.info("Startup: use GET /api/v1/debug/init to create tables if first deploy")

    db = SessionLocal()
    try:
        # Try to seed agents and expire codes (will fail gracefully if tables don't exist yet)
        from app.core.security import hash_password
        from app.models.models import Agent
        from app.services.authorization_service import expire_stale_codes

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


@app.get("/api/v1/debug/init")
def debug_init():
    """Create reimbursement tables via raw SQL and seed agents."""
    from sqlalchemy import text

    from app.core.database import SessionLocal

    results = []
    db = SessionLocal()

    # All DDL in one go — raw SQL, no ORM dependency resolution
    ddl_statements = [
        # Enums
        "DO $$ BEGIN CREATE TYPE agent_role_enum AS ENUM ('call_center', 'claims_officer', 'admin'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;",
        "DO $$ BEGIN CREATE TYPE auth_code_status_enum AS ENUM ('active', 'used', 'expired'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;",
        "DO $$ BEGIN CREATE TYPE claim_status_enum AS ENUM ('submitted', 'under_review', 'pending_info', 'approved', 'rejected', 'payment_processing', 'paid'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;",
        # Agents
        """CREATE TABLE IF NOT EXISTS agents (
            agent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(200) NOT NULL,
            email VARCHAR(200) NOT NULL UNIQUE,
            hashed_password TEXT NOT NULL,
            role agent_role_enum NOT NULL DEFAULT 'call_center',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );""",
        # Authorization codes
        """CREATE TABLE IF NOT EXISTS authorization_codes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            code VARCHAR(20) NOT NULL UNIQUE,
            enrollee_id VARCHAR(50) NOT NULL,
            member_name VARCHAR(200) NOT NULL DEFAULT '',
            approved_amount NUMERIC(12,2) NOT NULL,
            visit_type VARCHAR(100) NOT NULL,
            notes TEXT,
            agent_id UUID NOT NULL REFERENCES agents(agent_id),
            agent_name VARCHAR(200) NOT NULL,
            status auth_code_status_enum DEFAULT 'active',
            linked_claim_id UUID,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            expires_at TIMESTAMPTZ NOT NULL
        );""",
        # Reimbursement claims
        """CREATE TABLE IF NOT EXISTS reimbursement_claims (
            claim_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            claim_ref VARCHAR(30) NOT NULL UNIQUE,
            authorization_code_id UUID NOT NULL REFERENCES authorization_codes(id),
            enrollee_id VARCHAR(50) NOT NULL,
            member_name VARCHAR(200) NOT NULL,
            member_phone VARCHAR(20) NOT NULL,
            hospital_name VARCHAR(300) NOT NULL,
            visit_date DATE NOT NULL,
            reason_for_visit TEXT NOT NULL,
            reimbursement_reason TEXT NOT NULL,
            claim_amount NUMERIC(12,2) NOT NULL,
            medications TEXT,
            lab_investigations TEXT,
            comments TEXT,
            bank_name VARCHAR(200) NOT NULL,
            account_number VARCHAR(20) NOT NULL,
            account_name VARCHAR(200) NOT NULL,
            status claim_status_enum DEFAULT 'submitted',
            approved_amount NUMERIC(12,2),
            reviewer_id UUID REFERENCES agents(agent_id),
            reviewer_notes TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );""",
        # Add FK from auth codes to claims (after claims table exists)
        """DO $$ BEGIN
            ALTER TABLE authorization_codes ADD CONSTRAINT fk_auth_linked_claim
            FOREIGN KEY (linked_claim_id) REFERENCES reimbursement_claims(claim_id);
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;""",
        # Service lines
        """CREATE TABLE IF NOT EXISTS claim_service_lines (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            claim_id UUID NOT NULL REFERENCES reimbursement_claims(claim_id) ON DELETE CASCADE,
            service_name VARCHAR(200) NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            unit_price NUMERIC(12,2) NOT NULL,
            total NUMERIC(12,2) NOT NULL
        );""",
        # Audit logs
        """CREATE TABLE IF NOT EXISTS claim_audit_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            entity_type VARCHAR(50) NOT NULL,
            entity_id UUID NOT NULL,
            action VARCHAR(100) NOT NULL,
            actor_type VARCHAR(20) NOT NULL,
            actor_id VARCHAR(100) NOT NULL,
            details JSONB,
            ip_address VARCHAR(45),
            created_at TIMESTAMPTZ DEFAULT NOW()
        );""",
        # Indexes
        "CREATE INDEX IF NOT EXISTS idx_auth_codes_code ON authorization_codes(code);",
        "CREATE INDEX IF NOT EXISTS idx_auth_codes_enrollee ON authorization_codes(enrollee_id);",
        "CREATE INDEX IF NOT EXISTS idx_auth_codes_status ON authorization_codes(status);",
        "CREATE INDEX IF NOT EXISTS idx_claims_ref ON reimbursement_claims(claim_ref);",
        "CREATE INDEX IF NOT EXISTS idx_claims_enrollee ON reimbursement_claims(enrollee_id);",
        "CREATE INDEX IF NOT EXISTS idx_claims_status ON reimbursement_claims(status);",
        "CREATE INDEX IF NOT EXISTS idx_audit_entity ON claim_audit_logs(entity_type, entity_id);",
    ]

    for sql in ddl_statements:
        try:
            db.execute(text(sql))
            db.commit()
        except Exception as e:
            db.rollback()
            results.append(f"DDL error: {str(e)[:100]}")

    results.append("Tables created")

    # Seed agents using raw SQL with pre-hashed passwords
    try:
        count = db.execute(text("SELECT count(*) FROM agents")).scalar()
        if count == 0:
            db.execute(text("""
                INSERT INTO agents (name, email, hashed_password, role) VALUES
                ('Call Center Agent', 'agent@leadwayhealth.com', '$2b$12$dnJw6gVpUDlicLCZutlikeKX7DN9HmHOYUMOM57ytnB1FKkpTkpea', 'call_center'),
                ('Claims Officer', 'claims@leadwayhealth.com', '$2b$12$Mj/NnyDwS97ExWNw9vyJ2uQUnUPI4twJIzAqCrr8wbKzZa8xEXvkC', 'claims_officer'),
                ('Admin User', 'admin@leadwayhealth.com', '$2b$12$nHLO4Xm1G7vpxYtwCDfbAur2Cmsxf.byKUkU6JzjyglQS/RuNlpPW', 'admin');
            """))
            db.commit()
            results.append("3 agents seeded")
        else:
            results.append(f"{count} agents already exist")
    except Exception as e:
        results.append(f"Seed error: {e}")
    finally:
        db.close()

    return {"success": True, "results": results}
