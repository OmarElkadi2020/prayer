from __future__ import annotations
from typing import Protocol
from src.config.security import LOG
from src.shared.event_bus import EventBus
from src.domain.notification_messages import AudioPlaybackRequestedEvent, FocusModeRequestedEvent
import threading

class ActionExecutor(Protocol):
    """
    Protocol for executing actions like playing audio and triggering focus mode.
    This allows for decoupling the scheduler from the GUI.
    """
    def play_audio(self, audio_path: str):
        ...

    def trigger_focus_mode(self):
        ...

    def set_dry_run_event(self, event: threading.Event):
        ...

class DefaultActionExecutor:
    """
    The default implementation of ActionExecutor. It publishes events to request actions.
    """
    def __init__(self, event_bus: EventBus):
        self._event_bus = event_bus

    def play_audio(self, audio_path: str):
        LOG.info(f"DefaultActionExecutor: Requesting audio playback for {audio_path}")
        self._event_bus.publish(AudioPlaybackRequestedEvent(audio_path=audio_path))

    def trigger_focus_mode(self):
        LOG.info("DefaultActionExecutor: Requesting focus mode.")
        self._event_bus.publish(FocusModeRequestedEvent())

    def set_dry_run_event(self, event: threading.Event):
        # The default executor doesn't need to handle this event.
        pass

class DryRunActionExecutor:
    """
    An implementation of ActionExecutor for dry runs that only logs actions.
    """
    def __init__(self):
        self._dry_run_event: threading.Event | None = None

    def play_audio(self, audio_path: str):
        LOG.info(f"DryRunActionExecutor: Would play audio from {audio_path}")
        # In a dry run, we might still want to signal that the "audio" has "finished"
        if self._dry_run_event:
            self._dry_run_event.set()

    def trigger_focus_mode(self):
        LOG.info("DryRunActionExecutor: Would trigger focus mode.")

    def set_dry_run_event(self, event: threading.Event):
        self._dry_run_event = event
