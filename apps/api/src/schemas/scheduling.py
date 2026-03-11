from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.schemas.models import AppointmentStatus


# ---------------------------------------------------------------------------
# Domain objects
# ---------------------------------------------------------------------------

@dataclass
class TimeSlot:
    start: datetime
    end: datetime
    available: bool


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class CalendarBookingError(Exception):
    """Raised when Google Calendar refuses to create an event (slot taken or API error)."""


class SchedulingConflictError(Exception):
    """Raised when a local DB overlap check finds a conflicting appointment."""


# ---------------------------------------------------------------------------
# Pydantic request / response schemas for API routes
# ---------------------------------------------------------------------------

class BookConsultationRequest(BaseModel):
    lead_id: int
    start_time: datetime
    duration_minutes: int = 30
    attendee_email: str | None = None


class RescheduleRequest(BaseModel):
    new_start_time: datetime


class TimeSlotResponse(BaseModel):
    start: datetime
    end: datetime
    available: bool


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    provider_event_id: str | None
    start_time: datetime | None
    end_time: datetime | None
    status: AppointmentStatus


class AppointmentWithLeadResponse(BaseModel):
    id: int
    lead_id: int
    lead_name: str | None
    provider_event_id: str | None
    start_time: datetime | None
    end_time: datetime | None
    status: AppointmentStatus
