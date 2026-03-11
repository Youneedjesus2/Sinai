from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.repositories.schedule_repository import ScheduleRepository
from src.schemas.scheduling import (
    AppointmentResponse,
    AppointmentWithLeadResponse,
    BookConsultationRequest,
    RescheduleRequest,
    SchedulingConflictError,
    TimeSlotResponse,
)
from src.services.scheduling_service import SchedulingService

router = APIRouter(prefix='/scheduling', tags=['scheduling'])


@router.get('/appointments', response_model=list[AppointmentWithLeadResponse])
def get_appointments(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
) -> list[AppointmentWithLeadResponse]:
    """Return all booked appointments in the given date range (defaults to current week)."""
    if start_date is None:
        today = datetime.now(tz=timezone.utc).date()
        start_date = today - timedelta(days=today.weekday())  # Monday of current week
    if end_date is None:
        end_date = start_date + timedelta(days=7)
    start_dt = datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc)
    end_dt = datetime(end_date.year, end_date.month, end_date.day, tzinfo=timezone.utc)
    rows = ScheduleRepository(db).get_appointments_in_range(start_dt, end_dt)
    return [
        AppointmentWithLeadResponse(
            id=appt.id,
            lead_id=appt.lead_id,
            lead_name=lead_name,
            provider_event_id=appt.provider_event_id,
            start_time=appt.start_time,
            end_time=appt.end_time,
            status=appt.status,
        )
        for appt, lead_name in rows
    ]


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
