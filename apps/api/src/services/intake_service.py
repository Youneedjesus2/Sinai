from sqlalchemy.orm import Session

from src.core.logging import get_logger
from src.repositories.audit_repository import AuditRepository
from src.repositories.lead_repository import LeadRepository
from src.repositories.message_repository import MessageRepository
from src.schemas.lead import InboundLeadRequest
from src.schemas.llm import OrchestratorResult
from src.schemas.models import ConversationState, LeadStatus, MessageDirection
from src.services.orchestrator_service import OrchestratorService
from src.services.reply_service import ReplyService
from src.services.retrieval_service import RetrievalService

logger = get_logger(__name__)


class IntakeService:
    def __init__(self, db: Session):
        self.db = db
        self.leads = LeadRepository(db)
        self.messages = MessageRepository(db)
        self.audits = AuditRepository(db)

    def _audit(self, lead_id: int, event_type: str, payload: dict) -> None:
        self.audits.create_event(lead_id=lead_id, event_type=event_type, event_payload=payload)

    def process_inbound_lead(self, request: InboundLeadRequest) -> tuple:
        lead = self.leads.create_lead(
            agency_id=request.agency_id,
            name=request.name,
            phone=request.phone,
            email=request.email,
            source_channel=request.source_channel,
            status=LeadStatus.new,
        )
        self._audit(lead.id, 'lead_created', {'agency_id': lead.agency_id, 'source_channel': lead.source_channel})
        logger.info('lead_created', extra={'lead_id': lead.id, 'agency_id': lead.agency_id, 'source_channel': lead.source_channel})

        conversation = self.leads.create_conversation(lead_id=lead.id)
        self._audit(conversation.lead_id, 'conversation_created', {'conversation_id': conversation.id, 'state': conversation.current_state.value})
        logger.info('conversation_created', extra={'lead_id': lead.id, 'conversation_id': conversation.id})

        inbound = self.messages.create_message(
            conversation_id=conversation.id,
            direction=MessageDirection.inbound,
            channel=request.source_channel,
            body=request.message_body,
            provider_message_id=request.provider_message_id,
        )
        self._audit(lead.id, 'inbound_message_received', {'message_id': inbound.id, 'channel': inbound.channel})
        logger.info('inbound_message_received', extra={'lead_id': lead.id, 'message_id': inbound.id, 'channel': inbound.channel})

        retrieval_result = RetrievalService().retrieve(request.message_body, request.agency_id)
        self._audit(lead.id, 'retrieval_completed', {
            'context_found': retrieval_result.context_found,
            'confidence_score': retrieval_result.confidence_score,
        })
        logger.info('retrieval_completed', extra={'lead_id': lead.id, 'context_found': retrieval_result.context_found, 'confidence_score': retrieval_result.confidence_score})

        result: OrchestratorResult = OrchestratorService.process_inbound_message(
            request.message_body, retrieval_result
        )
        self._audit(lead.id, 'orchestration_completed', result.model_dump())
        logger.info('orchestration_completed', extra={'lead_id': lead.id, 'detected_intent': result.detected_intent, 'escalation_needed': result.escalation_needed})

        if result.escalation_needed:
            conversation.current_state = ConversationState.escalated
        elif result.follow_up_needed:
            conversation.current_state = ConversationState.awaiting_follow_up
        else:
            conversation.current_state = ConversationState.completed

        rendered_reply = ReplyService().render_reply(result, request.source_channel)
        outbound = self.messages.create_message(
            conversation_id=conversation.id,
            direction=MessageDirection.outbound,
            channel=request.source_channel,
            body=rendered_reply,
        )
        self._audit(lead.id, 'outbound_reply_created', {'message_id': outbound.id, 'intent': result.detected_intent})
        logger.info('outbound_reply_created', extra={'lead_id': lead.id, 'message_id': outbound.id, 'intent': result.detected_intent})

        lead.status = LeadStatus.engaged
        self.db.commit()
        self.db.refresh(lead)
        self.db.refresh(conversation)
        return lead, conversation, inbound, outbound, result
