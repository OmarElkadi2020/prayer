# ---------------------------------------------------------------------------
# actions.py – shell helpers, focus‑mode, audio playback
# ---------------------------------------------------------------------------
import os
import subprocess

from src.config.security import LOG
from .focus_steps import run as run_focus_steps_window


# -- focus mode -----------------------------------------------------------

def focus_mode(is_modal: bool = False) -> None:
    """
    Activates focus mode by running the focus steps window.
    If is_modal is True, the window will be blocking.
    """
    LOG.info(f"🕌 Focus‑mode ON. Attempting to run focus steps window (modal={is_modal}).")
    run_focus_steps_window(is_modal=is_modal)
    LOG.info("Focus steps window function called.")

# -- audio playback ---

def play(audio_path: str) -> None:
    """
    Plays the given audio file using the system's 'aplay' command for reliability.
    This is a blocking call and is intended for .wav files.
    """
    LOG.info(f"📢 Attempting to play audio using 'aplay': {audio_path}")
    if not os.path.exists(audio_path):
        LOG.error(f"Audio file not found: {audio_path}")
        return

    # Ensure the command is only used for .wav files
    if not str(audio_path).lower().endswith('.wav'):
        LOG.error(f"Playback via 'aplay' only supports .wav files. Cannot play '{audio_path}'.")
        return

    try:
        # Execute 'aplay' command. This is a blocking call.
        # We do not capture output to avoid potential deadlocks if the buffer fills.
        # Let aplay write directly to the system's stdout/stderr.
        subprocess.run(
            ['aplay', audio_path],
            check=True,        # Raise an exception if aplay returns a non-zero exit code
        )
        LOG.info("Playback finished successfully via 'aplay'.")

    except FileNotFoundError:
        LOG.error("The 'aplay' command was not found. Please install 'alsa-utils' on your system.")
    except subprocess.CalledProcessError as e:
        # This will now have no stderr to print, but we can still log the error
        LOG.error(f"Error playing audio with 'aplay'. Exit code: {e.returncode}")
    except Exception as e:
        LOG.error(f"An unexpected error occurred during 'aplay' execution: {e}")
