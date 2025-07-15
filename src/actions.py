# ---------------------------------------------------------------------------
# actions.py – shell helpers, focus‑mode, audio playback
# ---------------------------------------------------------------------------
import os
from pydub import AudioSegment
from pydub.playback import play as pydub_play

from src.config.security import LOG
from .focus_steps import run as run_focus_steps_window


# -- focus mode -----------------------------------------------------------

def focus_mode() -> None:
    """
    Activates focus mode by running the focus steps window.
    """
    LOG.info("🕌 Focus‑mode ON. Attempting to run focus steps window.")
    run_focus_steps_window()
    LOG.info("Focus steps window function called.")

# -- audio playback ---

def play(audio_path: str) -> None:
    """
    Plays the given audio file using pydub.
    """
    LOG.info(f"📢 Playing {audio_path}")
    if not os.path.exists(audio_path):
        LOG.error(f"Audio file not found: {audio_path}")
        return
    try:
        audio = AudioSegment.from_file(audio_path)
        pydub_play(audio)
        LOG.info("Playback finished.")
    except Exception as e:
        LOG.error(f"Error playing audio with pydub: {e}")
