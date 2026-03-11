from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from src.integrations.calendar_client import GoogleCalendarClient
from src.repositories.audit_repository import AuditRepository
from src.repositories.schedule_repository import ScheduleRepository
from src.schemas.models import Appointment, AppointmentStatus
from src.schemas.scheduling import (
    CalendarBookingError,
    SchedulingConflictError,
    TimeSlot,
)

CONSULTATION_TITLE = 'Healthcare Consultation'
DEFAULT_SLOT_DAYS = 7  # look-ahead when no date is requested


class SchedulingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ScheduleRepository(db)
        self.audits = AuditRepository(db)

    # ------------------------------------------------------------------
    # Slot availability
    # ------------------------------------------------------------------

    def get_available_slots(self, requested_date: date | None = None) -> list[TimeSlot]:
        """Return available time slots from Google Calendar.

        If requested_date is given, return slots for that day only.
        Otherwise return slots for the next DEFAULT_SLOT_DAYS days.
        """
        now = datetime.utcnow()
        if requested_date is not None:
            range_start = datetime(requested_date.year, requested_date.month, requested_date.day)
            range_end = range_start + timedelta(days=1)
        else:
            range_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            range_end = range_start + timedelta(days=DEFAULT_SLOT_DAYS)

        return GoogleCalendarClient().get_available_slots(range_start, range_end)

    # ------------------------------------------------------------------
    # Booking
    # ------------------------------------------------------------------

    def book_consultation(
        self,
        lead_id: int,
        start_time: datetime,
        duration_minutes: int = 30,
        attendee_email: str | None = None,
    ) -> Appointment:
        """Book a consultation slot.

        Raises SchedulingConflictError if the local DB has an overlap.
        Raises CalendarBookingError if Google Calendar rejects the event.
        """
        end_time = start_time + timedelta(minutes=duration_minutes)

        # 1. Local overlap check (safe failure rule #3)
        if self.repo.check_overlap(start_time, end_time):
            raise SchedulingConflictError(
                f'Appointment slot {start_time.isoformat()} is already booked'
            )

        # 2. Create Google Calendar event (may raise CalendarBookingError)
        provider_event_id = GoogleCalendarClient().create_event(
            title=CONSULTATION_TITLE,
            start=start_time,
            end=end_time,
            attendee_email=attendee_email,
        )

        # 3. Persist appointment
        appointment = self.repo.create_appointment(
            lead_id=lead_id,
            provider_event_id=provider_event_id,
            start_time=start_time,
            end_time=end_time,
        )

        # 4. Audit
        self.audits.create_event(
            lead_id=lead_id,
            event_type='appointment_booked',
            event_payload={
                'appointment_id': appointment.id,
                'provider_event_id': provider_event_id,
            },
        )

        # 5. Commit and return
        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    # ------------------------------------------------------------------
    # Cancellation
    # ------------------------------------------------------------------

    def cancel_consultation(self, appointment_id: int) -> Appointment:
        """Cancel an appointment — removes from Google Calendar and marks DB record."""
        appointment = self.repo.get_appointment(appointment_id)
        if appointment is None:
            raise ValueError(f'Appointment {appointment_id} not found')

        # Cancel on provider (best-effort — log failure but don't block DB update)
        if appointment.provider_event_id:
            success = GoogleCalendarClient().cancel_event(appointment.provider_event_id)
            if not success:
                self.audits.create_event(
                    lead_id=appointment.lead_id,
                    event_type='external_service_failure',
                    event_payload={
                        'vendor': 'google_calendar',
                        'error': f'cancel_event failed for event {appointment.provider_event_id}',
                    },
                )

        appointment = self.repo.update_appointment_status(
            appointment_id, AppointmentStatus.cancelled
        )

        self.audits.create_event(
            lead_id=appointment.lead_id,
            event_type='appointment_cancelled',
            event_payload={'appointment_id': appointment_id},
        )

        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    # ------------------------------------------------------------------
    # Rescheduling
    # ------------------------------------------------------------------

    def reschedule_consultation(
        self, appointment_id: int, new_start: datetime
    ) -> Appointment:
        """Cancel existing booking and create a new one at the requested time."""
        appointment = self.repo.get_appointment(appointment_id)
        if appointment is None:
            raise ValueError(f'Appointment {appointment_id} not found')

        if appointment.end_time and appointment.start_time:
            duration = int((appointment.end_time - appointment.start_time).total_seconds() // 60)
        else:
            duration = 30

        new_end = new_start + timedelta(minutes=duration)

        # Local overlap check (exclude the current appointment)
        if self.repo.check_overlap(new_start, new_end):
            raise SchedulingConflictError(
                f'New slot {new_start.isoformat()} conflicts with an existing appointment'
            )

        # Cancel old calendar event (best-effort)
        if appointment.provider_event_id:
            GoogleCalendarClient().cancel_event(appointment.provider_event_id)

        # Create new calendar event
        new_provider_event_id = GoogleCalendarClient().create_event(
            title=CONSULTATION_TITLE,
            start=new_start,
            end=new_end,
            attendee_email=None,
        )

        # Mark old appointment cancelled
        self.repo.update_appointment_status(appointment_id, AppointmentStatus.cancelled)

        # Create new appointment record
        new_appointment = self.repo.create_appointment(
            lead_id=appointment.lead_id,
            provider_event_id=new_provider_event_id,
            start_time=new_start,
            end_time=new_end,
        )

        self.audits.create_event(
            lead_id=appointment.lead_id,
            event_type='appointment_rescheduled',
            event_payload={
                'old_appointment_id': appointment_id,
                'new_appointment_id': new_appointment.id,
                'new_provider_event_id': new_provider_event_id,
            },
        )

        self.db.commit()
        self.db.refresh(new_appointment)
        return new_appointment
