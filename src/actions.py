# ---------------------------------------------------------------------------
# actions.py – shell helpers, focus‑mode, audio playback
# ---------------------------------------------------------------------------
import os
import subprocess
import sys

from src.config.security import LOG
from src.qt_utils import run_in_qt_thread


# -- focus mode -----------------------------------------------------------

def _create_trigger_focus_mode():
    """Factory to create the trigger_focus_mode function with a persistent state."""
    _focus_window_instance = None  # Closure to hold the window instance

    @run_in_qt_thread
    def trigger_focus_mode():
        """Triggers focus mode, ensuring it runs on the Qt GUI thread."""
        nonlocal _focus_window_instance
        LOG.info("Triggering focus mode for GUI.")
        from src.focus_steps_view import FocusStepsView  # Local import
        from src.presenter.focus_steps_presenter import FocusStepsPresenter

        if _focus_window_instance is None or not _focus_window_instance.isVisible():
            presenter = FocusStepsPresenter()
            _focus_window_instance = FocusStepsView(presenter, disable_sound=True)
            _focus_window_instance.show()
        
        _focus_window_instance.activateWindow()

    return trigger_focus_mode

trigger_focus_mode = _create_trigger_focus_mode()


def run_focus_steps(is_modal: bool = False) -> None:
    """
    Activates focus mode by running the focus steps window.
    If is_modal is True, the window will be blocking.
    """
    LOG.info(f"🕌 Focus‑mode ON. Attempting to run focus steps window (modal={is_modal}).")
    from .focus_steps_view import run as run_focus_steps_window
    run_focus_steps_window(is_modal=is_modal)
    LOG.info("Focus steps window function called.")



# -- audio playback ---

# -- audio playback ---

def play(audio_path: str) -> None:
    """
    Plays the given audio file using a suitable method for the current platform.
    This is a blocking call.
    """
    if not os.path.exists(audio_path):
        LOG.error(f"Audio file not found: {audio_path}")
        return

    if sys.platform.startswith('linux'):
        LOG.info(f"📢 Attempting to play audio using 'aplay': {audio_path}")
        try:
            subprocess.run(['aplay', audio_path], check=True)
            LOG.info("Playback finished successfully via 'aplay'.")
        except subprocess.CalledProcessError as e:
            LOG.error(f"aplay failed with error: {e}")
        except FileNotFoundError:
            LOG.error("aplay command not found. Please ensure alsa-utils is installed.")
        except Exception as e:
            LOG.error(f"An unexpected error occurred during aplay execution: {e}")
    else:
        # Fallback to playsound for other platforms (macOS, Windows)
        from playsound import playsound
        LOG.info(f"📢 Attempting to play audio using 'playsound': {audio_path}")
        try:
            playsound(audio_path)
            LOG.info("Playback finished successfully via 'playsound'.")
        except Exception as e:
            LOG.error(f"An unexpected error occurred during playsound execution: {e}")
