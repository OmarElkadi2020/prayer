import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import time

from src.scheduler import PrayerScheduler, get_scheduler_instance, run_scheduler_in_thread
from src.state import AppState
from src.config.security import TZ

class TestPrayerScheduler(unittest.TestCase):

    def setUp(self):
        self.mock_calendar_service = MagicMock()
        # When find_first_available_slot is called, return the first argument (the datetime)
        self.mock_calendar_service.find_first_available_slot.side_effect = lambda at, *args: at
        self.mock_calendar_service.add_event.return_value = True

        with patch('src.scheduler.adhan_path', return_value='fake_path.mp3'):
            from src import scheduler
            scheduler._scheduler_instance = None
            self.scheduler = get_scheduler_instance(self.mock_calendar_service)

    def tearDown(self):
        if self.scheduler.scheduler.running:
            self.scheduler.scheduler.shutdown()

    @patch('src.scheduler.today_times')
    @patch('src.scheduler.state_manager')
    def test_refresh_schedules_prayers_and_daily_job(self, mock_state_manager, mock_today_times):
        now = datetime.now(TZ)
        prayer_times = {
            'Fajr': now + timedelta(hours=1),
            'Dhuhr': now + timedelta(hours=7),
            'Asr': now + timedelta(hours=10),
        }
        mock_today_times.return_value = prayer_times

        self.scheduler.refresh(city='Test City', country='Test Country')

        self.assertEqual(mock_state_manager.state, AppState.IDLE)
        jobs = self.scheduler.scheduler.get_jobs()
        self.assertEqual(len(jobs), 4) # 3 prayers + 1 daily refresh
        daily_refresh_job = self.scheduler.scheduler.get_job('daily-refresh')
        self.assertIsNotNone(daily_refresh_job)
        
        # Find the hour and minute fields in the trigger
        hour_field = next((f for f in daily_refresh_job.trigger.fields if f.name == 'hour'), None)
        minute_field = next((f for f in daily_refresh_job.trigger.fields if f.name == 'minute'), None)

        self.assertIsNotNone(hour_field)
        self.assertEqual(str(hour_field), '0')
        self.assertIsNotNone(minute_field)
        self.assertEqual(str(minute_field), '5')

    @patch('src.scheduler.today_times')
    @patch('src.scheduler.state_manager')
    def test_refresh_handles_exception(self, mock_state_manager, mock_today_times):
        mock_today_times.side_effect = Exception("API Error")
        self.scheduler.refresh(city='Test City', country='Test Country')
        self.assertEqual(mock_state_manager.state, AppState.ERROR)
        self.assertEqual(len(self.scheduler.scheduler.get_jobs()), 0)

    @patch('src.scheduler.state_manager')
    def test_schedule_day_dry_run(self, mock_state_manager):
        now = datetime.now(TZ)
        prayer_times = {'Fajr': now + timedelta(minutes=10)}
        self.scheduler._schedule_day(prayer_times, dry_run=True)
        jobs = self.scheduler.scheduler.get_jobs()
        self.assertEqual(len(jobs), 1)
        prayer_job = jobs[0]
        self.assertTrue(prayer_job.id.startswith('prayer-dry-run-'))
        self.assertAlmostEqual(prayer_job.trigger.run_date.timestamp(), (now + timedelta(seconds=5)).timestamp(), delta=2)

    def test_update_next_prayer_info(self):
        now = datetime.now(TZ)
        
        mock_job1 = MagicMock()
        mock_job1.id = 'prayer-Asr-2024'
        mock_job1.next_run_time = now + timedelta(hours=2)

        mock_job2 = MagicMock()
        mock_job2.id = 'prayer-Dhuhr-2024'
        mock_job2.next_run_time = now + timedelta(hours=1)

        with patch.object(self.scheduler.scheduler, 'get_jobs', return_value=[mock_job1, mock_job2]):
            with patch('src.scheduler.state_manager') as mock_state_manager:
                self.scheduler._update_next_prayer_info()
                self.assertTrue(mock_state_manager.next_prayer_info.startswith('Dhuhr at'))

    def test_update_next_prayer_info_no_jobs(self):
        with patch.object(self.scheduler.scheduler, 'get_jobs', return_value=[]):
            with patch('src.scheduler.state_manager') as mock_state_manager:
                self.scheduler._update_next_prayer_info()
                self.assertEqual(mock_state_manager.next_prayer_info, "No upcoming prayers")

    

@patch('src.scheduler.load_config')
@patch('src.scheduler.get_scheduler_instance')
def test_run_scheduler_in_thread(mock_get_scheduler, mock_load_config):
    mock_load_config.return_value = {'city': 'Test', 'country': 'Test', 'method': 5, 'school': 0}
    mock_scheduler = MagicMock()
    mock_get_scheduler.return_value = mock_scheduler
    run_scheduler_in_thread(one_time_run=True, dry_run=True)
    time.sleep(0.1)
    mock_scheduler.refresh.assert_called_once_with(city='Test', country='Test', method=5, school=0, dry_run=True)
    mock_scheduler.run.assert_not_called()

@patch('src.scheduler.load_config')
@patch('src.scheduler.get_scheduler_instance')
@patch('src.scheduler.state_manager')
def test_run_scheduler_in_thread_no_config(mock_state_manager, mock_get_scheduler, mock_load_config):
    mock_load_config.return_value = {}
    run_scheduler_in_thread()
    time.sleep(0.1)
    mock_get_scheduler.assert_not_called()
    assert mock_state_manager.state == AppState.ERROR
    assert mock_state_manager.next_prayer_info == "Configure location"

if __name__ == '__main__':
    unittest.main()