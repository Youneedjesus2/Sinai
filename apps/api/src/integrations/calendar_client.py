import json
import logging
from datetime import datetime, timedelta

from src.core.config import get_settings
from src.schemas.scheduling import CalendarBookingError, TimeSlot

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar']
BUSINESS_HOUR_START = 9   # 09:00 UTC
BUSINESS_HOUR_END = 17    # 17:00 UTC


class GoogleCalendarClient:
    def __init__(self) -> None:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        settings = get_settings()
        creds_dict = json.loads(settings.google_calendar_credentials_json)
        creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=SCOPES
        )
        self._service = build('calendar', 'v3', credentials=creds)
        self._calendar_id = settings.google_calendar_id

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def get_available_slots(
        self,
        date_range_start: datetime,
        date_range_end: datetime,
        duration_minutes: int = 30,
    ) -> list[TimeSlot]:
        """Return all candidate slots with availability flags in the given window."""
        busy_intervals = self._get_busy_intervals(date_range_start, date_range_end)
        slots: list[TimeSlot] = []

        current = date_range_start.replace(
            hour=BUSINESS_HOUR_START, minute=0, second=0, microsecond=0
        )
        while current < date_range_end:
            slot_end = current + timedelta(minutes=duration_minutes)
            if current.hour < BUSINESS_HOUR_START or slot_end.hour > BUSINESS_HOUR_END or (
                slot_end.hour == BUSINESS_HOUR_END and slot_end.minute > 0
            ):
                current = current + timedelta(minutes=duration_minutes)
                continue

            available = not self._overlaps_busy(current, slot_end, busy_intervals)
            slots.append(TimeSlot(start=current, end=slot_end, available=available))
            current = slot_end

        return slots

    def create_event(
        self,
        title: str,
        start: datetime,
        end: datetime,
        attendee_email: str | None,
    ) -> str:
        """Create a Google Calendar event and return the event ID.

        Raises CalendarBookingError if the slot is no longer free.
        """
        # Server-side overlap check before committing (safe failure rule #3)
        busy = self._get_busy_intervals(start, end)
        if self._overlaps_busy(start, end, busy):
            raise CalendarBookingError(
                f'Slot {start.isoformat()}–{end.isoformat()} is no longer available'
            )

        body: dict = {
            'summary': title,
            'start': {'dateTime': start.isoformat(), 'timeZone': 'UTC'},
            'end': {'dateTime': end.isoformat(), 'timeZone': 'UTC'},
        }
        if attendee_email:
            body['attendees'] = [{'email': attendee_email}]

        event = (
            self._service.events()
            .insert(calendarId=self._calendar_id, body=body)
            .execute()
        )
        event_id: str = event['id']
        logger.info('Google Calendar event created — ID: %s', event_id)
        return event_id

    def cancel_event(self, event_id: str) -> bool:
        """Delete a Google Calendar event. Returns True on success."""
        try:
            self._service.events().delete(
                calendarId=self._calendar_id, eventId=event_id
            ).execute()
            logger.info('Google Calendar event deleted — ID: %s', event_id)
            return True
        except Exception as exc:
            logger.error('Google Calendar cancel_event failed — ID: %s  error: %s', event_id, exc)
            return False

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_busy_intervals(
        self, range_start: datetime, range_end: datetime
    ) -> list[tuple[datetime, datetime]]:
        """Return a list of (start, end) busy intervals from the calendar."""
        try:
            result = (
                self._service.events()
                .list(
                    calendarId=self._calendar_id,
                    timeMin=range_start.isoformat() + 'Z',
                    timeMax=range_end.isoformat() + 'Z',
                    singleEvents=True,
                    orderBy='startTime',
                )
                .execute()
            )
            intervals: list[tuple[datetime, datetime]] = []
            for event in result.get('items', []):
                s = event.get('start', {})
                e = event.get('end', {})
                start_str = s.get('dateTime') or s.get('date')
                end_str = e.get('dateTime') or e.get('date')
                if start_str and end_str:
                    intervals.append((
                        datetime.fromisoformat(start_str.replace('Z', '+00:00')),
                        datetime.fromisoformat(end_str.replace('Z', '+00:00')),
                    ))
            return intervals
        except Exception as exc:
            logger.error('Google Calendar events().list() failed: %s', exc)
            return []

    @staticmethod
    def _overlaps_busy(
        start: datetime,
        end: datetime,
        busy: list[tuple[datetime, datetime]],
    ) -> bool:
        """Return True if [start, end) overlaps any busy interval."""
        for b_start, b_end in busy:
            # Strip tzinfo for comparison if one side is naive
            bs = b_start.replace(tzinfo=None) if b_start.tzinfo else b_start
            be = b_end.replace(tzinfo=None) if b_end.tzinfo else b_end
            s = start.replace(tzinfo=None) if start.tzinfo else start
            e = end.replace(tzinfo=None) if end.tzinfo else end
            if s < be and e > bs:
                return True
        return False
