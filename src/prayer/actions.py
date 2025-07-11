# ---------------------------------------------------------------------------
# actions.py – shell helpers, focus‑mode, audio playback
# ---------------------------------------------------------------------------

from __future__ import annotations
import sys, os
from datetime import datetime, timedelta
from typing import Set

from apscheduler.schedulers.blocking import BlockingScheduler
from playsound import playsound

from .config import TZ, LOG, FOCUS_DELAY, FOCUS_LENGTH
from .focus_steps import run as run_focus_steps_window


# -- focus mode -----------------------------------------------------------

def focus_mode(disable_network: bool = True):
    LOG.info("🕌 Focus‑mode ON.")
    # The network control functionality was removed for platform independence.
    # The focus steps window is now launched directly.
    run_focus_steps_window()

    # The scheduler part below is for network control, which is currently removed.
    # resume = datetime.now(TZ) + FOCUS_LENGTH
    # tmp_scheduler = BlockingScheduler(timezone=TZ)
    # tmp_scheduler.add_job(lambda: LOG.info("🌐 Network control functionality removed for platform independence."), "date", run_date=resume)
    # tmp_scheduler.start(paused=False)

# -- audio playback ---


def play(audio_path: str):
    LOG.info("📢 Playing %s", audio_path)
    try:
        playsound(audio_path)
    except Exception as e:
        LOG.error(f"Error playing audio with playsound: {e}")