# ---------------------------------------------------------------------------
# calendar_utils.py – Calendar access with de-duplication
# ---------------------------------------------------------------------------

from __future__ import annotations

from datetime import datetime, date, time, timedelta
from typing import Optional

from .config import TZ, BUSY_SLOT, LOG
from .calendar_api.base import CalendarService
from .calendar_api.google_calendar import GoogleCalendarService
# from .calendar_api.microsoft_calendar import MicrosoftCalendarService

# In the future, this will be based on user configuration
def get_calendar_service() -> Optional[CalendarService]:
    """
    Returns the configured calendar service.
    """
    # For now, we'll default to Google Calendar
    try:
        return GoogleCalendarService()
    except Exception as e:
        LOG.error(f"Failed to initialize calendar service: {e}")
        return None


def first_free_gap(start: datetime, duration_minutes: int) -> Optional[datetime]:
    """
    Finds the earliest available time slot for a given duration, starting from a specific time.
    """
    service = get_calendar_service()
    if not service:
        return start # No service, assume it's free

    try:
        return service.find_first_available_slot(start, duration_minutes)
    except Exception as e:
        LOG.error(f"Could not find free gap: {e}")
        return start # Fail open


def add_busy_block(slot_start: datetime, summary: str, duration_minutes: int) -> bool:
    """
    Creates a busy calendar event.
    """
    service = get_calendar_service()
    if not service:
        return False

    slot_end = slot_start + timedelta(minutes=duration_minutes)
    
    try:
        # First, check if an event with the same summary already exists for that day
        day_start = slot_start.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        events = service.get_events(day_start, day_end)
        for event in events:
            if event.get('summary', '').lower() == summary.lower():
                LOG.info(f"Event '{summary}' already exists for today. Skipping.")
                return False

        service.create_event(summary, slot_start, slot_end, "Scheduled by Prayer App")
        LOG.info(f"📅 Added busy block: {summary} at {slot_start.strftime('%H:%M')}-{slot_end.strftime('%H:%M')}")
        return True
    except Exception as e:
        LOG.error(f"Failed to add busy block: {e}")
        return False