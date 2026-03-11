# Changelog

## Unreleased

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
