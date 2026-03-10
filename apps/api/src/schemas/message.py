from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.schemas.models import MessageDirection


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    direction: MessageDirection
    channel: str
    body: str
    provider_message_id: str | None
    created_at: datetime
