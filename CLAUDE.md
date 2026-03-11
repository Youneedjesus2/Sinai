# CLAUDE.md — Healthcare AI Lead Intake Agent

This file is the single source of truth for all Claude Code sessions on this project.
Read this file completely before writing any code, creating any file, or making any decision.
If something is not defined here, ask before assuming.

---

## 1. Project Identity

**Product:** Healthcare AI Lead Intake Agent

**Purpose:** Help healthcare agencies respond to inbound leads via SMS, email, and web forms — answering service questions from approved sources, collecting intake data, scheduling consultations, and handing off to human staff.

**This system is NOT:**
- A medical advisor
- A diagnostic tool
- A replacement for human consultation
- A general-purpose chatbot

**Core product rule:** If the system cannot answer using approved trusted context, it must say:

> "I don't have enough reliable information to answer that right now, but I can connect you with a team member."

This is a hard product constraint, not a suggestion.

---

## 2. Monorepo Structure

```
/
├── CLAUDE.md                         ← you are here
├── apps/
│   └── api/                          ← FastAPI backend (Python 3.11+)
│       ├── src/
│       │   ├── main.py
│       │   ├── api/routes/           ← HTTP route handlers only
│       │   ├── core/                 ← config, db, logging
│       │   ├── integrations/         ← external vendor clients
│       │   ├── repositories/         ← DB access only
│       │   ├── schemas/              ← Pydantic schemas + SQLAlchemy models
│       │   └── services/             ← business logic
│       └── tests/
├── apps/
│   └── web/                          ← Next.js 14 App Router dashboard (to be created)
├── prompts/                          ← versioned prompt files (to be created)
│   ├── system/
│   ├── tasks/
│   └── channels/
├── evals/                            ← evaluation datasets and scripts
├── knowledge/                        ← approved RAG source documents
├── healthcare-ai-lead-agent/         ← project docs
│   ├── docs/
│   ├── security/
│   └── evals/
└── Checklist.md
```

---

## 3. Tech Stack — Do Not Deviate

### Backend

| Layer | Tech |
|---|---|
| Framework | FastAPI 0.115+ |
| ORM | SQLAlchemy 2.0 (mapped_column style) |
| Validation | Pydantic v2 (model_validate, not .parse_obj) |
| Config | pydantic-settings with lru_cache |
| DB | SQLite for dev, Supabase/Postgres for production |
| Vector search | pgvector via SQLAlchemy |
| AI orchestration | OpenAI Responses API (gpt-4o) |
| RAG | LlamaIndex |
| SMS | Twilio |
| Email | SendGrid |
| Calendar | Google Calendar API |
| Observability | Phoenix (Arize) |
| Evals | Ragas |
| Server | Uvicorn |

### Frontend (when created)

| Layer | Tech |
|---|---|
| Framework | Next.js 14 App Router |
| Language | TypeScript |
| Styling | Tailwind CSS |
| Components | shadcn/ui |
| Data fetching | SWR |
| Auth | Supabase Auth |

---

## 4. Code Patterns — Follow Exactly

### 4.1 Repository Pattern

Repositories handle DB access only. No business logic.

```python
# CORRECT
class LeadRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_lead(self, **kwargs) -> Lead:
        lead = Lead(**kwargs)
        self.db.add(lead)
        self.db.flush()  # flush, not commit — commit happens in service layer
        return lead
```

**Rules:**
- Always `flush()` in repositories, never `commit()`
- `commit()` only happens at the end of a service method
- Always `refresh()` after commit for relationships

### 4.2 Service Layer

Services own business logic and transaction lifecycle.

```python
# CORRECT
class SomeService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SomeRepository(db)
        self.audits = AuditRepository(db)

    def do_thing(self, ...) -> ...:
        # 1. do work via repositories
        # 2. audit via self.audits.create_event()
        # 3. commit at the very end
        self.db.commit()
        self.db.refresh(result)
        return result
```

### 4.3 Route Handlers

Routes are thin. They call one service method and return the result.

```python
# CORRECT — routes do nothing except call service and return
@router.post('/leads/inbound', response_model=IntakeResponse)
def inbound_lead_intake(payload: InboundLeadRequest, db: Session = Depends(get_db)):
    lead, conversation, inbound, outbound, orchestration = IntakeService(db).process_inbound_lead(payload)
    return IntakeResponse(...)
```

### 4.4 Integration Clients

All external vendor calls go in `src/integrations/`. They are thin HTTP/SDK wrappers — no business logic.

