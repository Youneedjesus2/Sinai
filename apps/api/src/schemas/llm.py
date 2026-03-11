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
