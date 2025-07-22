# ------------------------------------------------------------------------
# scheduler.py – orchestrates one full day, prevents duplicates
# ------------------------------------------------------------------------
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Dict, Optional, TYPE_CHECKING
import threading

from apscheduler.schedulers.background import BackgroundScheduler

from src.config.security import TZ, BUSY_SLOT, LOG
from src.qt_utils import run_in_qt_thread
from src.actions_executor import ActionExecutor, DryRunActionExecutor
from src.shared.event_bus import EventBus
from src.domain.config_messages import ConfigurationChangedEvent
from src.domain.enums import AppState
from src.domain.scheduler_messages import ApplicationStateChangedEvent, ScheduleRefreshedEvent
from src.shared.commands import SimulatePrayerCommand


if TYPE_CHECKING:
    from src.calendar_api.base import CalendarService

class PrayerScheduler:
    """
    Owns a BackgroundScheduler and manages the scheduling of prayer-related events.
    It handles fetching prayer times, scheduling jobs, and preventing duplicates.
    """

    def __init__(self, audio_path: str, calendar_service: Optional[CalendarService], prayer_times_func, action_executor: ActionExecutor, event_bus: EventBus):
        self.audio_path = audio_path
        self.calendar_service = calendar_service
        self.prayer_times_func = prayer_times_func
        self.action_executor = action_executor
        self.event_bus = event_bus
        job_defaults = {
            'misfire_grace_time': None
        }
        self.scheduler = BackgroundScheduler(timezone=TZ, job_defaults=job_defaults)

        self.event_bus.register(ConfigurationChangedEvent, self._handle_config_change)
        self.event_bus.register(SimulatePrayerCommand, self._handle_simulate_prayer_command)


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
        self.event_bus.publish(ApplicationStateChangedEvent(new_state=AppState.SYNCING))
        LOG.info(f"Refreshing prayer schedule for {city}, {country}")
        self.scheduler.remove_all_jobs()
        LOG.info("All previous jobs cleared.")
        
        if dry_run and dry_run_event:
            self.action_executor.set_dry_run_event(dry_run_event)

        try:
            times = self.prayer_times_func(city, country, method, school)
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
            self.event_bus.publish(ApplicationStateChangedEvent(new_state=AppState.ERROR))
        else:
            self.event_bus.publish(ApplicationStateChangedEvent(new_state=AppState.IDLE))
            if dry_run:
                self.event_bus.publish(ScheduleRefreshedEvent(next_prayer_info="Dry run: Prayer scheduled for immediate execution"))
            else:
                self._update_next_prayer_info()

    def run(self):
        """Starts the scheduler's background loop."""
        if not self.scheduler.running:
            LOG.info("Starting scheduler to fire jobs in the background.")
            self.scheduler.start()
        else:
            LOG.info("Scheduler is already running.")

    def play_adhan_and_duaa(self):
        """
        A combined action to play adhan and duaa.
        """
        LOG.info("Executing play_adhan_and_duaa for scheduled job.")
        self.event_bus.publish(ApplicationStateChangedEvent(new_state=AppState.PRAYER_TIME))
        
        try:
            from src.config.security import get_asset_path
            adhan_path = str(get_asset_path('adhan.wav'))
            duaa_path = str(get_asset_path('duaa_after_adhan.wav'))

            LOG.info(f"Playing Adhan from {adhan_path}")
            self.action_executor.play_audio(adhan_path)
            LOG.info("Adhan finished. Playing Duaa.")
            self.action_executor.play_audio(duaa_path)
            LOG.info("Duaa finished.")

        except Exception as e:
            LOG.error(f"Error during audio playback or focus mode trigger: {e}")
        
        finally:
            LOG.info("Playback sequence complete. Setting state to IDLE.")
            self.event_bus.publish(ApplicationStateChangedEvent(new_state=AppState.IDLE))
            # Do not update GUI components in a dry run, as there is no GUI.
            # This also prevents a race condition on scheduler shutdown.
            if not isinstance(self.action_executor, DryRunActionExecutor):
                self._update_next_prayer_info()

    def run_dry_run_simulation(self, city: str, country: str, method: Optional[int], school: Optional[int]):
        """
        Executes a one-time dry run simulation of a prayer time, including audio playback.
        This method blocks until the dry run audio sequence is complete.
        """
        LOG.info("Executing dry run simulation.")
        audio_finished_event = threading.Event()

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
        self.run()

        try:
            LOG.info("Waiting for dry run job to execute and audio to play...")
            event_was_set = audio_finished_event.wait(timeout=90)

            if not event_was_set:
                LOG.warning("Dry run timed out waiting for audio to finish.")
        finally:
            LOG.info("Shutting down scheduler after dry run.")
            self.scheduler.shutdown()
            LOG.info("Dry run simulation finished.")

    def _schedule_single_prayer_job(self, name: str, at: datetime, is_dry_run: bool):
        """
        Schedules a single prayer job.
        """
        job_base_id = f"{name}-{at.strftime('%Y%m%d%H%M%S')}" if is_dry_run else f"{name}-{at.strftime('%Y%m%d%H%M')}"

        self.scheduler.add_job(
            self.action_executor.trigger_focus_mode, "date", run_date=at - timedelta(seconds=10)
        )
        self.scheduler.add_job(
            self.play_adhan_and_duaa, "date", run_date=at,
            id=f"prayer-{job_base_id}"
        )
        if is_dry_run:
            LOG.info(f"Dry run prayer simulation scheduled at {at.strftime('%H:%M:%S')}")
        else:
            LOG.info(f"🗓️  {name:<8s} prayer and focus sequence at {at.strftime('%H:%M')}")

    def _schedule_day(self, times: Dict[str, datetime], dry_run: bool = False):
        """
        Schedules all prayer-related jobs for the given times.
        """
        now = datetime.now(TZ)
        LOG.debug(f"Scheduling for today. Current time: {now.strftime('%H:%M')}")

        if dry_run:
            LOG.info("Dry run mode activated. Scheduling immediate test prayer.")
            slot = now + timedelta(seconds=5)
            self._schedule_single_prayer_job(
                name="dry-run",
                at=slot,
                is_dry_run=True
            )
            LOG.info(f"Dry run prayer and focus sequence scheduled at {slot.strftime('%H:%M:%S')}")
            return

        # Sort by time, not by name, to process chronologically
        for name, at in sorted(times.items(), key=lambda item: item[1]):
            if name in {"Sunrise", "Firstthird", "Lastthird"}:
                continue

            if at < now:
                LOG.debug(f"Skipping past prayer: {name} at {at.strftime('%H:%M')}")
                continue

            slot = at

            if self.calendar_service:
                LOG.debug(f"Attempting to add calendar event for {name} at {at}")
                try:
                    self.calendar_service.add_event(
                        start_time=at,
                        summary=name,
                        duration_minutes=BUSY_SLOT.total_seconds() / 60
                    )
                except Exception as e:
                    LOG.error(f"Failed to add event to calendar for {name}: {e}")
            else:
                LOG.info("Calendar service not active. Skipping calendar event creation.")

            self._schedule_single_prayer_job(
                name=name,
                at=slot,
                is_dry_run=False
            )

    @run_in_qt_thread
    def _update_next_prayer_info(self):
        """
        Finds the next scheduled prayer and updates the state manager.
        This is run in the Qt thread to prevent race conditions with the scheduler.
        """
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
                self.event_bus.publish(ScheduleRefreshedEvent(next_prayer_info=info))
                LOG.info(f"Next prayer updated: {info}")
            except IndexError:
                LOG.warning(f"Could not parse prayer name from job ID: {next_prayer_job.id}")
                self.event_bus.publish(ScheduleRefreshedEvent(next_prayer_info="Error"))
        else:
            self.event_bus.publish(ScheduleRefreshedEvent(next_prayer_info="No upcoming prayers"))
            LOG.info("No upcoming prayers scheduled for today.")

    def _handle_config_change(self, event: ConfigurationChangedEvent):
        LOG.info("ConfigurationChangedEvent received, refreshing schedule.")
        config = event.config
        if config.city and config.country:
            self.refresh(
                city=config.city,
                country=config.country,
                method=config.method,
                school=config.school
            )
        else:
            LOG.warning("Cannot refresh schedule, city or country not provided in config change event.")

    def _handle_simulate_prayer_command(self, command: SimulatePrayerCommand):
        LOG.info(f"Received SimulatePrayerCommand for {command.prayer_name}.")
        now = datetime.now(TZ)
        # Schedule the simulation 5 seconds from now
        simulation_time = now + timedelta(seconds=5)
        self._schedule_single_prayer_job(
            name=f"simulated-{command.prayer_name}",
            at=simulation_time,
            is_dry_run=True # Use dry_run=True for simulation
        )
        LOG.info(f"Scheduled simulated {command.prayer_name} prayer for {simulation_time.strftime('%H:%M:%S')}.")
        self.event_bus.publish(ScheduleRefreshedEvent(next_prayer_info=f"Simulated {command.prayer_name} at {simulation_time.strftime('%H:%M:%S')}"))