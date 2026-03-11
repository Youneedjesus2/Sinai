# Changelog

## Unreleased

## 3/11/2026 — Session 9: Postgres Migration + Production Config
### Added
- `migrations/001_initial_schema.sql` — rewritten for PostgreSQL: `BIGSERIAL` PKs, `TIMESTAMPTZ`, `JSONB`, native ENUM types (`leadstatus`, `conversationstate`, `messagedirection`, `appointmentstatus`), `ON DELETE CASCADE` on all FK refs, required indexes on all foreign keys + `agency_id`, partial index on `messages.provider_message_id`, `pgvector` extension, `knowledge_vectors` table for LlamaIndex with `ivfflat` cosine index
- `migrations/002_rls_policies.sql` — Row Level Security on all six data tables; creates `sinai_app` restricted role; policies filter through `agency_id` via `current_setting('app.current_agency_id', true)`; service role bypasses RLS (Supabase default); `knowledge_vectors` excluded (shared across agencies)
- `alembic.ini` — Alembic config; URL placeholder overridden by `DATABASE_URL` env var at runtime
- `alembic/env.py` — reads `DATABASE_URL` from env; sets `APP_ENV` and `OPENAI_API_KEY` defaults so settings don't fail during migration runs; imports `Base.metadata` for autogenerate support
- `alembic/script.py.mako` — standard Alembic revision template
- `alembic/versions/2026_03_11_0001_initial_schema.py` — Alembic-managed version of the Postgres schema (equivalent to 001_initial_schema.sql); full `upgrade()` and `downgrade()`
- `apps/api/Dockerfile` — Python 3.11-slim; installs `libpq-dev` for psycopg2; installs deps via `pyproject.toml`; copies `src/`, `alembic/`, `prompts/`; exposes port 8000; `HEALTHCHECK` on `/health`; starts with `uvicorn`
- `apps/api/.dockerignore` — excludes `.env`, `__pycache__`, `*.pyc`, `tests/`, `.pytest_cache/`, `.venv/`
- `railway.json` — Railway deployment config at repo root; builds from `apps/api/Dockerfile`; `startCommand` runs `alembic upgrade head` before uvicorn; healthcheck on `/health`

### Changed
- `src/core/config.py` — added `supabase_url: str | None` and `supabase_anon_key: str | None` (both optional, for future Supabase Auth integrations)
- `pyproject.toml` — added `alembic>=1.13.0` and `psycopg2-binary>=2.9.0`
- `.env.example` — updated `DATABASE_URL` to show Postgres connection string format; added `SUPABASE_URL` and `SUPABASE_ANON_KEY`

### Notes
- App code requires **no changes** to swap from SQLite to Postgres — only `DATABASE_URL` changes
- Tests continue to run against SQLite via `Base.metadata.create_all()` in `conftest.py` (unaffected by Alembic)
- `alembic upgrade head` is idempotent; safe to run on every deploy

## 3/11/2026 — Session 8: Structured Logging + Phoenix Observability
### Added
- `src/core/logging.py` — `get_logger(name)`: configures root logger with `_JsonFormatter` on first call; emits single-line JSON `{"timestamp", "level", "name", "message", "extra"}` to stdout; log level from `LOG_LEVEL` env var; no PII in any log call per data-governance.md §9
- `src/core/app.py` — `setup_phoenix_tracing()`: initializes OpenTelemetry TracerProvider via `arize-phoenix-otel`; registers `OpenAIInstrumentor` for LLM span capture; skips silently if `PHOENIX_COLLECTOR_ENDPOINT` is not set; catches `ImportError` gracefully so missing packages don't crash startup
- `tests/test_logging.py` — 8 tests: `get_logger` returns Logger, same-name caching, JSON format validation, extra-field capture, exception traceback capture, IntakeService logging, OrchestratorService logging, `setup_phoenix_tracing` no-op safety

### Changed
- `src/core/config.py` — added `log_level: str = 'INFO'` and `phoenix_collector_endpoint: str | None = None`
- `src/main.py` — calls `setup_phoenix_tracing()` at FastAPI startup before table creation
- `src/core/startup.py` — switched from `logging.getLogger` to `get_logger`
- `src/services/intake_service.py` — structured log at each step with IDs only, no message bodies
- `src/services/orchestrator_service.py` — logs `detected_intent` + `escalation_needed` on all paths
- `src/services/retrieval_service.py` — logs `context_found` + `confidence_score`
- `src/services/scheduling_service.py` — logs booking attempts, conflicts, outcomes
- `src/services/summary_service.py` — logs summary generation start and completion
- `src/integrations/openai_client.py` — switched to `get_logger`; logs success/failure with vendor tag
- `src/integrations/sendgrid_client.py` — switched to `get_logger`; structured log keys
- `src/integrations/ringcentral_client.py` — switched to `get_logger`; fixed PII leak (phone number removed from logs; logs message ID only)
- `src/integrations/calendar_client.py` — switched from `logging.getLogger` to `get_logger`
- `pyproject.toml` — added `arize-phoenix-otel>=0.3.0` and `openinference-instrumentation-openai>=0.1.0`
- `.env.example` — added `LOG_LEVEL=INFO` and `PHOENIX_COLLECTOR_ENDPOINT=`

