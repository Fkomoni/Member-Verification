-- ============================================================
-- LeadwayHMO RxHub — PBM Member Self-Service Platform
-- PostgreSQL Database Schema
-- ============================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- MEMBERS (synced from PBM, read-only for app)
-- ============================================================
CREATE TABLE members (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id       VARCHAR(50) UNIQUE NOT NULL,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(255),
    phone           VARCHAR(20) NOT NULL,
    date_of_birth   DATE,
    gender          VARCHAR(10),
    diagnosis       TEXT,
    plan_type       VARCHAR(50),
    plan_name       VARCHAR(100),
    employer        VARCHAR(200),
    status          VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','INACTIVE','SUSPENDED')),
    pbm_synced_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_members_member_id ON members(member_id);
CREATE INDEX idx_members_phone ON members(phone);
CREATE INDEX idx_members_status ON members(status);

-- ============================================================
-- MEDICATIONS (synced from PBM per member)
-- ============================================================
CREATE TABLE medications (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id       VARCHAR(50) NOT NULL REFERENCES members(member_id) ON DELETE CASCADE,
    drug_name       VARCHAR(200) NOT NULL,
    generic_name    VARCHAR(200),
    dosage          VARCHAR(100) NOT NULL,
    frequency       VARCHAR(100) NOT NULL,
    route           VARCHAR(50),
    prescriber      VARCHAR(200),
    start_date      DATE,
    end_date        DATE,
    is_covered      BOOLEAN DEFAULT TRUE,
    coverage_pct    NUMERIC(5,2) DEFAULT 100.00,
    copay_amount    NUMERIC(10,2) DEFAULT 0.00,
    refill_count    INTEGER DEFAULT 0,
    max_refills     INTEGER DEFAULT 12,
    last_refill_at  TIMESTAMPTZ,
    next_refill_due DATE,
    days_supply     INTEGER DEFAULT 30,
    quantity         INTEGER,
    status          VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','DISCONTINUED','SUSPENDED','PENDING')),
    pbm_drug_id     VARCHAR(100),
    pbm_synced_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_medications_member ON medications(member_id);
CREATE INDEX idx_medications_status ON medications(status);
CREATE INDEX idx_medications_refill_due ON medications(next_refill_due);

-- ============================================================
-- CHANGE REQUESTS (core approval workflow)
-- ============================================================
CREATE TABLE requests (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id       VARCHAR(50) NOT NULL REFERENCES members(member_id) ON DELETE CASCADE,
    request_type    VARCHAR(30) NOT NULL CHECK (request_type IN ('PROFILE_UPDATE','MEDICATION_CHANGE','REFILL_ACTION')),
    action          VARCHAR(30) NOT NULL CHECK (action IN ('ADD','REMOVE','MODIFY','REFILL','SUSPEND_REFILL','RESUME_REFILL')),
    payload         JSONB NOT NULL DEFAULT '{}',
    comment         TEXT,
    attachment_url  TEXT,
    status          VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING','REVIEWED','APPROVED','REJECTED','MODIFIED')),
    admin_id        UUID,
    admin_comment   TEXT,
    reviewed_at     TIMESTAMPTZ,
    resolved_at     TIMESTAMPTZ,
    pbm_synced      BOOLEAN DEFAULT FALSE,
    pbm_sync_error  TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_requests_member ON requests(member_id);
CREATE INDEX idx_requests_status ON requests(status);
CREATE INDEX idx_requests_type ON requests(request_type);
CREATE INDEX idx_requests_created ON requests(created_at DESC);

-- ============================================================
-- REQUEST AUDIT LOGS
-- ============================================================
CREATE TABLE request_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id      UUID NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
    actor_type      VARCHAR(20) NOT NULL CHECK (actor_type IN ('MEMBER','ADMIN','SYSTEM')),
    actor_id        VARCHAR(100) NOT NULL,
    action          VARCHAR(50) NOT NULL,
    before_state    JSONB,
    after_state     JSONB,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_request_logs_request ON request_logs(request_id);
CREATE INDEX idx_request_logs_actor ON request_logs(actor_id);

-- ============================================================
-- ADMINS (portal users)
-- ============================================================
CREATE TABLE admins (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(200) NOT NULL,
    role            VARCHAR(20) DEFAULT 'AGENT' CHECK (role IN ('AGENT','SUPERVISOR','SUPER_ADMIN')),
    is_active       BOOLEAN DEFAULT TRUE,
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_admins_email ON admins(email);

-- ============================================================
-- RESOURCES (newsletters, health tips, drug alerts)
-- ============================================================
CREATE TABLE resources (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title           VARCHAR(300) NOT NULL,
    body            TEXT NOT NULL,
    category        VARCHAR(30) NOT NULL CHECK (category IN ('NEWSLETTER','HEALTH_TIP','DRUG_ALERT','SCARCITY_ALERT','PBM_UPDATE')),
    diagnosis_tags  TEXT[] DEFAULT '{}',
    thumbnail_url   TEXT,
    is_published    BOOLEAN DEFAULT FALSE,
    published_at    TIMESTAMPTZ,
    author_id       UUID REFERENCES admins(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_resources_category ON resources(category);
CREATE INDEX idx_resources_published ON resources(is_published, published_at DESC);
CREATE INDEX idx_resources_diagnosis ON resources USING GIN(diagnosis_tags);

-- ============================================================
-- OTP LOGS
-- ============================================================
CREATE TABLE otp_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id       VARCHAR(50) NOT NULL,
    phone           VARCHAR(20) NOT NULL,
    otp_hash        VARCHAR(255) NOT NULL,
    purpose         VARCHAR(20) DEFAULT 'LOGIN',
    attempts        INTEGER DEFAULT 0,
    max_attempts    INTEGER DEFAULT 3,
    is_used         BOOLEAN DEFAULT FALSE,
    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_otp_member ON otp_logs(member_id);
CREATE INDEX idx_otp_expires ON otp_logs(expires_at);

-- ============================================================
-- PAYMENTS
-- ============================================================
CREATE TABLE payments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id       VARCHAR(50) NOT NULL REFERENCES members(member_id) ON DELETE CASCADE,
    medication_id   UUID REFERENCES medications(id),
    amount          NUMERIC(12,2) NOT NULL,
    currency        VARCHAR(3) DEFAULT 'NGN',
    payment_type    VARCHAR(30) NOT NULL CHECK (payment_type IN ('UNCOVERED_MEDICATION','SUPPLEMENT','COPAY','TOP_UP')),
    gateway         VARCHAR(30) DEFAULT 'PAYSTACK',
    gateway_ref     VARCHAR(200),
    gateway_status  VARCHAR(30),
    status          VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING','PROCESSING','SUCCESS','FAILED','REFUNDED')),
    metadata        JSONB DEFAULT '{}',
    paid_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_payments_member ON payments(member_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_gateway_ref ON payments(gateway_ref);

-- ============================================================
-- NOTIFICATIONS
-- ============================================================
CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id       VARCHAR(50) NOT NULL REFERENCES members(member_id) ON DELETE CASCADE,
    title           VARCHAR(200) NOT NULL,
    body            TEXT NOT NULL,
    category        VARCHAR(30) DEFAULT 'GENERAL',
    is_read         BOOLEAN DEFAULT FALSE,
    action_url      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notifications_member ON notifications(member_id, is_read);
CREATE INDEX idx_notifications_created ON notifications(created_at DESC);

-- ============================================================
-- SYNC LOG (PBM integration tracking)
-- ============================================================
CREATE TABLE sync_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type     VARCHAR(30) NOT NULL,
    entity_id       VARCHAR(100) NOT NULL,
    direction       VARCHAR(10) NOT NULL CHECK (direction IN ('INBOUND','OUTBOUND')),
    endpoint        VARCHAR(300),
    request_body    JSONB,
    response_body   JSONB,
    status_code     INTEGER,
    success         BOOLEAN DEFAULT FALSE,
    error_message   TEXT,
    retry_count     INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sync_logs_entity ON sync_logs(entity_type, entity_id);
CREATE INDEX idx_sync_logs_success ON sync_logs(success);
CREATE INDEX idx_sync_logs_created ON sync_logs(created_at DESC);
