# ------------------------------------------------------------------------
# scheduler.py – orchestrates one full day, prevents duplicates
# ------------------------------------------------------------------------
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Dict
from importlib import resources
import threading
import time

from apscheduler.schedulers.background import BackgroundScheduler

from .config import TZ, BUSY_SLOT, FOCUS_DELAY, LOG, load_config, adhan_path
from .calendar_utils import first_free_gap, add_busy_block
from .prayer_times import today_times
from .actions import play, focus_mode
from .state import state_manager, AppState

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
    Owns a BackgroundScheduler and manages the scheduling of prayer-related events.
    It handles fetching prayer times, scheduling jobs, and preventing duplicates.
    """

    def __init__(self, audio_path: str):
        self.audio_path = audio_path
        self.scheduler = BackgroundScheduler(timezone=TZ)
        self._duaa_audio_path = duaa_path() # Cache the path on init

    def refresh(self, *, city: str, country: str, method: int | None = None, school: int | None = None):
        """
        Wipes all existing jobs and schedules prayers for the current day.
        A daily refresh job is also scheduled to run shortly after midnight.
        This method is idempotent.
        """
        state_manager.state = AppState.SYNCING
        LOG.info("Refreshing prayer schedule for %s, %s", city, country)
        self.scheduler.remove_all_jobs()
        LOG.info("All previous jobs cleared.")
        
        try:
            times = today_times(city, country, method, school)
            LOG.info("Today's prayer times: %s", times)
            self._schedule_day(times)
            LOG.info("All prayer jobs for today added to the scheduler.")

            # Update next prayer info
            self._update_next_prayer_info()

            job_kwargs = {"city": city, "country": country}
            if method is not None:
                job_kwargs["method"] = method
            if school is not None:
                job_kwargs["school"] = school

            self.scheduler.add_job(
                self.refresh, "cron", hour=0, minute=5,
                id="daily-refresh", replace_existing=True, kwargs=job_kwargs
            )
            LOG.info("Next daily refresh job at 00:05 added to the scheduler.")
        except Exception as e:
            LOG.error(f"An error occurred during refresh: {e}")
            state_manager.state = AppState.ERROR
        else:
            state_manager.state = AppState.IDLE

    def run(self):
        """Starts the scheduler's background loop."""
        if not self.scheduler.running:
            LOG.info("Starting scheduler to fire jobs in the background.")
            self.scheduler.start()
        else:
            LOG.info("Scheduler is already running.")

    def play_adhan_and_duaa(self, audio_path: str):
        """A combined action to play adhan, set state, and play duaa after a delay."""
        state_manager.state = AppState.PRAYER_TIME
        LOG.info("Playing adhan...")
        play(audio_path)
        
        # This is a blocking delay, which is simple for this use case.
        # Adhan duration is roughly 2m 53s.
        time.sleep(173) 
        
        if self._duaa_audio_path:
            LOG.info("Playing duaa...")
            play(self._duaa_audio_path)
        
        state_manager.state = AppState.IDLE
        # After the prayer, we need to find the *next* one.
        self._update_next_prayer_info()

    def trigger_focus_mode(self):
        """Wrapper for the focus_mode action."""
        LOG.info("Triggering focus mode.")
        focus_mode()

    def _schedule_day(self, times: Dict[str, datetime]):
        """Schedules all prayer-related jobs for the given times."""
        now = datetime.now(TZ)
        LOG.debug("Scheduling for today. Current time: %s", now.strftime('%H:%M'))
        
        for name, at in sorted(times.items()):
            if name in {"Sunrise", "Firstthird", "Lastthird"}:
                continue
            
            if at < now:
                LOG.debug("Skipping past prayer: %s at %s", name, at.strftime('%H:%M'))
                continue

            slot = first_free_gap(at, BUSY_SLOT.total_seconds() / 60)
            if slot is None:
                LOG.warning("Could not find a free calendar gap for %s around %s", name, at.strftime('%H:%M'))
                continue
            
            if not add_busy_block(slot, name, BUSY_SLOT.total_seconds() / 60):
                LOG.info("Skipping %s, as it's already in the external calendar.", name)
                continue

            job_base_id = f"{name}-{slot:%Y%m%d%H%M}"
            
            # Schedule the combined adhan and duaa job
            self.scheduler.add_job(
                self.play_adhan_and_duaa, "date", run_date=slot,
                id=f"prayer-{job_base_id}", args=[self.audio_path], misfire_grace_time=None
            )
            LOG.info("🗓️  %-8s prayer at %s", name, slot.strftime("%H:%M"))

            # Schedule Focus Mode
            focus_time = slot + FOCUS_DELAY
            self.scheduler.add_job(
                self.trigger_focus_mode, "date", run_date=focus_time,
                id=f"focus-{job_base_id}"
            )
            LOG.info("🗓️  %-8s focus at %s", name, focus_time.strftime("%H:%M"))

    def _update_next_prayer_info(self):
        """Finds the next scheduled prayer and updates the state manager."""
        now = datetime.now(TZ)
        next_prayer_job = None
        
        all_jobs = self.scheduler.get_jobs()
        # Filter for prayer jobs and find the soonest one in the future
        prayer_jobs = sorted(
            [j for j in all_jobs if j.id.startswith('prayer-') and j.next_run_time > now],
            key=lambda j: j.next_run_time
        )
        
        if prayer_jobs:
            next_prayer_job = prayer_jobs[0]
            # Extract prayer name from job id: "prayer-Asr-202401011530" -> "Asr"
            try:
                prayer_name = next_prayer_job.id.split('-')[1]
                info = f"{prayer_name} at {next_prayer_job.next_run_time.strftime('%H:%M')}"
                state_manager.next_prayer_info = info
                LOG.info(f"Next prayer updated: {info}")
            except IndexError:
                LOG.warning(f"Could not parse prayer name from job ID: {next_prayer_job.id}")
                state_manager.next_prayer_info = "Error"
        else:
            state_manager.next_prayer_info = "No upcoming prayers"
            LOG.info("No upcoming prayers scheduled for today.")

# --- Singleton instance for the scheduler ---
_scheduler_instance: PrayerScheduler | None = None
_scheduler_lock = threading.Lock()

def get_scheduler_instance() -> PrayerScheduler:
    """Initializes and returns a singleton PrayerScheduler instance."""
    global _scheduler_instance
    with _scheduler_lock:
        if _scheduler_instance is None:
            audio = adhan_path()
            _scheduler_instance = PrayerScheduler(audio_path=audio)
    return _scheduler_instance

def run_scheduler_in_thread(one_time_run: bool = False):
    """
    Main entry point for managing the scheduler.
    Runs the scheduler in a background thread or performs a one-time sync.
    """
    def scheduler_job():
        config = load_config()
        
        if not config.get('city') or not config.get('country'):
            LOG.warning("Scheduler cannot run without city/country configuration.")
            state_manager.state = AppState.ERROR
            state_manager.next_prayer_info = "Configure location"
            return

        scheduler = get_scheduler_instance()
        method = config.get('method')
        school = config.get('school')
        scheduler.refresh(city=config['city'], country=config['country'], method=method, school=school)
        
        if not one_time_run:
            scheduler.run()

    job_thread = threading.Thread(target=scheduler_job, daemon=True)
    job_thread.start()
