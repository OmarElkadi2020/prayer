# src/gui/notification_service.py
from __future__ import annotations
import logging

from src.shared.event_bus import EventBus
from src.domain.notification_messages import AudioPlaybackRequestedEvent, FocusModeRequestedEvent
from src.shared.audio_player import play
from src.qt_utils import run_in_qt_thread

LOG = logging.getLogger(__name__)

class NotificationService:
    """
    A service that handles events related to user notifications (UI, audio).
    It acts as the bridge between the event-driven backend and the Qt GUI.
    """
    def __init__(self, event_bus: EventBus):
        self._event_bus = event_bus
        self._event_bus.register(AudioPlaybackRequestedEvent, self.handle_audio_playback_requested)
        self._event_bus.register(FocusModeRequestedEvent, self.handle_focus_mode_requested)

    def _run_focus_steps(self, is_modal: bool = False):
        """Activates focus mode by running the focus steps window."""
        LOG.info(f"Activating focus steps window (modal={is_modal}).")
        from src.focus_steps_view import run as run_focus_steps_window
        run_focus_steps_window(is_modal=is_modal)
        LOG.info("Focus steps window function called.")

    @run_in_qt_thread
    def handle_focus_mode_requested(self, event: FocusModeRequestedEvent):
        """Handles the request to show the focus mode window on the GUI thread."""
        LOG.info("Handling FocusModeRequestedEvent.")
        self._run_focus_steps(is_modal=True)

    def handle_audio_playback_requested(self, event: AudioPlaybackRequestedEvent):
        """Handles the request to play audio."""
        LOG.info(f"Handling AudioPlaybackRequestedEvent for {event.audio_path}.")
        play(event.audio_path)
