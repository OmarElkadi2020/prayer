import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

from googleapiclient.discovery import build

from .base import CalendarService
from src.auth.google_auth import get_google_credentials

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
            print(f"An error occurred: {error}")

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
            'visibility': 'private',
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
    
    def add_event(self, start_time: datetime, summary: str, duration_minutes: int) -> bool:
        """
        Creates a busy calendar event.
        """
        slot_end = start_time + timedelta(minutes=duration_minutes)
        
        try:
            # First, check if an event with the same summary already exists for that day
            day_start = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            events = self.get_events(day_start, day_end)
            for event in events:
                if event.get('summary', '').lower() == summary.lower():
                    print(f"Event '{summary}' already exists in Calender for today. Skipping readding it.")
                    return False

            self.create_event(summary, start_time, slot_end, "Scheduled by Prayer App")
            print(f"📅 Added busy block: {summary} at {start_time.strftime('%H:%M')}-{slot_end.strftime('%H:%M')}")
            return True
        except Exception as e:
            print(f"Failed to add busy block: {e}")
            return False
    
    
