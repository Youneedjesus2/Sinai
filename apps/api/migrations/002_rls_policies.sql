-- ============================================================
-- 002_rls_policies.sql — Row Level Security for multi-agency isolation
-- CLAUDE.md section 15: every data query MUST filter by agency_id.
-- This file adds a DB-level enforcement layer on top of the app-level
-- filtering that already exists in the repository pattern.
--
-- Usage:
--   This script is intended to be run in the Supabase SQL editor
--   AFTER 001_initial_schema.sql.
--
-- How it works:
--   - The FastAPI backend connects using the Postgres service role, which
--     bypasses RLS (Supabase default). Policies here protect data if the
--     database is accessed through lower-privileged roles (e.g., the anon
--     key, a future staff dashboard, or direct SQL by a restricted role).
--   - For each request, the app sets `app.current_agency_id` via
--     SET LOCAL before running queries when using a restricted role.
--   - The service role continues to bypass all policies.
-- ============================================================

-- ─────────────────────────────────────────────────────────────
-- Helper: create a restricted app role for future staff access
-- Skip if the role already exists.
-- ─────────────────────────────────────────────────────────────

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sinai_app') THEN
        CREATE ROLE sinai_app NOLOGIN;
    END IF;
END
$$;

GRANT USAGE ON SCHEMA public TO sinai_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sinai_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sinai_app;

-- ─────────────────────────────────────────────────────────────
-- leads — has agency_id directly
-- ─────────────────────────────────────────────────────────────

ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

-- Allow the service role (postgres) full access (bypasses RLS automatically).
-- This policy covers the sinai_app role and any authenticated Supabase users.
CREATE POLICY leads_agency_isolation ON leads
    AS PERMISSIVE
    FOR ALL
    TO sinai_app
    USING (
        agency_id = current_setting('app.current_agency_id', true)
    )
    WITH CHECK (
        agency_id = current_setting('app.current_agency_id', true)
    );

-- ─────────────────────────────────────────────────────────────
-- conversations — filtered through leads.agency_id
-- ─────────────────────────────────────────────────────────────

ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY conversations_agency_isolation ON conversations
    AS PERMISSIVE
    FOR ALL
    TO sinai_app
    USING (
        lead_id IN (
            SELECT id FROM leads
            WHERE agency_id = current_setting('app.current_agency_id', true)
        )
    );

-- ─────────────────────────────────────────────────────────────
-- messages — filtered through conversations → leads
-- ─────────────────────────────────────────────────────────────

ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY messages_agency_isolation ON messages
    AS PERMISSIVE
    FOR ALL
    TO sinai_app
    USING (
        conversation_id IN (
            SELECT c.id FROM conversations c
            INNER JOIN leads l ON l.id = c.lead_id
            WHERE l.agency_id = current_setting('app.current_agency_id', true)
        )
    );

-- ─────────────────────────────────────────────────────────────
-- appointments — filtered through leads.agency_id
-- ─────────────────────────────────────────────────────────────

ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;

CREATE POLICY appointments_agency_isolation ON appointments
    AS PERMISSIVE
    FOR ALL
    TO sinai_app
    USING (
        lead_id IN (
            SELECT id FROM leads
            WHERE agency_id = current_setting('app.current_agency_id', true)
        )
    );

-- ─────────────────────────────────────────────────────────────
-- summaries — filtered through leads.agency_id
-- ─────────────────────────────────────────────────────────────

ALTER TABLE summaries ENABLE ROW LEVEL SECURITY;

CREATE POLICY summaries_agency_isolation ON summaries
    AS PERMISSIVE
    FOR ALL
    TO sinai_app
    USING (
        lead_id IN (
            SELECT id FROM leads
            WHERE agency_id = current_setting('app.current_agency_id', true)
        )
    );

-- ─────────────────────────────────────────────────────────────
-- audit_events — filtered through leads.agency_id
-- ─────────────────────────────────────────────────────────────

ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY audit_events_agency_isolation ON audit_events
    AS PERMISSIVE
    FOR ALL
    TO sinai_app
    USING (
        lead_id IN (
            SELECT id FROM leads
            WHERE agency_id = current_setting('app.current_agency_id', true)
        )
    );

-- ─────────────────────────────────────────────────────────────
-- knowledge_vectors — shared across agencies (no RLS needed)
-- RAG documents are agency-scoped at the application layer via
-- document metadata, not via RLS.
-- ─────────────────────────────────────────────────────────────

-- (no RLS on knowledge_vectors)
