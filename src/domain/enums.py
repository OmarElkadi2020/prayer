# src/domain/enums.py
from __future__ import annotations
from enum import Enum, auto

class AppState(Enum):
    IDLE = auto()
    SYNCING = auto()
    PRAYER_TIME = auto()
    ERROR = auto()
