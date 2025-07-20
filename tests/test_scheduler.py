import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import threading

from src.scheduler import PrayerScheduler
from src.actions_executor import ActionExecutor
from src.state import AppState
from src.config.security import TZ

class TestPrayerScheduler(unittest.TestCase):

    def setUp(self):
        self.audio_path = "/fake/path/to/audio.wav"
        self.calendar_service = Mock()
        self.state_manager = Mock()
        self.prayer_times_func = Mock()
        self.action_executor = Mock(spec=ActionExecutor)

        self.scheduler = PrayerScheduler(
            audio_path=self.audio_path,
            calendar_service=self.calendar_service,
            state_manager=self.state_manager,
            prayer_times_func=self.prayer_times_func,
            action_executor=self.action_executor
        )

    def tearDown(self):
        try:
            self.scheduler.scheduler.shutdown(wait=False)
        except Exception:
            pass

    def test_initialization(self):
        self.assertIsNotNone(self.scheduler.scheduler)
        self.assertEqual(self.scheduler.audio_path, self.audio_path)
        self.assertEqual(self.scheduler.action_executor, self.action_executor)

    def test_refresh_schedules_prayers(self):
        city = "Test City"
        country = "Test Country"
        now = datetime.now(TZ)
        prayer_times = {
            "Fajr": now + timedelta(minutes=10),
            "Dhuhr": now + timedelta(hours=4),
        }
        self.prayer_times_func.return_value = prayer_times

        self.scheduler.refresh(city=city, country=country)

        self.prayer_times_func.assert_called_once_with(city, country, None, None)
        self.assertEqual(self.state_manager.state, AppState.IDLE)
        
        # 2 prayers * 2 jobs (focus + adhan) + 1 daily refresh job = 5
        self.assertEqual(len(self.scheduler.scheduler.get_jobs()), 5)

    def test_refresh_dry_run(self):
        city = "Test City"
        country = "Test Country"
        dry_run_event = threading.Event()

        self.scheduler.refresh(city=city, country=country, dry_run=True, dry_run_event=dry_run_event)

        self.action_executor.set_dry_run_event.assert_called_once_with(dry_run_event)
        # 1 dry run job * 2 (focus + adhan) + 1 daily refresh job = 3
        self.assertEqual(len(self.scheduler.scheduler.get_jobs()), 3)

    def test_play_adhan_and_duaa(self):
        self.scheduler.play_adhan_and_duaa()
        self.action_executor.play_audio.assert_called_once_with(self.audio_path)
        self.assertEqual(self.state_manager.state, AppState.IDLE)

    def test_schedule_single_prayer_job(self):
        prayer_name = "TestPrayer"
        prayer_time = datetime.now(TZ) + timedelta(minutes=5)
        
        with patch.object(self.scheduler.scheduler, 'add_job') as mock_add_job:
            self.scheduler._schedule_single_prayer_job(prayer_name, prayer_time, is_dry_run=False)
            
            self.assertEqual(mock_add_job.call_count, 2)
            
            # Check focus mode job
            focus_call = mock_add_job.call_args_list[0]
            self.assertEqual(focus_call[0][0], self.action_executor.trigger_focus_mode)
            self.assertEqual(focus_call[1]['run_date'], prayer_time - timedelta(seconds=10))

            # Check adhan job
            adhan_call = mock_add_job.call_args_list[1]
            self.assertEqual(adhan_call[0][0], self.scheduler.play_adhan_and_duaa)
            self.assertEqual(adhan_call[1]['run_date'], prayer_time)

if __name__ == '__main__':
    unittest.main()
