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
