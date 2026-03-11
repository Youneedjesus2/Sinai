from sqlalchemy import select
from sqlalchemy.orm import Session

from src.schemas.models import Conversation, Lead


class LeadRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_lead(self, **kwargs) -> Lead:
        lead = Lead(**kwargs)
        self.db.add(lead)
        self.db.flush()
        return lead

    def get_lead(self, lead_id: int) -> Lead | None:
        return self.db.get(Lead, lead_id)

    def create_conversation(self, lead_id: int) -> Conversation:
        conversation = Conversation(lead_id=lead_id)
        self.db.add(conversation)
        self.db.flush()
        return conversation

    def get_conversations_for_lead(self, lead_id: int) -> list[Conversation]:
        return list(
            self.db.scalars(
                select(Conversation).where(Conversation.lead_id == lead_id)
            )
        )
