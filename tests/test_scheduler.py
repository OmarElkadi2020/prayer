from src.domain.config_messages import ConfigurationChangedEvent
import unittest
from unittest.mock import Mock, patch, call
from datetime import datetime, timedelta
import threading

from src.scheduler import PrayerScheduler
from src.actions_executor import ActionExecutor
from src.shared.event_bus import EventBus
from src.domain.scheduler_messages import ScheduleRefreshedEvent, ApplicationStateChangedEvent
from src.domain.enums import AppState
from src.config.security import TZ
from src.config.schema import Config
from src.shared.commands import SimulatePrayerCommand

class TestPrayerScheduler(unittest.TestCase):

    def setUp(self):
        self.mock_event_bus = Mock(spec=EventBus)
        self.mock_calendar_service = Mock()
        self.mock_prayer_times_func = Mock()
        self.mock_action_executor = Mock(spec=ActionExecutor)
        self.mock_config_service = Mock()

        self.scheduler = PrayerScheduler(
            audio_path="dummy_path",
            event_bus=self.mock_event_bus,
            calendar_service=self.mock_calendar_service,
            prayer_times_func=self.mock_prayer_times_func,
            action_executor=self.mock_action_executor
        )

    def test_initialization(self):
        self.assertIsNotNone(self.scheduler.scheduler)
        self.assertEqual(self.scheduler.event_bus, self.mock_event_bus)
        self.assertEqual(self.scheduler.action_executor, self.mock_action_executor)
        expected_calls = [
            call(ConfigurationChangedEvent, self.scheduler._handle_config_change),
            call(SimulatePrayerCommand, self.scheduler._handle_simulate_prayer_command)
        ]
        self.mock_event_bus.register.assert_has_calls(expected_calls, any_order=True)

    @patch('src.scheduler.PrayerScheduler._update_next_prayer_info')
    def test_refresh_schedules_prayers(self, mock_update_next_prayer_info):
        mock_config = Mock(spec=Config)
        mock_config.city = "Test City"
        mock_config.country = "Test Country"
        mock_config.calculation_method = "ISNA"
        mock_config.adjust_methods = {}

        now = datetime.now(TZ)
        prayer_times = {
            "Fajr": now + timedelta(minutes=10),
            "Dhuhr": now + timedelta(hours=4),
        }
        self.mock_prayer_times_func.return_value = prayer_times

        self.scheduler.refresh(city=mock_config.city, country=mock_config.country, method=mock_config.calculation_method, school=mock_config.adjust_methods)

        self.mock_prayer_times_func.assert_called_once_with(
            mock_config.city,
            mock_config.country,
            mock_config.calculation_method,
            mock_config.adjust_methods
        )
        
        # 2 prayers * 2 jobs (focus + adhan) + 1 daily refresh job = 5
        self.assertEqual(len(self.scheduler.scheduler.get_jobs()), 5)
        self.mock_event_bus.publish.assert_has_calls([
            call(ApplicationStateChangedEvent(new_state=AppState.SYNCING)),
            call(ApplicationStateChangedEvent(new_state=AppState.IDLE))
        ])
        mock_update_next_prayer_info.assert_called_once()


    def test_refresh_dry_run(self):
        mock_config = Mock(spec=Config)
        mock_config.city = "Test City"
        mock_config.country = "Test Country"
        mock_config.calculation_method = "ISNA"
        mock_config.adjust_methods = {}

        dry_run_event = threading.Event()

        self.scheduler.refresh(city=mock_config.city, country=mock_config.country, method=mock_config.calculation_method, school=mock_config.adjust_methods, dry_run=True, dry_run_event=dry_run_event)

        self.mock_action_executor.set_dry_run_event.assert_called_once_with(dry_run_event)
        # 1 dry run job * 2 (focus + adhan) + 1 daily refresh job = 3
        self.assertEqual(len(self.scheduler.scheduler.get_jobs()), 3)

    def test_play_adhan_and_duaa(self):
        from src.config.security import get_asset_path

        self.scheduler.play_adhan_and_duaa()

        expected_calls = [
            call(str(get_asset_path('adhan.wav'))),
            call(str(get_asset_path('duaa_after_adhan.wav')))
        ]
        self.mock_action_executor.play_audio.assert_has_calls(expected_calls)
        self.mock_event_bus.publish.assert_called_with(ApplicationStateChangedEvent(new_state=AppState.IDLE))

    def test_schedule_single_prayer_job(self):
        prayer_name = "TestPrayer"
        prayer_time = datetime.now(TZ) + timedelta(minutes=5)
        
        with patch.object(self.scheduler.scheduler, 'add_job') as mock_add_job:
            self.scheduler._schedule_single_prayer_job(prayer_name, prayer_time, is_dry_run=False)
            
            self.assertEqual(mock_add_job.call_count, 2)
            
            # Check focus mode job
            focus_call = mock_add_job.call_args_list[0]
            self.assertEqual(focus_call[0][0], self.mock_action_executor.trigger_focus_mode)
            self.assertEqual(focus_call[1]['run_date'], prayer_time - timedelta(seconds=10))

            # Check adhan job
            adhan_call = mock_add_job.call_args_list[1]
            self.assertEqual(adhan_call[0][0], self.scheduler.play_adhan_and_duaa)
            self.assertEqual(adhan_call[1]['run_date'], prayer_time)

if __name__ == '__main__':
    unittest.main()