```python
# CORRECT
class OpenAIClient:
    def __init__(self):
        self.client = OpenAI(api_key=get_settings().openai_api_key)

    def complete_structured(self, prompt: str, response_model: type) -> ...:
        ...
```

### 4.5 Pydantic Models

Always use Pydantic v2 patterns:
- `model_validate()` not `parse_obj()`
- `model_dump()` not `.dict()`
- `ConfigDict(from_attributes=True)` for ORM models
- Use `str | None` not `Optional[str]`

### 4.6 Enums

Use `str, Enum` pattern, always lowercase values:

```python
class LeadStatus(str, Enum):
    new = 'new'
    engaged = 'engaged'
```

---

## 5. Naming Conventions

| Type | Convention | Example |
|---|---|---|
| Files | snake_case | openai_client.py |
| Classes | PascalCase | OrchestratorService |
| Functions/methods | snake_case | process_inbound_message |
| Variables | snake_case | lead_id |
| Constants | SCREAMING_SNAKE | MAX_RETRIES = 3 |
| DB table names | plural snake_case | audit_events |
| Routes | kebab-case | /leads/inbound |
| Env vars | SCREAMING_SNAKE | OPENAI_API_KEY |

---

## 6. Environment Variables

All secrets go in `.env`. Never hardcode. Pattern:

```python
# In config.py — always add new env vars here
class Settings(BaseSettings):
    openai_api_key: str = Field(..., alias='OPENAI_API_KEY')
    twilio_account_sid: str = Field(..., alias='TWILIO_ACCOUNT_SID')
    twilio_auth_token: str = Field(..., alias='TWILIO_AUTH_TOKEN')
    sendgrid_api_key: str = Field(..., alias='SENDGRID_API_KEY')
    google_calendar_credentials_json: str = Field(..., alias='GOOGLE_CALENDAR_CREDENTIALS_JSON')
```

A `.env.example` file must always be updated when new vars are added.

---

## 7. Audit Logging — Required for Every State Change

Every meaningful system event MUST be logged via `AuditRepository.create_event()`.

**Required audit events:**
- `lead_created`
- `conversation_created`
- `inbound_message_received`
- `orchestration_completed`
- `outbound_reply_created`
- `retrieval_completed` — include `context_found: bool` and `confidence_score`
- `escalation_triggered` — include `reason`
- `appointment_booked`
- `appointment_rescheduled`
- `appointment_cancelled`
- `summary_generated`
- `external_service_failure` — include `vendor` and `error`

Never log raw message bodies. Log message IDs. Log event types and payloads with IDs only.

---

## 8. Safe Failure Rules

These are product rules enforced in code, not just prompts:

1. **No answer without approved context.** If retrieval returns empty or low confidence, the orchestrator must use the fallback path — not pass empty context to the LLM and hope.
2. **Structured output validation is mandatory.** All LLM responses must be validated against a Pydantic schema before they touch any business logic. If validation fails, use the fallback `OrchestratorResult`.
3. **No tool execution without server-side validation.** If the AI suggests booking an appointment, the scheduling service must validate availability server-side before creating the event. Never trust model tool call inputs directly.
4. **Escalation is always the safe path.** When in doubt, escalate. The cost of a false escalation is much lower than the cost of a wrong automated answer.
5. **Idempotency on webhooks.** Twilio and other providers may retry. Check `provider_message_id` before creating new messages.

---

## 9. Prompt Management Rules

Prompts live in `prompts/` directory, version-controlled.

**Structure:**
```
prompts/
  system/
    lead_intake_assistant.md      ← v1
  tasks/
    classify_intent.md
    extract_intake_fields.md
    generate_summary.md
    escalation_recommendation.md
  channels/
    sms_reply.md
    email_reply.md
```

Every prompt file has a metadata header:

```
---
prompt: classify_intent
version: v1
owner: backend
last_updated: 2026-03-11
---
```

Never inline prompts in Python code. Load them from files.

---

## 10. Test Rules

- Tests live in `apps/api/tests/`
- Use `pytest` with `TestClient` from FastAPI
- `conftest.py` handles DB setup/teardown (already exists — match this pattern)
- Every new service needs at minimum one integration test
- Every new route needs at minimum one happy-path test
- Eval tests for AI behavior go in `evals/` using Ragas, not pytest

---

## 11. What Already Exists (Do Not Re-create)

