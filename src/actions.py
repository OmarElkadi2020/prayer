# ---------------------------------------------------------------------------
# actions.py – shell helpers, focus‑mode, audio playback
# ---------------------------------------------------------------------------
import os
import subprocess

from src.config.security import LOG
from src.qt_utils import run_in_qt_thread


# -- focus mode -----------------------------------------------------------

@run_in_qt_thread
def trigger_focus_mode():
    """Triggers focus mode, ensuring it runs on the Qt GUI thread."""
    LOG.info("Triggering focus mode for GUI.")
    from src.focus_steps_view import FocusStepsView # Import locally to avoid circular dependency
    from src.presenter.focus_steps_presenter import FocusStepsPresenter
    # We need to hold a reference to the window, otherwise it might get garbage collected
    if not hasattr(trigger_focus_mode, "_focus_window_instance") or not trigger_focus_mode._focus_window_instance.isVisible():
        presenter = FocusStepsPresenter()
        trigger_focus_mode._focus_window_instance = FocusStepsView(presenter, disable_sound=True) # Disable sound to avoid double sound with adhan
        trigger_focus_mode._focus_window_instance.show()
        trigger_focus_mode._focus_window_instance.activateWindow()
    else:
        trigger_focus_mode._focus_window_instance.activateWindow()


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

from playsound import playsound

# -- audio playback ---

def play(audio_path: str) -> None:
    """
    Plays the given audio file using the 'playsound' library for cross-platform support.
    This is a blocking call.
    """
    LOG.info(f"📢 Attempting to play audio using 'playsound': {audio_path}")
    if not os.path.exists(audio_path):
        LOG.error(f"Audio file not found: {audio_path}")
        return

    try:
        playsound(audio_path)
        LOG.info("Playback finished successfully via 'playsound'.")
    except Exception as e:
        LOG.error(f"An unexpected error occurred during 'playsound' execution: {e}")
