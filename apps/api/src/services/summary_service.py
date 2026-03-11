from sqlalchemy.orm import Session

from src.core.logging import get_logger
from src.core.prompts import load_prompt
from src.integrations.openai_client import OpenAIClient, OrchestratorError

logger = get_logger(__name__)
from src.repositories.audit_repository import AuditRepository
from src.repositories.lead_repository import LeadRepository
from src.repositories.message_repository import MessageRepository
from src.repositories.summary_repository import SummaryRepository
from src.schemas.llm import SummaryOutput
from src.schemas.models import Summary


class SummaryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.leads = LeadRepository(db)
        self.messages = MessageRepository(db)
        self.summaries = SummaryRepository(db)
        self.audits = AuditRepository(db)

    def generate_summary(self, lead_id: int) -> Summary:
        """Generate a staff summary from all conversation messages for the lead.

        Raises ValueError if lead does not exist.
        Raises OrchestratorError if the LLM call fails.
        """
        lead = self.leads.get_lead(lead_id)
        if lead is None:
            logger.warning('summary_lead_not_found', extra={'lead_id': lead_id})
            raise ValueError(f'Lead {lead_id} not found')

        logger.info('summary_generation_started', extra={'lead_id': lead_id})

        # 1. Build transcript from all conversations
        transcript = self._build_transcript(lead_id)

        # 2. Load prompt (never inline)
        system_prompt = load_prompt('tasks/generate_summary.md')

        # 3. Call LLM with structured output
        output: SummaryOutput = OpenAIClient().complete_structured(
            system_prompt=system_prompt,
            user_message=transcript,
            response_model=SummaryOutput,
        )

        # 4. Format summary_text from structured output
        summary_text = self._format_summary_text(output)

        # 5. Persist
        summary = self.summaries.create_summary(
            lead_id=lead_id,
            summary_text=summary_text,
            summary_json=output.model_dump(),
        )

        logger.info('summary_generated', extra={'lead_id': lead_id, 'summary_id': summary.id})

        # 6. Audit
        self.audits.create_event(
            lead_id=lead_id,
            event_type='summary_generated',
            event_payload={'summary_id': summary.id},
        )

        # 7. Commit and return
        self.db.commit()
        self.db.refresh(summary)
        return summary

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_transcript(self, lead_id: int) -> str:
        conversations = self.leads.get_conversations_for_lead(lead_id)
        lines: list[str] = []
        for conversation in conversations:
            msgs = self.messages.list_for_conversation(conversation.id)
            for msg in msgs:
                prefix = '[LEAD]' if msg.direction.value == 'inbound' else '[AGENT]'
                lines.append(f'{prefix} {msg.body}')
        return '\n'.join(lines) if lines else '(No messages recorded)'

    @staticmethod
    def _format_summary_text(output: SummaryOutput) -> str:
        unresolved = ', '.join(output.unresolved_questions) if output.unresolved_questions else 'None'
        escalation = ', '.join(output.escalation_reasons) if output.escalation_reasons else 'None'
        return (
            f'Lead Name: {output.lead_name or "Unknown"}\n'
            f'Requested Service: {output.requested_service or "Not specified"}\n'
            f'Location: {output.location or "Not specified"}\n'
            f'Care Needs: {output.care_needs or "Not specified"}\n'
            f'Scheduled Time: {output.scheduled_time or "Not scheduled"}\n'
            f'Unresolved Questions: {unresolved}\n'
            f'Escalation Reasons: {escalation}\n'
            f'Next Steps: {output.next_steps or "Not specified"}'
        )
