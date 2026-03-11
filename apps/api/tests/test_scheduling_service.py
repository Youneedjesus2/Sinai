"""Tests for SchedulingService — booking, overlap, cancellation, rescheduling."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.schemas.models import AppointmentStatus
from src.schemas.scheduling import SchedulingConflictError


START = datetime(2026, 6, 1, 10, 0, 0)
END = datetime(2026, 6, 1, 10, 30, 0)


def _make_appointment(
    id: int = 1,
    lead_id: int = 42,
    provider_event_id: str = 'gcal-event-001',
    status: AppointmentStatus = AppointmentStatus.confirmed,
    start: datetime = START,
    end: datetime = END,
) -> MagicMock:
    appt = MagicMock()
    appt.id = id
    appt.lead_id = lead_id
    appt.provider_event_id = provider_event_id
    appt.status = status
    appt.start_time = start
    appt.end_time = end
    return appt


# ---------------------------------------------------------------------------
# 1. Booking success creates Appointment record and audit event
# ---------------------------------------------------------------------------

def test_book_consultation_creates_appointment_and_audit(reset_db):
    from src.core.db import SessionLocal
    from src.services.scheduling_service import SchedulingService

    db = SessionLocal()
    try:
        # We need a real lead in the DB for the FK constraint
        from src.schemas.models import Lead
        lead = Lead(agency_id='test-agency', source_channel='email')
        db.add(lead)
        db.flush()
        lead_id = lead.id

        with patch('src.services.scheduling_service.GoogleCalendarClient') as mock_gc:
            mock_gc.return_value.create_event.return_value = 'gcal-event-001'
            appointment = SchedulingService(db).book_consultation(
                lead_id=lead_id,
                start_time=START,
                duration_minutes=30,
            )

        assert appointment.id is not None
        assert appointment.lead_id == lead_id
        assert appointment.provider_event_id == 'gcal-event-001'
        assert appointment.status == AppointmentStatus.confirmed

        # Audit event should exist
        from src.repositories.audit_repository import AuditRepository
        events = AuditRepository(db).list_for_lead(lead_id)
        event_types = [e.event_type for e in events]
        assert 'appointment_booked' in event_types
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 2. Overlap prevention raises SchedulingConflictError
# ---------------------------------------------------------------------------

def test_book_consultation_raises_conflict_on_overlap(reset_db):
    from src.core.db import SessionLocal
    from src.services.scheduling_service import SchedulingService

    db = SessionLocal()
    try:
        from src.schemas.models import Lead
        lead = Lead(agency_id='test-agency', source_channel='sms')
        db.add(lead)
        db.flush()
        lead_id = lead.id

        # Book first appointment
        with patch('src.services.scheduling_service.GoogleCalendarClient') as mock_gc:
            mock_gc.return_value.create_event.return_value = 'gcal-event-001'
            SchedulingService(db).book_consultation(lead_id=lead_id, start_time=START)

        # Attempt to book overlapping slot — should raise
        with patch('src.services.scheduling_service.GoogleCalendarClient') as mock_gc:
            mock_gc.return_value.create_event.return_value = 'gcal-event-002'
            with pytest.raises(SchedulingConflictError):
                SchedulingService(db).book_consultation(lead_id=lead_id, start_time=START)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 3. Cancellation updates appointment status to 'cancelled'
# ---------------------------------------------------------------------------

def test_cancel_consultation_sets_status_to_cancelled(reset_db):
    from src.core.db import SessionLocal
    from src.services.scheduling_service import SchedulingService

    db = SessionLocal()
    try:
        from src.schemas.models import Lead
        lead = Lead(agency_id='test-agency', source_channel='sms')
        db.add(lead)
        db.flush()
        lead_id = lead.id

        # Book
        with patch('src.services.scheduling_service.GoogleCalendarClient') as mock_gc:
            mock_gc.return_value.create_event.return_value = 'gcal-event-001'
            appointment = SchedulingService(db).book_consultation(
                lead_id=lead_id, start_time=START
            )

        appointment_id = appointment.id

        # Cancel
        with patch('src.services.scheduling_service.GoogleCalendarClient') as mock_gc:
            mock_gc.return_value.cancel_event.return_value = True
            cancelled = SchedulingService(db).cancel_consultation(appointment_id)

        assert cancelled.status == AppointmentStatus.cancelled

        # Audit events should include appointment_cancelled
        from src.repositories.audit_repository import AuditRepository
        events = AuditRepository(db).list_for_lead(lead_id)
        event_types = [e.event_type for e in events]
        assert 'appointment_cancelled' in event_types
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 4. cancel_consultation raises 404 when appointment not found
# ---------------------------------------------------------------------------

def test_cancel_nonexistent_appointment_raises_value_error(reset_db):
    from src.core.db import SessionLocal
    from src.services.scheduling_service import SchedulingService

    db = SessionLocal()
    try:
        with pytest.raises(ValueError, match='9999'):
            SchedulingService(db).cancel_consultation(9999)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 5. Rescheduling creates a new appointment and cancels the old one
# ---------------------------------------------------------------------------

def test_reschedule_creates_new_appointment(reset_db):
    from src.core.db import SessionLocal
    from src.services.scheduling_service import SchedulingService

    db = SessionLocal()
    try:
        from src.schemas.models import Lead
        lead = Lead(agency_id='test-agency', source_channel='sms')
        db.add(lead)
        db.flush()
        lead_id = lead.id

        # Book original
        with patch('src.services.scheduling_service.GoogleCalendarClient') as mock_gc:
            mock_gc.return_value.create_event.return_value = 'gcal-event-001'
            original = SchedulingService(db).book_consultation(
                lead_id=lead_id, start_time=START
            )

        new_start = datetime(2026, 6, 2, 14, 0, 0)

        # Reschedule to a non-overlapping slot
        with patch('src.services.scheduling_service.GoogleCalendarClient') as mock_gc:
            mock_gc.return_value.cancel_event.return_value = True
            mock_gc.return_value.create_event.return_value = 'gcal-event-002'
            rescheduled = SchedulingService(db).reschedule_consultation(
                appointment_id=original.id,
                new_start=new_start,
            )

        assert rescheduled.id != original.id
        assert rescheduled.provider_event_id == 'gcal-event-002'
        assert rescheduled.status == AppointmentStatus.confirmed

        # Audit events should include appointment_rescheduled
        from src.repositories.audit_repository import AuditRepository
        events = AuditRepository(db).list_for_lead(lead_id)
        event_types = [e.event_type for e in events]
        assert 'appointment_rescheduled' in event_types
    finally:
        db.close()
