# ------------------------------------------------------------------------
# scheduler.py – orchestrates one full day, prevents duplicates
# ------------------------------------------------------------------------
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Dict, Optional, TYPE_CHECKING
from importlib import resources
import threading
import time

from apscheduler.schedulers.background import BackgroundScheduler

from src.config.security import TZ, BUSY_SLOT, FOCUS_DELAY, LOG, load_config, adhan_path, get_asset_path
from src.qt_utils import run_in_qt_thread

from .prayer_times import today_times
from .actions import play, focus_mode
from .state import state_manager, AppState

if TYPE_CHECKING:
    from src.calendar_api.base import CalendarService

def duaa_path() -> str:
    """Safely retrieves the path to the duaa audio file."""
    try:
        return str(get_asset_path('duaa_after_adhan.wav'))
    except FileNotFoundError:
        LOG.error("Duaa audio file not found.")
        return ""

class PrayerScheduler:
    """
    Owns a BackgroundScheduler and manages the scheduling of prayer-related events.
    It handles fetching prayer times, scheduling jobs, and preventing duplicates.
    """

    def __init__(self, audio_path: str, calendar_service: Optional[CalendarService]):
        self.audio_path = audio_path
        job_defaults = {
            'misfire_grace_time': None
        }
        self.scheduler = BackgroundScheduler(timezone=TZ, job_defaults=job_defaults)
        self._duaa_audio_path = duaa_path() # Cache the path on init
        self.calendar_service = calendar_service
        self._focus_window_instance = None # To hold a strong reference to the focus window

    def set_audio_path(self, audio_path: str):
        """Sets a new path for the audio file for the scheduler instance."""
        LOG.info(f"Scheduler audio path updated to: {audio_path}")
        self.audio_path = audio_path

    def refresh(self, *, city: str, country: str, method: int | None = None, school: int | None = None, dry_run: bool = False, dry_run_event: Optional[threading.Event] = None):
        """
        Wipes all existing jobs and schedules prayers for the current day.
        A daily refresh job is also scheduled to run shortly after midnight.
        This method is idempotent.
        """
        state_manager.state = AppState.SYNCING
        LOG.info(f"Refreshing prayer schedule for {city}, {country}")
        self.scheduler.remove_all_jobs()
        LOG.info("All previous jobs cleared.")
        
        try:
            times = today_times(city, country, method, school)
            LOG.info(f"Today's prayer times: {times}")
            self._schedule_day(times, dry_run)
            LOG.info("All prayer jobs for today added to the scheduler.")

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
            if dry_run:
                state_manager.next_prayer_info = "Dry run: Prayer scheduled for immediate execution"
            else:
                self._update_next_prayer_info()

    def run(self):
        """Starts the scheduler's background loop."""
        if not self.scheduler.running:
            LOG.info("Starting scheduler to fire jobs in the background.")
            self.scheduler.start()
        else:
            LOG.info("Scheduler is already running.")

    @run_in_qt_thread
    def trigger_focus_mode(self):
        """Triggers focus mode, ensuring it runs on the Qt GUI thread."""
        LOG.info("Triggering focus mode for GUI.")
        if self._focus_window_instance is None or not self._focus_window_instance.isVisible():
            from src.focus_steps import StepWindow # Import locally to avoid circular dependency
            self._focus_window_instance = StepWindow(disable_sound=True) # Disable sound to avoid double sound with adhan
            self._focus_window_instance.show()
            self._focus_window_instance.activateWindow()
        else:
            self._focus_window_instance.activateWindow()

    def play_adhan_and_duaa(self, audio_path: str, is_dry_run: bool = False):
        """
        A combined action to play adhan and duaa.
        - In GUI mode, it then triggers the non-blocking focus window.
        - In dry-run mode, it sets an event to signal completion to the main thread.
        """
        LOG.info("Executing play_adhan_and_duaa for scheduled job.")
        state_manager.state = AppState.PRAYER_TIME
        
        try:
            LOG.info(f"Playing adhan: {audio_path}")
            play(audio_path)

            if self._duaa_audio_path:
                LOG.info(f"Playing duaa: {self._duaa_audio_path}")
                play(self._duaa_audio_path)
            else:
                LOG.warning("Duaa audio path not found. Skipping duaa.")
            
            LOG.info("Audio finished.")

        except Exception as e:
            LOG.error(f"Error during audio playback or focus mode trigger: {e}")
        
        finally:
            LOG.info("Playback sequence complete. Setting state to IDLE.")
            state_manager.state = AppState.IDLE
            self._update_next_prayer_info()

    def run_dry_run_simulation(self, city: str, country: str, method: Optional[int], school: Optional[int]):
        """
        Executes a one-time dry run simulation of a prayer time, including audio playback.
        This method blocks until the dry run audio sequence is complete.
        """
        LOG.info("Executing dry run simulation.")
        audio_finished_event = threading.Event()

        # For dry run, use the short completion sound instead of the full adhan
        from src.config.security import get_asset_path
        dry_run_audio_path = str(get_asset_path('complete_sound.wav'))
        self.set_audio_path(dry_run_audio_path)

        self.refresh(
            city=city,
            country=country,
            method=method,
            school=school,
            dry_run=True,
            dry_run_event=audio_finished_event
        )
        self.run() # Start the scheduler to execute the job

        LOG.info("Waiting for dry run job to execute and audio to play...")
        event_was_set = audio_finished_event.wait(timeout=90) # Wait up to 90s

        if not event_was_set:
            LOG.warning("Dry run timed out waiting for audio to finish.")
        
        LOG.info("Dry run simulation finished.")

    def _schedule_single_prayer_job(self, name: str, at: datetime, is_dry_run: bool):
        """
        Schedules a single prayer job.
        """
        job_base_id = f"{name}-{at.strftime('%Y%m%d%H%M%S')}" if is_dry_run else f"{name}-{at.strftime('%Y%m%d%H%M')}"

        job_kwargs = {
            'audio_path': self.audio_path,
            'is_dry_run': is_dry_run
        }
        self.trigger_focus_mode() # Trigger focus mode before audio
        self.scheduler.add_job(
            self.play_adhan_and_duaa, "date", run_date=at,
            id=f"prayer-{job_base_id}", kwargs=job_kwargs
        )
        if is_dry_run:
            LOG.info(f"🗓️  Dry run prayer simulation scheduled at {at.strftime('%H:%M:%S')}")
        else:
            LOG.info(f"🗓️  {name:<8s} prayer and focus sequence at {at.strftime('%H:%M')}")

    def _schedule_day(self, times: Dict[str, datetime], dry_run: bool = False):
        """
        Schedules all prayer-related jobs for the given times.
        Passes the dry_run_event to the job if in dry_run mode.
        """
        now = datetime.now(TZ)
        LOG.debug(f"Scheduling for today. Current time: {now.strftime('%H:%M')}")

        if dry_run:
            LOG.info("Dry run mode activated. Scheduling immediate test prayer.")
            slot = now + timedelta(seconds=5)
            job_base_id = f"dry-run-{slot.strftime('%Y%m%d%H%M%S')}"

            self._schedule_single_prayer_job(
                name="dry-run",
                at=slot,
                is_dry_run=True
            )
            LOG.info(f"🗓️  Dry run prayer and focus sequence scheduled at {slot.strftime('%H:%M:%S')}")
            return

        for name, at in sorted(times.items()):
            if name in {"Sunrise", "Firstthird", "Lastthird"}:
                continue

            if at < now:
                LOG.debug(f"Skipping past prayer: {name} at {at.strftime('%H:%M')}")
                continue

            slot = at

            if self.calendar_service:
                if not self.calendar_service.add_event(
                    start_time=at,
                    summary=name,
                    duration_minutes=BUSY_SLOT.total_seconds() / 60
                ):
                    LOG.info(f"Skipping scheduling for {name} as it's already in the external calendar.")
                    continue
            else:
                LOG.info("Calendar service not active. Scheduling prayer without calendar check.")

            self._schedule_single_prayer_job(
                name=name,
                at=slot,
                is_dry_run=False
            )

    def _update_next_prayer_info(self):
        """Finds the next scheduled prayer and updates the state manager."""
        now = datetime.now(TZ)
        next_prayer_job = None
        
        all_jobs = self.scheduler.get_jobs()
        prayer_jobs = sorted(
            [j for j in all_jobs if j.id.startswith('prayer-') and getattr(j, 'next_run_time', None) and j.next_run_time >= now],
            key=lambda j: j.next_run_time
        )
        
        if prayer_jobs:
            next_prayer_job = prayer_jobs[0]
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

def get_scheduler_instance(calendar_service: Optional[CalendarService] = None) -> PrayerScheduler:
    """Initializes and returns a singleton PrayerScheduler instance."""
    global _scheduler_instance
    with _scheduler_lock:
        if _scheduler_instance is None:
            audio = adhan_path()
            _scheduler_instance = PrayerScheduler(audio_path=audio, calendar_service=calendar_service)
        elif calendar_service is not None and _scheduler_instance.calendar_service is None:
            # If scheduler already exists but calendar service wasn't set, set it now.
            _scheduler_instance.calendar_service = calendar_service
    return _scheduler_instance

def run_scheduler_in_thread(one_time_run: bool = False, calendar_service: Optional[CalendarService] = None, dry_run: bool = False):
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

        scheduler = get_scheduler_instance(calendar_service)
        method = config.get('method')
        school = config.get('school')
        scheduler.refresh(city=config['city'], country=config['country'], method=method, school=school, dry_run=dry_run)
        
        if not one_time_run:
            scheduler.run()

    job_thread = threading.Thread(target=scheduler_job, daemon=True)
    job_thread.start()


