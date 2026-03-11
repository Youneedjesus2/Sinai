# Changelog

## Unreleased

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
