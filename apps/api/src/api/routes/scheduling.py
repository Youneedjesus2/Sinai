from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.schemas.scheduling import (
    AppointmentResponse,
    BookConsultationRequest,
    RescheduleRequest,
    SchedulingConflictError,
    TimeSlotResponse,
)
from src.services.scheduling_service import SchedulingService

router = APIRouter(prefix='/scheduling', tags=['scheduling'])


@router.get('/slots', response_model=list[TimeSlotResponse])
def get_slots(requested_date: date | None = None, db: Session = Depends(get_db)) -> list[TimeSlotResponse]:
    slots = SchedulingService(db).get_available_slots(requested_date=requested_date)
    return [TimeSlotResponse(start=s.start, end=s.end, available=s.available) for s in slots]


@router.post('/book', response_model=AppointmentResponse)
def book_consultation(payload: BookConsultationRequest, db: Session = Depends(get_db)) -> AppointmentResponse:
    try:
        appointment = SchedulingService(db).book_consultation(
            lead_id=payload.lead_id,
            start_time=payload.start_time,
            duration_minutes=payload.duration_minutes,
            attendee_email=payload.attendee_email,
        )
    except SchedulingConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return AppointmentResponse.model_validate(appointment)


@router.post('/{appointment_id}/cancel', response_model=AppointmentResponse)
def cancel_consultation(appointment_id: int, db: Session = Depends(get_db)) -> AppointmentResponse:
    try:
        appointment = SchedulingService(db).cancel_consultation(appointment_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return AppointmentResponse.model_validate(appointment)


@router.post('/{appointment_id}/reschedule', response_model=AppointmentResponse)
def reschedule_consultation(
    appointment_id: int,
    payload: RescheduleRequest,
    db: Session = Depends(get_db),
) -> AppointmentResponse:
    try:
        appointment = SchedulingService(db).reschedule_consultation(
            appointment_id=appointment_id,
            new_start=payload.new_start_time,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except SchedulingConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return AppointmentResponse.model_validate(appointment)
