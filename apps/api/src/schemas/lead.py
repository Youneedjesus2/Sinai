from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.schemas.models import ConversationState, LeadStatus


class SummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    summary_text: str
    summary_json: dict
    created_at: datetime


class InboundLeadRequest(BaseModel):
    agency_id: str
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    source_channel: str
    message_body: str
    provider_message_id: str | None = None


class LeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agency_id: str
    name: str | None
    phone: str | None
    email: str | None
    source_channel: str
    status: LeadStatus
    created_at: datetime


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    current_state: ConversationState
    last_message_at: datetime