## 3/11/2026 — Session 7: Conversation Summary Service
### Added
- `SummaryOutput` Pydantic model added to `src/schemas/llm.py` — structured LLM output with `lead_name`, `requested_service`, `location`, `care_needs`, `scheduled_time`, `unresolved_questions`, `escalation_reasons`, `next_steps`
- `SummaryResponse` Pydantic model added to `src/schemas/lead.py` — `id`, `lead_id`, `summary_text`, `summary_json`, `created_at` with `from_attributes=True`
- `src/repositories/summary_repository.py` — `SummaryRepository.create_summary(lead_id, summary_text, summary_json)`; follows flush-in-repo pattern
- `src/services/summary_service.py` — `SummaryService.generate_summary(lead_id)`: loads all conversations + messages → builds `[LEAD]`/`[AGENT]` transcript → loads `prompts/tasks/generate_summary.md` → calls `OpenAIClient.complete_structured(SummaryOutput)` → formats `summary_text` → creates `Summary` record → audits `summary_generated` → commit
- `src/api/routes/leads.py` — `POST /leads/{lead_id}/summary`; returns `SummaryResponse`; 404 if lead not found
- `src/repositories/lead_repository.py` — added `get_conversations_for_lead(lead_id)` method
- `tests/test_summary_service.py` — 5 tests: service creates record + audit, 404 for unknown lead, transcript includes all messages, route happy path, route 404

### Changed
- `src/schemas/llm.py` — added `SummaryOutput` model
- `src/schemas/lead.py` — added `SummaryResponse` model

## 3/11/2026 — Session 6: Google Calendar Scheduling Pipeline
### Added
- `src/schemas/scheduling.py` — `TimeSlot` dataclass (`start`, `end`, `available`); `CalendarBookingError` and `SchedulingConflictError` exceptions; `BookConsultationRequest`, `RescheduleRequest`, `TimeSlotResponse`, `AppointmentResponse` Pydantic schemas
- `src/integrations/calendar_client.py` — `GoogleCalendarClient` with lazy Google SDK imports; `get_available_slots()` generates 9am–5pm UTC business-hour slots and marks each with availability from Calendar API; `create_event()` does a server-side overlap check before creating (raises `CalendarBookingError` if taken); `cancel_event()` deletes the Calendar event
- `src/repositories/schedule_repository.py` — `ScheduleRepository` with `create_appointment`, `get_appointment`, `get_appointments_for_lead`, `update_appointment_status`, `check_overlap` (queries only `confirmed` appointments); follows flush-in-repo / commit-in-service pattern
- `src/services/scheduling_service.py` — `SchedulingService` with `get_available_slots`, `book_consultation` (local overlap check → Calendar create → DB create → audit `appointment_booked` → commit), `cancel_consultation` (Calendar cancel → DB update → audit `appointment_cancelled`), `reschedule_consultation` (conflict check → cancel old → Calendar create new → DB create new → audit `appointment_rescheduled`)
- `src/api/routes/scheduling.py` — `GET /scheduling/slots`, `POST /scheduling/book` (409 on conflict), `POST /scheduling/{id}/cancel` (404 if not found), `POST /scheduling/{id}/reschedule` (404/409)
- `tests/test_scheduling_service.py` — 5 service-layer tests: booking creates appointment + audit, overlap raises `SchedulingConflictError`, cancellation sets status to `cancelled` + audit, 404 on missing appointment, reschedule creates new appointment + audit
- `google-api-python-client>=2.0.0` and `google-auth>=2.0.0` added to `pyproject.toml`
- `GOOGLE_CALENDAR_CREDENTIALS_JSON=` and `GOOGLE_CALENDAR_ID=` added to `.env.example`

### Changed
- `src/core/config.py` — added `google_calendar_credentials_json` and `google_calendar_id` (both optional with empty-string defaults)
- `src/main.py` — registers `scheduling_router`

