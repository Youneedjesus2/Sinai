from sqlalchemy import select
from sqlalchemy.orm import Session

from src.schemas.models import AuditEvent


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_event(self, lead_id: int, event_type: str, event_payload: dict) -> AuditEvent:
        event = AuditEvent(lead_id=lead_id, event_type=event_type, event_payload=event_payload)
        self.db.add(event)
        self.db.flush()
        return event

    def list_for_lead(self, lead_id: int) -> list[AuditEvent]:
        return list(self.db.scalars(select(AuditEvent).where(AuditEvent.lead_id == lead_id).order_by(AuditEvent.created_at.asc())))
