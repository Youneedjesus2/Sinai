from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.schemas.models import Conversation, Message, MessageDirection


class MessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_message(
        self,
        conversation_id: int,
        direction: MessageDirection,
        channel: str,
        body: str,
        provider_message_id: str | None = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            direction=direction,
            channel=channel,
            body=body,
            provider_message_id=provider_message_id,
        )
        self.db.add(message)
        conversation = self.db.get(Conversation, conversation_id)
        if conversation:
            conversation.last_message_at = datetime.utcnow()
        self.db.flush()
        return message

    def find_by_provider_id(self, provider_message_id: str) -> Message | None:
        return self.db.scalars(
            select(Message).where(Message.provider_message_id == provider_message_id)
        ).first()

    def list_for_conversation(self, conversation_id: int) -> list[Message]:
        return list(self.db.scalars(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())))
