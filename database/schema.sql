-- ============================================================
-- Biometric Member Verification Portal - Database Schema
-- PostgreSQL
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enum types
CREATE TYPE verification_status_enum AS ENUM ('APPROVED', 'DENIED', 'PENDING');
CREATE TYPE match_status_enum AS ENUM ('MATCH', 'NO_MATCH', 'NEW_ENROLLMENT');

-- ============================================================
-- 1. Members
-- ============================================================
CREATE TABLE members (
    member_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enrollee_id     VARCHAR(50) NOT NULL UNIQUE,
    name            VARCHAR(200) NOT NULL,
    dob             DATE,
    gender          VARCHAR(10),
    nin             VARCHAR(20),
    biometric_registered BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_members_enrollee_id ON members(enrollee_id);
CREATE INDEX idx_members_nin ON members(nin) WHERE nin IS NOT NULL;

-- ============================================================
-- 2. Biometrics
-- ============================================================
CREATE TABLE biometrics (
    biometric_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id           UUID NOT NULL REFERENCES members(member_id) ON DELETE CASCADE,
    fingerprint_template BYTEA NOT NULL,  -- AES-encrypted template (NOT raw image)
    finger_position     VARCHAR(20) NOT NULL DEFAULT 'right_thumb',
    date_created        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_biometrics_member_id ON biometrics(member_id);

-- ============================================================
-- 3. Providers
-- ============================================================
CREATE TABLE providers (
    provider_id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                    VARCHAR(200) NOT NULL,
    email                   VARCHAR(200) NOT NULL UNIQUE,
    hashed_password         TEXT NOT NULL,
    prognosis_provider_id   VARCHAR(50) NOT NULL,  -- Provider ID in Prognosis system
    location                VARCHAR(300),
    device_id               VARCHAR(100),
    is_active               BOOLEAN DEFAULT TRUE,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_providers_email ON providers(email);

-- ============================================================
-- 4. Visits
-- ============================================================
CREATE TABLE visits (
    visit_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id           UUID NOT NULL REFERENCES members(member_id),
    provider_id         UUID NOT NULL REFERENCES providers(provider_id),
    verification_token  VARCHAR(500),
    verification_status verification_status_enum DEFAULT 'PENDING',
    timestamp           TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_visits_member_id ON visits(member_id);
CREATE INDEX idx_visits_provider_id ON visits(provider_id);
CREATE INDEX idx_visits_timestamp ON visits(timestamp);

-- ============================================================
-- 5. Verification Logs (Audit Trail)
-- ============================================================
CREATE TABLE verification_logs (
    log_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID NOT NULL REFERENCES members(member_id),
    provider_id UUID NOT NULL REFERENCES providers(provider_id),
    match_status match_status_enum NOT NULL,
    device_id   VARCHAR(100),
    timestamp   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_verification_logs_member_id ON verification_logs(member_id);
CREATE INDEX idx_verification_logs_provider_id ON verification_logs(provider_id);
CREATE INDEX idx_verification_logs_timestamp ON verification_logs(timestamp);

-- ============================================================
-- REIMBURSEMENT & AUTHORIZATION CONTROL SYSTEM
-- ============================================================

-- Enum types for reimbursement system
CREATE TYPE agent_role_enum AS ENUM ('call_center', 'claims_officer', 'admin');
CREATE TYPE auth_code_status_enum AS ENUM ('active', 'used', 'expired');
CREATE TYPE claim_status_enum AS ENUM (
    'submitted', 'under_review', 'pending_info',
    'approved', 'rejected', 'payment_processing', 'paid'
);

-- ============================================================
-- 6. Agents (Call Center, Claims Officers, Admins)
-- ============================================================
CREATE TABLE agents (
    agent_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(200) NOT NULL,
    email           VARCHAR(200) NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    role            agent_role_enum NOT NULL DEFAULT 'call_center',
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agents_email ON agents(email);
CREATE INDEX idx_agents_role ON agents(role);

-- ============================================================
-- 7. Authorization Codes
-- ============================================================
CREATE TABLE authorization_codes (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code            VARCHAR(20) NOT NULL UNIQUE,
    member_id       UUID NOT NULL REFERENCES members(member_id),
    enrollee_id     VARCHAR(50) NOT NULL,
    approved_amount NUMERIC(12, 2) NOT NULL,
    visit_type      VARCHAR(100) NOT NULL,
    notes           TEXT,
    agent_id        UUID NOT NULL REFERENCES agents(agent_id),
    agent_name      VARCHAR(200) NOT NULL,
    status          auth_code_status_enum DEFAULT 'active',
    linked_claim_id UUID,  -- FK added after claims table
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_auth_codes_code ON authorization_codes(code);
CREATE INDEX idx_auth_codes_enrollee_id ON authorization_codes(enrollee_id);
CREATE INDEX idx_auth_codes_status ON authorization_codes(status);
CREATE INDEX idx_auth_codes_agent_id ON authorization_codes(agent_id);

-- ============================================================
-- 8. Reimbursement Claims
-- ============================================================
CREATE TABLE reimbursement_claims (
    claim_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_ref           VARCHAR(30) NOT NULL UNIQUE,
    authorization_code_id UUID NOT NULL REFERENCES authorization_codes(id),
    member_id           UUID NOT NULL REFERENCES members(member_id),
    enrollee_id         VARCHAR(50) NOT NULL,
    member_name         VARCHAR(200) NOT NULL,
    member_phone        VARCHAR(20) NOT NULL,
    hospital_name       VARCHAR(300) NOT NULL,
    visit_date          DATE NOT NULL,
    reason_for_visit    TEXT NOT NULL,
    reimbursement_reason TEXT NOT NULL,
    claim_amount        NUMERIC(12, 2) NOT NULL,
    medications         TEXT,
    lab_investigations  TEXT,
    comments            TEXT,
    bank_name           VARCHAR(200) NOT NULL,
    account_number      VARCHAR(20) NOT NULL,
    account_name        VARCHAR(200) NOT NULL,
    status              claim_status_enum DEFAULT 'submitted',
    approved_amount     NUMERIC(12, 2),
    reviewer_id         UUID REFERENCES agents(agent_id),
    reviewer_notes      TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_claims_claim_ref ON reimbursement_claims(claim_ref);
CREATE INDEX idx_claims_enrollee_id ON reimbursement_claims(enrollee_id);
CREATE INDEX idx_claims_status ON reimbursement_claims(status);
CREATE INDEX idx_claims_authorization_code ON reimbursement_claims(authorization_code_id);

-- Add FK from authorization_codes → reimbursement_claims
ALTER TABLE authorization_codes
    ADD CONSTRAINT fk_auth_code_linked_claim
    FOREIGN KEY (linked_claim_id) REFERENCES reimbursement_claims(claim_id);

-- ============================================================
-- 9. Claim Service Lines
-- ============================================================
CREATE TABLE claim_service_lines (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id    UUID NOT NULL REFERENCES reimbursement_claims(claim_id) ON DELETE CASCADE,
    service_name VARCHAR(200) NOT NULL,
    quantity    INTEGER NOT NULL DEFAULT 1,
    unit_price  NUMERIC(12, 2) NOT NULL,
    total       NUMERIC(12, 2) NOT NULL
);

CREATE INDEX idx_service_lines_claim_id ON claim_service_lines(claim_id);

-- ============================================================
-- 10. Claim Audit Logs
-- ============================================================
CREATE TABLE claim_audit_logs (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL,
    entity_id   UUID NOT NULL,
    action      VARCHAR(100) NOT NULL,
    actor_type  VARCHAR(20) NOT NULL,
    actor_id    VARCHAR(100) NOT NULL,
    details     JSONB,
    ip_address  VARCHAR(45),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_entity ON claim_audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_created_at ON claim_audit_logs(created_at);
