from sqlalchemy import select
from sqlalchemy.orm import Session

from src.schemas.models import Conversation, ConversationState, Lead


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

    def list_for_agency(self, agency_id: str) -> list[Lead]:
        return list(
            self.db.scalars(
                select(Lead)
                .where(Lead.agency_id == agency_id)
                .order_by(Lead.created_at.desc())
            )
        )

    def list_escalated_for_agency(self, agency_id: str) -> list[Lead]:
        """Return leads that have at least one conversation in the 'escalated' state."""
        return list(
            self.db.scalars(
                select(Lead)
                .join(Conversation, Conversation.lead_id == Lead.id)
                .where(
                    Lead.agency_id == agency_id,
                    Conversation.current_state == ConversationState.escalated,
                )
                .order_by(Lead.created_at.desc())
                .distinct()
            )
        )

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
