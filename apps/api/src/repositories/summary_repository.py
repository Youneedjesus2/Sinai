from sqlalchemy import select
from sqlalchemy.orm import Session

from src.schemas.models import Summary


class SummaryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_summary(self, lead_id: int, summary_text: str, summary_json: dict) -> Summary:
        summary = Summary(
            lead_id=lead_id,
            summary_text=summary_text,
            summary_json=summary_json,
        )
        self.db.add(summary)
        self.db.flush()
        return summary

    def get_for_lead(self, lead_id: int) -> Summary | None:
        return self.db.scalars(
            select(Summary)
            .where(Summary.lead_id == lead_id)
            .order_by(Summary.created_at.desc())
        ).first()