| File | Status |
|---|---|
| src/schemas/models.py | Complete — Lead, Conversation, Message, Appointment, Summary, AuditEvent |
| src/schemas/lead.py | Complete — InboundLeadRequest, LeadResponse, ConversationResponse |
| src/schemas/llm.py | Complete — OrchestratorResult |
| src/schemas/message.py | Complete — MessageResponse |
| src/repositories/lead_repository.py | Complete |
| src/repositories/message_repository.py | Complete |
| src/repositories/audit_repository.py | Complete |
| src/services/intake_service.py | Complete |
| src/services/orchestrator_service.py | Exists — rule-based stub, NEEDS replacement |
| src/api/routes/leads.py | Complete |
| src/api/routes/messages.py | Complete |
| src/api/routes/health.py | Complete |
| src/core/config.py | Complete — extend Settings class as needed |
| src/core/db.py | Complete |
| src/main.py | Complete |
| tests/conftest.py | Complete |
| tests/test_inbound_flow.py | Complete |
| tests/test_orchestrator_service.py | Complete |

---

## 12. What Needs to Be Built (Session Order)

Build in this order. Dependencies are sequential.

| Session | What to Build |
|---|---|
| Session 1 | `openai_client.py` → replace `orchestrator_service.py` with real LLM |
| Session 2 | `retrieval_service.py` (LlamaIndex + pgvector RAG pipeline) |
| Session 3 | `reply_service.py` + `prompts/` directory |
| Session 4 | `twilio_client.py` + inbound webhook route |
| Session 5 | `sendgrid_client.py` + email channel support |
| Session 6 | `calendar_client.py` + `scheduling_service.py` + `schedule_repository.py` |
| Session 7 | `summary_service.py` + summary route |
| Session 8 | `logging.py` (structured logging) + Phoenix tracing wrappers |
| Session 9 | Supabase/Postgres migration (swap DATABASE_URL, run migrations) |
| Session 10 | Next.js dashboard — leads list + conversation view |
| Session 11 | Next.js dashboard — scheduling + escalation views |
| Session 12 | Deployment config (Railway API + Vercel frontend + env setup) |

---

## 13. Definition of Done (Per Session)

A session is complete when:

- [ ] Code runs without errors
- [ ] At least one test covers the new behavior
- [ ] Audit events are logged where applicable
- [ ] Safe failure path exists
- [ ] `.env.example` updated if new vars added
- [ ] `CHANGELOG.md` updated with what was built
- [ ] No hardcoded secrets, IDs, or magic strings

---

## 14. Security Rules

- Secrets only via environment variables
- Never commit `.env` — it is in `.gitignore`
- Never log raw phone numbers or email addresses — log IDs
- PHI/PII must not appear in error messages
- All inbound webhook endpoints must validate signatures (Twilio, etc.)
- Row-level security will be enforced at Supabase level for multi-agency isolation

---

## 15. Multi-Agency Data Isolation

Every database query that touches user data MUST filter by `agency_id`.

```python
# CORRECT
def get_leads_for_agency(self, agency_id: str) -> list[Lead]:
    return list(self.db.scalars(
        select(Lead).where(Lead.agency_id == agency_id)
    ))

# WRONG — never do this
def get_all_leads(self) -> list[Lead]:
    return list(self.db.scalars(select(Lead)))
```

This is a security requirement, not a feature.

---

## 16. Forbidden Patterns

Never do these:

- `import *`
- Hardcoded API keys, URLs, or credentials anywhere in code
- Business logic in route handlers
- DB commits inside repositories
- Inline prompt strings in Python files
- Returning raw SQLAlchemy objects from routes (use Pydantic response models)
- Logging raw message bodies, phone numbers, or email addresses
- Answering lead questions without retrieval context

---

## 17. Key Docs to Reference

When building a specific component, read the relevant doc first:

| Building | Read first |
|---|---|
| RAG pipeline | healthcare-ai-lead-agent/docs/architecture.md sections C, D, E |
| Prompts | healthcare-ai-lead-agent/docs/prompts.md |
| Scheduling | healthcare-ai-lead-agent/docs/architecture.md section G |
| Security/secrets | healthcare-ai-lead-agent/security/secrets-policy.md |
| Evals | healthcare-ai-lead-agent/evals/README.md |
| Audit/logging | healthcare-ai-lead-agent/security/data-governance.md sections 9, 10 |
| Failure behavior | healthcare-ai-lead-agent/docs/architecture.md section "Failure Points" |
