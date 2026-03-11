# Changelog

## Unreleased

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
