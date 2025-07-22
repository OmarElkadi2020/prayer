# src/domain/notification_messages.py
from __future__ import annotations
from dataclasses import dataclass

from src.shared.events import Event

@dataclass
class FocusModeRequestedEvent(Event):
    """Event published to request showing the focus mode window."""
    pass

@dataclass
class AudioPlaybackRequestedEvent(Event):
    """Event published to request playing an audio file."""
    audio_path: str
