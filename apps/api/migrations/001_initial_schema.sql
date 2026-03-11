-- ============================================================
-- 001_initial_schema.sql — PostgreSQL schema for Sinai API
-- Replaces the SQLite schema with production-ready PostgreSQL.
-- Run this against Supabase SQL editor before first deploy.
-- ============================================================

-- Vector similarity search extension (required by LlamaIndex pgvector)
CREATE EXTENSION IF NOT EXISTS vector;

-- ─────────────────────────────────────────────────────────────
-- Native ENUM types
-- ─────────────────────────────────────────────────────────────

CREATE TYPE leadstatus AS ENUM ('new', 'engaged', 'qualified', 'closed');
CREATE TYPE conversationstate AS ENUM ('intake', 'awaiting_follow_up', 'escalated', 'completed');
CREATE TYPE messagedirection AS ENUM ('inbound', 'outbound');
CREATE TYPE appointmentstatus AS ENUM ('pending', 'confirmed', 'cancelled');

-- ─────────────────────────────────────────────────────────────
-- Core tables
-- ─────────────────────────────────────────────────────────────

CREATE TABLE leads (
    id          BIGSERIAL PRIMARY KEY,
    agency_id   TEXT NOT NULL,
    name        TEXT,
    phone       TEXT,
    email       TEXT,
    source_channel TEXT NOT NULL,
    status      leadstatus NOT NULL DEFAULT 'new',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE conversations (
    id              BIGSERIAL PRIMARY KEY,
    lead_id         BIGINT NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    current_state   conversationstate NOT NULL DEFAULT 'intake',
    last_message_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE messages (
    id                  BIGSERIAL PRIMARY KEY,
    conversation_id     BIGINT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    direction           messagedirection NOT NULL,
    channel             TEXT NOT NULL,
    body                TEXT NOT NULL,
    provider_message_id TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE appointments (
    id                BIGSERIAL PRIMARY KEY,
    lead_id           BIGINT NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    provider_event_id TEXT,
    start_time        TIMESTAMPTZ,
    end_time          TIMESTAMPTZ,
    status            appointmentstatus NOT NULL DEFAULT 'pending'
);

CREATE TABLE summaries (
    id           BIGSERIAL PRIMARY KEY,
    lead_id      BIGINT NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    summary_text TEXT NOT NULL,
    summary_json JSONB NOT NULL DEFAULT '{}',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE audit_events (
    id            BIGSERIAL PRIMARY KEY,
    lead_id       BIGINT NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    event_type    TEXT NOT NULL,
    event_payload JSONB NOT NULL DEFAULT '{}',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────
-- Indexes for common query patterns
-- ─────────────────────────────────────────────────────────────

CREATE INDEX idx_leads_agency_id ON leads(agency_id);
CREATE INDEX idx_conversations_lead_id ON conversations(lead_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_audit_events_lead_id ON audit_events(lead_id);
CREATE INDEX idx_messages_provider_id ON messages(provider_message_id) WHERE provider_message_id IS NOT NULL;
CREATE INDEX idx_appointments_lead_id ON appointments(lead_id);

-- ─────────────────────────────────────────────────────────────
-- LlamaIndex pgvector embeddings table
-- Schema matches LlamaIndex PGVectorStore expectations.
-- ─────────────────────────────────────────────────────────────

CREATE TABLE knowledge_vectors (
    id         TEXT PRIMARY KEY,
    text       TEXT NOT NULL,
    metadata_  JSONB NOT NULL DEFAULT '{}',
    node_id    TEXT,
    embedding  vector(1536)
);

CREATE INDEX idx_knowledge_vectors_embedding ON knowledge_vectors USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
