# ------------------------------------------------------------------------
# scheduler.py – orchestrates one full day, prevents duplicates
# ------------------------------------------------------------------------
from __future__ import annotations
from datetime import datetime, timedelta, date
from typing import Dict, Set
from importlib import resources

from apscheduler.schedulers.blocking import BlockingScheduler

from .config import TZ, BUSY_SLOT, FOCUS_DELAY, LOG
from .calendar_utils import first_free_gap, add_busy_block
from .prayer_times import today_times
from .actions import play, focus_mode

def duaa_path() -> str:
    """Safely retrieves the path to the duaa audio file."""
    try:
        with resources.path('prayer.assets', 'duaa_after_adhan.wav') as p:
            return str(p)
    except FileNotFoundError:
        LOG.error("Duaa audio file not found.")
        return ""

class PrayerScheduler:
    """
    Owns a BlockingScheduler and manages the scheduling of prayer-related events.
    It handles fetching prayer times, scheduling jobs, and preventing duplicates.
    """

    def __init__(self, audio_path: str):
        self.audio_path = audio_path
        self.scheduler = BlockingScheduler(timezone=TZ)
        self._duaa_audio_path = duaa_path() # Cache the path on init

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def refresh(self, *, city: str, country: str, method: int | None = None, school: int | None = None):
        """
        Wipes all existing jobs and schedules prayers for the current day.
        A daily refresh job is also scheduled to run shortly after midnight.
        This method is idempotent.
        """
        LOG.info("Refreshing prayer schedule for %s, %s", city, country)
        self.scheduler.remove_all_jobs()
        
        times = today_times(city, country, method, school)
        self._schedule_day(times)

        # Arguments for keyword-only parameters must be passed via `kwargs`.
        job_kwargs = {"city": city, "country": country}
        if method is not None:
            job_kwargs["method"] = method
        if school is not None:
            job_kwargs["school"] = school

        self.scheduler.add_job(
            self.refresh,
            "cron",
            hour=0,
            minute=5,
            id="daily-refresh",
            replace_existing=True,
            kwargs=job_kwargs
        )
        LOG.info("Daily refresh job scheduled for 00:05.")

    def run(self):
        """Starts the scheduler's blocking loop."""
        LOG.info("Starting prayer scheduler...")
        self.scheduler.start()

    # -----------------------------------------------------------------
    # Action Wrappers (for cleaner scheduling and testing)
    # -----------------------------------------------------------------
    def play_adhan(self, audio_path: str):
        """Wrapper for the play action for adhan."""
        LOG.info("Playing adhan...")
        play(audio_path)

    def play_duaa(self):
        """Wrapper for the play action for duaa."""
        if self._duaa_audio_path:
            LOG.info("Playing duaa...")
            play(self._duaa_audio_path)

    def trigger_focus_mode(self):
        """Wrapper for the focus_mode action."""
        LOG.info("Triggering focus mode.")
        focus_mode()

    # -----------------------------------------------------------------
    # Internal Scheduling Logic
    # -----------------------------------------------------------------
    def _schedule_day(self, times: Dict[str, datetime]):
        """Schedules all prayer-related jobs for the given times."""
        now = datetime.now(TZ)
        LOG.debug("Scheduling for today. Current time: %s", now.strftime('%H:%M'))
        
        for name, at in sorted(times.items()):
            # --- Validation and Filtering ---
            if name in {"Sunrise", "Firstthird", "Lastthird"}:
                continue
            
            if at < now:
                LOG.debug("Skipping past prayer: %s at %s", name, at.strftime('%H:%M'))
                continue

            # --- Calendar Integration ---
            slot = first_free_gap(at, BUSY_SLOT.total_seconds() / 60)
            if slot is None:
                LOG.warning("Could not find a free calendar gap for %s around %s", name, at.strftime('%H:%M'))
                continue
            
            if not add_busy_block(slot, name, BUSY_SLOT.total_seconds() / 60):
                LOG.info("Skipping %s, as it's already in the external calendar.", name)
                # continue # This would skip scheduling if already in the calender, but we want to schedule anyway.

            # --- Job Scheduling ---
            job_base_id = f"{name}-{slot:%Y%m%d%H%M}"
            
            # 1. Adhan
            self.scheduler.add_job(
                self.play_adhan, "date", run_date=slot,
                id=f"adhan-{job_base_id}", args=[self.audio_path], misfire_grace_time=None
            )
            LOG.info("🗓️  %-8s adhan at %s", name, slot.strftime("%H:%M"))

            # 2. Duaa
            duaa_time = slot + timedelta(minutes=2, seconds=53)
            self.scheduler.add_job(
                self.play_duaa, "date", run_date=duaa_time,
                id=f"duaa-{job_base_id}"
            )

            # 3. Focus Mode
            focus_time = slot + FOCUS_DELAY
            self.scheduler.add_job(
                self.trigger_focus_mode, "date", run_date=focus_time,
                id=f"focus-{job_base_id}"
            )
            LOG.info("🗓️  %-8s focus at %s", name, focus_time.strftime("%H:%M"))
