from pydantic import BaseModel


class OrchestratorResult(BaseModel):
    detected_intent: str
    follow_up_needed: bool
    escalation_needed: bool
    suggested_next_reply: str