## 3/11/2026 — Session 5: SendGrid Email Integration (Inbound Webhook + Outbound Sending)
### Added
- `src/integrations/sendgrid_client.py` — `SendGridClient` with lazy SendGrid SDK import; `send_email(to, from_, subject, body) -> bool` returns `True` on 2xx response, `False` on failure; logs via Python logger (never logs email addresses)
- `src/api/routes/email_webhook.py` — `POST /webhooks/email/inbound`; parses SendGrid Inbound Parse multipart/form-data (`from`, `subject`, `text`, `headers`); extracts sender email and name from `From` header; extracts `Message-ID` from raw headers for idempotency; calls `IntakeService`; sends reply via `SendGridClient.send_email` with subject `'Re: Your inquiry — Care Team'`; audits `external_service_failure` if send fails
- `tests/test_email_webhook.py` — 4 tests: happy-path intake + send, duplicate Message-ID idempotency, send failure audits `external_service_failure`, sender name extracted and passed to intake
- Two `SENDGRID_*` vars added to `.env.example`
- `sendgrid>=6.0.0` added to `pyproject.toml`

### Changed
- `src/core/config.py` — added `sendgrid_api_key` and `sendgrid_from_email` settings (both optional with empty-string defaults)
- `src/main.py` — registers `email_router` at app startup
- `src/services/reply_service.py` — `render_reply` now accepts optional `name: str | None = None`; `_format_email` uses `'Hi {name},'` when name is provided, `'Hi there,'` otherwise; sign-off updated to `'Best regards,\nCare Team'`
- `tests/test_reply_service.py` — updated greeting assertion from `'Hello,'` to `'Hi there,'`; added `test_email_reply_uses_name_when_provided`

## 3/11/2026 — Session 4: RingCentral SMS Integration (Inbound Webhook + Outbound Sending)
### Added
- `src/integrations/ringcentral_client.py` — `RingCentralClient` with JWT server-to-server auth; `send_sms(to, body)` returns RingCentral message ID or `None` on failure; `register_webhook_subscription(webhook_url)` creates a 7-day subscription with verification token; `renew_subscription(subscription_id)` refreshes an existing subscription
- `src/api/routes/sms.py` — `POST /webhooks/sms/inbound`; handles RingCentral URL validation handshake (echoes `Validation-Token`); validates `Verification-Token` header (403 on mismatch); ignores Outbound-direction messages; checks `provider_message_id` for idempotency before running intake; calls `IntakeService` then `RingCentralClient.send_sms`; audits `external_service_failure` if send fails
- `src/core/startup.py` — `register_ringcentral_webhook()` (no-ops if `RINGCENTRAL_CLIENT_ID` empty; reuses `RINGCENTRAL_SUBSCRIPTION_ID` if set; else registers new subscription and logs ID for operator); `schedule_subscription_renewal()` uses APScheduler `BackgroundScheduler` to renew 6 days after startup; `shutdown_scheduler()` for clean app shutdown
- `ringcentral>=0.7.0` and `apscheduler>=3.10.0` added to `pyproject.toml`
- `tests/test_sms_webhook.py` — 6 tests: validation handshake, wrong verification token (403), outbound direction ignored, duplicate message ID idempotency, happy-path intake + send, `send_sms` failure audits `external_service_failure`
- Six `RINGCENTRAL_*` vars added to `.env.example`

### Changed
- `src/main.py` — wires `sms_router`; startup event calls `register_ringcentral_webhook()` and `schedule_subscription_renewal()`; shutdown event calls `shutdown_scheduler()`
- `src/repositories/message_repository.py` — added `find_by_provider_id(provider_message_id) -> Message | None` for webhook idempotency
- `src/core/config.py` — added 7 RingCentral settings fields (all with safe empty-string or `None` defaults so tests and unconfigured deployments work without them)
- `tests/conftest.py` — added `RINGCENTRAL_WEBHOOK_VERIFICATION_TOKEN=test-verification-token` env var

