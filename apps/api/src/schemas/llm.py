from pydantic import BaseModel


class OrchestratorResult(BaseModel):
    detected_intent: str
    follow_up_needed: bool
    escalation_needed: bool
    suggested_next_reply: str


class RetrievalResult(BaseModel):
    context_chunks: list[str]
    confidence_score: float
    sources: list[str]
    context_found: bool


class IntakeFields(BaseModel):
    requested_service: str | None = None
    location: str | None = None
    preferred_schedule: str | None = None
    care_recipient: str | None = None


class SummaryOutput(BaseModel):
    lead_name: str | None = None
    requested_service: str | None = None
    location: str | None = None
    care_needs: str | None = None
    scheduled_time: str | None = None
    unresolved_questions: list[str] = []
    escalation_reasons: list[str] = []
    next_steps: str | None = None
