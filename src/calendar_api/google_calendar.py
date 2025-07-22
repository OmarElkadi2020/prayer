from datetime import datetime, timedelta
from typing import List, Dict, Any
from zoneinfo import ZoneInfo

from googleapiclient.discovery import build
from src.config.security import LOG

from .base import CalendarService

class GoogleCalendarService(CalendarService):
    """
    Google Calendar implementation of the CalendarService.
    """

    def __init__(self, creds):
        self.creds = creds
        self.service = None
        self.setup_credentials()

    def setup_credentials(self) -> None:
        try:
            self.service = build("calendar", "v3", credentials=self.creds)
        except Exception as error:
            LOG.error(f"An error occurred: {error}")

    def get_events(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        LOG.debug(f"get_events: Fetching events from {start_time.isoformat()} to {end_time.isoformat()}")
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=start_time.isoformat(),
            timeMax=end_time.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        LOG.debug(f"get_events: Received events_result: {events_result}")
        return events_result.get('items', [])

    def create_event(self, summary: str, start_time: datetime, end_time: datetime, description: str) -> Dict[str, Any]:
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
            },
            'end': {
                'dateTime': end_time.isoformat(),
            },
            'visibility': 'private',
        }
        created_event = self.service.events().insert(calendarId='primary', body=event).execute()
        return created_event

    def delete_event(self, event_id: str) -> None:
        self.service.events().delete(calendarId='primary', eventId=event_id).execute()

    def find_first_available_slot(self, start_time: datetime, duration_minutes: int) -> datetime:
        utc_zone = ZoneInfo("UTC")
        
        # Ensure start_time is UTC-aware
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=utc_zone)
        else:
            start_time = start_time.astimezone(utc_zone)

        day_start = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        LOG.debug(f"DEBUG (find_first_available_slot): Initial start_time (UTC): {start_time}")
        LOG.debug(f"DEBUG (find_first_available_slot): day_start (UTC): {day_start}, day_end (UTC): {day_end}")

        events = sorted(self.get_events(day_start, day_end), key=lambda x: (
            datetime.fromisoformat(x['start']['dateTime']).astimezone(utc_zone) if 'dateTime' in x['start']
            else datetime.fromisoformat(x['start']['date']).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=utc_zone)
        ))
        LOG.debug(f"DEBUG (find_first_available_slot): Fetched events: {events}")

        current_slot_start = start_time

        for event in events:
            LOG.debug(f"DEBUG (find_first_available_slot): Current slot start at iteration beginning: {current_slot_start}")
            event_start_data = event.get('start')
            event_end_data = event.get('end')

            event_start_str = None
            if event_start_data and 'dateTime' in event_start_data:
                event_start_str = event_start_data['dateTime']
            elif event_start_data and 'date' in event_start_data:
                event_start_str = event_start_data['date']

            event_end_str = None
            if event_end_data and 'dateTime' in event_end_data:
                event_end_str = event_end_data['dateTime']
            elif event_end_data and 'date' in event_end_data:
                event_end_str = event_end_data['date']

            LOG.debug(f"DEBUG (find_first_available_slot): Processing event: start_str={event_start_str}, end_str={event_end_str}")

            if not event_start_str or not event_end_str:
                LOG.debug(f"Skipping event due to missing or empty start/end time data: start={event_start_data}, end={event_end_data}")
                continue

            if not isinstance(event_start_str, str) or not isinstance(event_end_str, str):
                LOG.error(f"Skipping event due to non-string start/end time: start={event_start_str} (type: {type(event_start_str)}), end={event_end_str} (type: {type(event_end_str)})")
                continue

            try:
                is_all_day_event = 'date' in event_start_data and 'dateTime' not in event_start_data

                if is_all_day_event:
                    LOG.debug(f"DEBUG (find_first_available_slot): Skipping all-day event: {event.get('summary')}")
                    continue # Skip all-day events for slot finding

                event_start = datetime.fromisoformat(event_start_str).astimezone(utc_zone)
                event_end = datetime.fromisoformat(event_end_str).astimezone(utc_zone)
                LOG.debug(f"DEBUG (find_first_available_slot): Parsed event: start={event_start}, end={event_end}")

            except ValueError as ve:
                LOG.error(f"Failed to parse event time string '{event_start_str}' or '{event_end_str}': {ve}")
                continue

            # If the current potential slot ends before the event starts, we found a slot
            if current_slot_start + timedelta(minutes=duration_minutes) <= event_start:
                LOG.debug(f"DEBUG (find_first_available_slot): Found slot before event. Returning {current_slot_start}")
                return current_slot_start

            # If there's an overlap, move the current_slot_start past the end of the current event
            if current_slot_start < event_end:
                LOG.debug(f"DEBUG (find_first_available_slot): Overlap detected. Moving current_slot_start from {current_slot_start} to {event_end}")
                current_slot_start = event_end

        # If no more events, the current_slot_start is available
        LOG.debug(f"DEBUG (find_first_available_slot): No more events. Returning final current_slot_start: {current_slot_start.astimezone(utc_zone)}")
        return current_slot_start.astimezone(utc_zone)
    
    def add_event(self, start_time: datetime, summary: str, duration_minutes: int) -> bool:
        """
        Creates a busy calendar event.
        """
        utc_zone = ZoneInfo("UTC")
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=utc_zone)
        else:
            start_time = start_time.astimezone(utc_zone)

        # Find the first available slot for the event
        actual_start_time = self.find_first_available_slot(start_time, duration_minutes)
        actual_slot_end = actual_start_time + timedelta(minutes=duration_minutes)

        try:
            # First, check if an event with the same summary already exists for that day
            day_start = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            events = self.get_events(day_start, day_end)
            for event in events:
                if event.get('summary', '').lower() == summary.lower():
                    LOG.info(f"Event '{summary}' already exists in Calender for today. Skipping readding it.")
                    return False

            self.create_event(summary, actual_start_time, actual_slot_end, "Scheduled by Prayer App")
            LOG.info(f"📅 Added busy block: {summary} at {actual_start_time.strftime('%H:%M')}-{actual_slot_end.strftime('%H:%M')}")
            return True
        except Exception as e:
            LOG.error(f"Failed to add busy block: {e}")
            return False
    
    
