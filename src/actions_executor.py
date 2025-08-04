from __future__ import annotations
from src.config.security import LOG
from src.shared.event_bus import EventBus
from src.domain.notification_messages import AudioPlaybackRequestedEvent, FocusModeRequestedEvent
import threading

class ActionExecutor:
    """
    Executes actions like playing audio and triggering focus mode.
    This allows for decoupling the scheduler from the GUI.
    """
    def __init__(self, event_bus: EventBus, dry_run: bool = False):
        self._event_bus = event_bus
        self._dry_run = dry_run
        self._dry_run_event: threading.Event | None = None

    def play_audio(self, audio_path: str):
        if self._dry_run:
            LOG.info(f"ActionExecutor (dry_run): Would play audio from {audio_path}")
            if self._dry_run_event:
                self._dry_run_event.set()
        else:
            LOG.info(f"ActionExecutor: Requesting audio playback for {audio_path}")
            self._event_bus.publish(AudioPlaybackRequestedEvent(audio_path=audio_path))

    def trigger_focus_mode(self):
        if self._dry_run:
            LOG.info("ActionExecutor (dry_run): Would trigger focus mode.")
        else:
            LOG.info("ActionExecutor: Requesting focus mode.")
            self._event_bus.publish(FocusModeRequestedEvent())

    def set_dry_run_event(self, event: threading.Event):
        if self._dry_run:
            self._dry_run_event = event