## 3/11/2026 — Session 3: Reply Rendering Service + Prompt Library
### Added
- `prompts/system/lead_intake_assistant.md` — v1 system prompt defining role, allowed scope, hard restrictions (no medical advice, no diagnoses), safe fallback rule, and tone guidance
- `prompts/tasks/extract_intake_fields.md` — v1 task prompt for extracting `requested_service`, `location`, `preferred_schedule`, `care_recipient` as structured JSON matching `IntakeFields`
- `prompts/tasks/generate_summary.md` — v1 task prompt for generating staff summaries from full conversation history; returns structured JSON with `lead_name`, `requested_service`, `care_needs`, `scheduled_time`, `unresolved_questions`, `escalation_reasons`, `next_steps`
- `prompts/channels/sms_reply.md` — v1 formatting rules: 160-char max, plain text, conversational, no markdown, no formal greetings
- `prompts/channels/email_reply.md` — v1 formatting rules: greeting, professional tone, plain text, paragraph structure, warm closing
- `src/core/prompts.py` — `load_prompt(path: str) -> str` utility that resolves paths relative to project-level `prompts/` directory; raises `FileNotFoundError` with helpful message if file is missing
- `IntakeFields` Pydantic model added to `src/schemas/llm.py` with nullable `requested_service`, `location`, `preferred_schedule`, `care_recipient` fields
- `src/services/reply_service.py` — `ReplyService.render_reply(orchestration, channel)`; loads channel prompt via `load_prompt`; formats SMS (≤160 chars, sentence-boundary truncation) and email (greeting + closing); unknown channels fall back to SMS
- `tests/test_reply_service.py` — 8 tests covering SMS short/long/boundary truncation, unknown channel fallback, email greeting/closing, email length preservation, `load_prompt` error and success cases

### Changed
- `src/services/intake_service.py` — replaces direct `result.suggested_next_reply` with `ReplyService().render_reply(result, channel)` for channel-appropriate outbound message formatting

## 3/11/2026 — Session 2: RAG Retrieval Pipeline (LlamaIndex + pgvector)
### Added
- `src/integrations/vector_store.py` — `VectorStoreClient` with `get_or_create_index()` and `query()`; uses `PGVectorStore` for PostgreSQL and LlamaIndex's default in-memory store for SQLite dev; lazy imports to avoid hard runtime dependency
- `src/services/retrieval_service.py` — `RetrievalService.retrieve()` loads documents from `knowledge/`, queries the index, computes average confidence score, returns `RetrievalResult`; safe failure returns `context_found=False` on any exception
- `RetrievalResult` Pydantic model added to `src/schemas/llm.py` with `context_chunks`, `confidence_score`, `sources`, and `context_found` fields
- `knowledge/README.md` — explains approved RAG source policy and how to add documents
- `knowledge/sample-services.md` — placeholder service descriptions for dev/test retrieval
- `llama-index>=0.10.0` and `pgvector>=0.2.0` added to `pyproject.toml`
- `tests/test_retrieval_service.py` — 4 tests covering high confidence, low confidence, empty results, and exception fallback

### Changed
- `src/services/orchestrator_service.py` — accepts optional `retrieval_result: RetrievalResult | None`; if `context_found=False`, escalates immediately without calling LLM (safe failure rule); if `context_found=True`, injects approved context into system prompt
- `src/services/intake_service.py` — added retrieval step between inbound message receipt and orchestration; emits `retrieval_completed` audit event with `context_found` and `confidence_score`
- `tests/test_orchestrator_service.py` — added tests for low-confidence escalation path and context injection path
- `tests/test_inbound_flow.py` — mocks `RetrievalService`, updates expected audit count from 5 to 6, includes `retrieval_completed` in expected audit events

## 3/11/2026 — Session 1: OpenAI Structured Output Orchestrator
### Added
- `src/integrations/openai_client.py` — `OpenAIClient` with `complete_structured()` using OpenAI gpt-4o structured outputs via `beta.chat.completions.parse`; raises `OrchestratorError` on failure
- `prompts/tasks/classify_intent.md` — versioned prompt instructing the model to classify intent into one of five categories, apply escalation rules for emergency keywords and clinical questions, and return a reply matching the `OrchestratorResult` schema
- `openai>=1.0.0` added to `pyproject.toml` dependencies
- `OPENAI_API_KEY` added to `src/core/config.py` Settings and `.env.example`

### Changed
- `src/services/orchestrator_service.py` — replaced rule-based keyword stub with real LLM call; loads prompt from `prompts/tasks/classify_intent.md`; falls back to safe `fallback` result on any exception
- `tests/test_orchestrator_service.py` — rewritten to mock OpenAI SDK; covers appointment intent happy path and exception fallback path
- `tests/test_inbound_flow.py` — updated to mock OpenAI client so end-to-end happy-path test remains deterministic
- `tests/conftest.py` — added `OPENAI_API_KEY=test-key` env var for test Settings initialization

## 3/10/2026
### Added
- Built a minimal FastAPI backend happy-path for inbound lead intake with route, service, repository, and schema separation.
- Added normalized data models and persistence for leads, conversations, messages, appointments, summaries, and audit events.
- Implemented a rule-based orchestrator v1 that returns validated structured next-action output.
- Added audit logging for lead creation, conversation creation, inbound message receipt, orchestration completion, and outbound reply creation.
- Added initial SQL migration for core tables and basic unit/integration tests for orchestrator and end-to-end intake flow.
