from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.repositories.lead_repository import LeadRepository
from src.schemas.lead import ConversationResponse, InboundLeadRequest, LeadResponse
from src.schemas.llm import OrchestratorResult
from src.services.intake_service import IntakeService

router = APIRouter(prefix='/leads', tags=['leads'])


class IntakeResponse(LeadResponse):
    conversation: ConversationResponse
    orchestration: OrchestratorResult


@router.post('/inbound', response_model=IntakeResponse)
def inbound_lead_intake(payload: InboundLeadRequest, db: Session = Depends(get_db)):
    lead, conversation, _inbound, _outbound, orchestration = IntakeService(db).process_inbound_lead(payload)
    return IntakeResponse(
        **LeadResponse.model_validate(lead).model_dump(),
        conversation=ConversationResponse.model_validate(conversation),
        orchestration=orchestration,
    )


@router.get('/{lead_id}', response_model=LeadResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = LeadRepository(db).get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail='Lead not found')
    return lead
