# src/domain/scheduler_messages.py
from __future__ import annotations
from dataclasses import dataclass

from src.domain.enums import AppState
from src.shared.events import Event

@dataclass
class ScheduleRefreshedEvent(Event):
    """Event published when the prayer schedule has been refreshed."""
    next_prayer_info: str

@dataclass
class ApplicationStateChangedEvent(Event):
    """Event published when the application's core state changes."""
    new_state: AppState

@dataclass
class PrayerTimeEvent(Event):
    """Event published when it is time for a specific prayer."""
    prayer_name: str
