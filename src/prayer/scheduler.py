# ------------------------------------------------------------------------
# scheduler.py – orchestrates one full day, prevents duplicates
# ------------------------------------------------------------------------
from __future__ import annotations
from datetime import datetime, timedelta, date
from typing import Dict, Set
from importlib import resources

from apscheduler.schedulers.blocking import BlockingScheduler

from .config import TZ, BUSY_SLOT, POST_DELAY, FOCUS_DELAY, LOG
from .calendar_utils import first_free_gap, add_busy_block
from .prayer_times import today_times
from .actions import play, focus_mode

def duaa_path():
    with resources.path('prayer.assets', 'duaa_after_adhan.wav') as p:
        return str(p)

class PrayerScheduler:
    """Owns a BlockingScheduler + duplicate tracking for the running process."""

    def __init__(self, audio_cmd: str):
        self.audio_cmd = audio_cmd
        self.scheduler = BlockingScheduler(timezone=TZ)
        self._scheduled: Set[tuple[str, date]] = set()

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def refresh(self, *, city: str, country: str, method: int, school: int):
        """Wipe existing jobs (except this refresh) and schedule prayers for today.
        Duplicate names for the same date are skipped *globally* across refreshes."""
        for job in self.scheduler.get_jobs():
            if job.id != "daily-refresh":
                self.scheduler.remove_job(job.id)

        times = today_times(city, country, method, school)
        self._schedule_day(times)

    def run(self):
        self.scheduler.start()

    # -----------------------------------------------------------------
    # internals
    # -----------------------------------------------------------------
    def _schedule_day(self, times: Dict[str, datetime]):
        now = datetime.now(TZ)

        for name, at in times.items():
            if name in {"Sunrise", "Lastthird", "Firstthird"}:
                continue
            if at < now:
                continue
            
            day_key = (name, at.date())
            if day_key in self._scheduled:
                LOG.debug("Duplicate by scheduler memory: %s on %s", name, at.date())
                continue

            # Find the first available slot
            slot = first_free_gap(at, BUSY_SLOT.total_seconds() / 60)
            
            if slot is None:
                LOG.warning("%s: no free gap", name)
                continue
            
            # Add a busy block to the calendar
            if not add_busy_block(slot, name, BUSY_SLOT.total_seconds() / 60):
                LOG.info("Skip %s – already in the calendar for %s", name, slot.date().isoformat())
                continue

            job_id = f"{name}-{slot:%Y%m%d%H%M}"
            self.scheduler.add_job(play, "date", run_date=slot, args=[self.audio_cmd], id="adhan-"+job_id, misfire_grace_time=None)
            LOG.info("🗓 %-8s adhan at %s", name, slot.strftime("%H:%M of %d.%m.%Y"))
            self.scheduler.add_job(play, "date", run_date=slot + timedelta(minutes=2, seconds=53), id="duaa-"+job_id, args=[f"ffplay -nodisp -autoexit -loglevel quiet '{duaa_path()}'"])
            focus_at = slot + FOCUS_DELAY
            self.scheduler.add_job(focus_mode, "date", run_date=focus_at, id=f"focus-"+job_id)
            LOG.info("🗓 %-8s focus at %s", name, focus_at.strftime("%H:%M of %d.%m.%Y"))
            self._scheduled.add(day_key)