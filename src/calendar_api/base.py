from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any

class CalendarService(ABC):
    """
    Abstract base class for calendar services.
    """

    @abstractmethod
    def get_events(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """
        Get all events between two datetimes.
        """
        pass

    @abstractmethod
    def create_event(self, summary: str, start_time: datetime, end_time: datetime, description: str) -> Dict[str, Any]:
        """
        Create a new event.
        """
        pass

    @abstractmethod
    def delete_event(self, event_id: str) -> None:
        """
        Delete an event by its ID.
        """
        pass

    @abstractmethod
    def find_first_available_slot(self, start_time: datetime, duration_minutes: int) -> datetime:
        """
        Find the first available slot for an event.
        """
        pass

    @abstractmethod
    def setup_credentials(self) -> None:
        """
        Setup credentials for the service.
        """
        pass
