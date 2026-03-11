from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from src.schemas.models import Appointment, AppointmentStatus


class ScheduleRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_appointment(
        self,
        lead_id: int,
        provider_event_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> Appointment:
        appointment = Appointment(
            lead_id=lead_id,
            provider_event_id=provider_event_id,
            start_time=start_time,
            end_time=end_time,
            status=AppointmentStatus.confirmed,
        )
        self.db.add(appointment)
        self.db.flush()
        return appointment

    def get_appointment(self, appointment_id: int) -> Appointment | None:
        return self.db.get(Appointment, appointment_id)

    def get_appointments_for_lead(self, lead_id: int) -> list[Appointment]:
        return list(
            self.db.scalars(
                select(Appointment).where(Appointment.lead_id == lead_id)
            )
        )

    def update_appointment_status(
        self, appointment_id: int, status: AppointmentStatus
    ) -> Appointment:
        appointment = self.db.get(Appointment, appointment_id)
        if appointment is None:
            raise ValueError(f'Appointment {appointment_id} not found')
        appointment.status = status
        self.db.flush()
        return appointment

    def check_overlap(self, start_time: datetime, end_time: datetime) -> bool:
        """Return True if any confirmed appointment overlaps the given window."""
        result = self.db.scalars(
            select(Appointment).where(
                and_(
                    Appointment.status == AppointmentStatus.confirmed,
                    Appointment.start_time < end_time,
                    Appointment.end_time > start_time,
                )
            )
        ).first()
        return result is not None
