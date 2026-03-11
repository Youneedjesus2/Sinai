from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.repositories.lead_repository import LeadRepository
from src.repositories.schedule_repository import ScheduleRepository
from src.repositories.summary_repository import SummaryRepository
from src.schemas.lead import ConversationResponse, InboundLeadRequest, LeadResponse, SummaryResponse
from src.schemas.llm import OrchestratorResult
from src.schemas.scheduling import AppointmentResponse
from src.services.intake_service import IntakeService
from src.services.summary_service import SummaryService

router = APIRouter(prefix='/leads', tags=['leads'])


class IntakeResponse(LeadResponse):
    conversation: ConversationResponse
    orchestration: OrchestratorResult


@router.get('', response_model=list[LeadResponse])
def list_leads(agency_id: str = Query(...), db: Session = Depends(get_db)):
    return LeadRepository(db).list_for_agency(agency_id)


@router.get('/escalated', response_model=list[LeadResponse])
def list_escalated_leads(agency_id: str = Query(...), db: Session = Depends(get_db)):
    return LeadRepository(db).list_escalated_for_agency(agency_id)


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


@router.get('/{lead_id}/conversations', response_model=list[ConversationResponse])
def get_lead_conversations(lead_id: int, db: Session = Depends(get_db)):
    lead = LeadRepository(db).get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail='Lead not found')
    convs = LeadRepository(db).get_conversations_for_lead(lead_id)
    return [ConversationResponse.model_validate(c) for c in convs]


@router.get('/{lead_id}/appointments', response_model=list[AppointmentResponse])
def get_lead_appointments(lead_id: int, db: Session = Depends(get_db)):
    lead = LeadRepository(db).get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail='Lead not found')
    appts = ScheduleRepository(db).get_appointments_for_lead(lead_id)
    return [AppointmentResponse.model_validate(a) for a in appts]


@router.get('/{lead_id}/summary', response_model=SummaryResponse)
def get_lead_summary(lead_id: int, db: Session = Depends(get_db)):
    lead = LeadRepository(db).get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail='Lead not found')
    summary = SummaryRepository(db).get_for_lead(lead_id)
    if not summary:
        raise HTTPException(status_code=404, detail='No summary found for this lead')
    return SummaryResponse.model_validate(summary)


@router.post('/{lead_id}/summary', response_model=SummaryResponse)
def generate_summary(lead_id: int, db: Session = Depends(get_db)):
    try:
        summary = SummaryService(db).generate_summary(lead_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return SummaryResponse.model_validate(summary)
