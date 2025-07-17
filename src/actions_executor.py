from __future__ import annotations
from typing import Protocol
from src.config.security import LOG
from src.actions import play, trigger_focus_mode
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
    The default implementation of ActionExecutor that interacts with the system.
    """
    def play_audio(self, audio_path: str):
        LOG.info(f"DefaultActionExecutor: Playing audio from {audio_path}")
        play(audio_path)

    def trigger_focus_mode(self):
        LOG.info("DefaultActionExecutor: Triggering focus mode.")
        trigger_focus_mode()

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
