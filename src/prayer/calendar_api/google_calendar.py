import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

from googleapiclient.discovery import build

from .base import CalendarService
from prayer.auth.google_auth import get_google_credentials

class GoogleCalendarService(CalendarService):
    """
    Google Calendar implementation of the CalendarService.
    """

    def __init__(self):
        self.creds = get_google_credentials()
        self.service = build('calendar', 'v3', credentials=self.creds)

    def _get_credentials(self):
        return get_google_credentials()

    def get_events(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=start_time.isoformat(),
            timeMax=end_time.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
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
        }
        created_event = self.service.events().insert(calendarId='primary', body=event).execute()
        return created_event

    def delete_event(self, event_id: str) -> None:
        self.service.events().delete(calendarId='primary', eventId=event_id).execute()

    def find_first_available_slot(self, start_time: datetime, duration_minutes: int) -> datetime:
        day_start = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        events = self.get_events(day_start, day_end)
        
        potential_start = start_time
        
        while True:
            is_available = True
            potential_end = potential_start + timedelta(minutes=duration_minutes)
            
            for event in events:
                event_start_str = event['start'].get('dateTime')
                event_end_str = event['end'].get('dateTime')
                
                if not event_start_str or not event_end_str:
                    continue

                event_start = datetime.fromisoformat(event_start_str)
                event_end = datetime.fromisoformat(event_end_str)

                if potential_start < event_end and potential_end > event_start:
                    is_available = False
                    potential_start = event_end # Move to the end of the conflicting event
                    break
            
            if is_available:
                return potential_start
    
    def setup_credentials(self) -> None:
        self._get_credentials()
