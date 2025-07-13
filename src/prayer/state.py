from __future__ import annotations
import threading
from enum import Enum, auto

class AppState(Enum):
    IDLE = auto()
    SYNCING = auto()
    PRAYER_TIME = auto()
    ERROR = auto()

class StateManager:
    """A thread-safe class to manage the application's global state."""
    def __init__(self):
        self._state = AppState.IDLE
        self._lock = threading.Lock()
        self._next_prayer_info = "Loading..."

    @property
    def state(self) -> AppState:
        with self._lock:
            return self._state

    @state.setter
    def state(self, new_state: AppState):
        with self._lock:
            self._state = new_state

    @property
    def next_prayer_info(self) -> str:
        with self._lock:
            return self._next_prayer_info

    @next_prayer_info.setter
    def next_prayer_info(self, info: str):
        with self._lock:
            self._next_prayer_info = info

# Singleton instance
state_manager = StateManager()
