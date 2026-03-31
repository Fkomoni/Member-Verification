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
