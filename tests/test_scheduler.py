from __future__ import annotations

import pytest
from unittest.mock import MagicMock, call
from datetime import datetime, timedelta
from prayer.scheduler import PrayerScheduler
from prayer.config import TZ

# It's better to mock the specific classes/functions used, not the entire module.
from apscheduler.schedulers.blocking import BlockingScheduler

@pytest.fixture
def mock_prayer_times() -> dict[str, datetime]:
    """Provides a consistent set of mock prayer times for tests."""
    base_time = datetime(2025, 7, 10, tzinfo=TZ)
    return {
        "Fajr": base_time.replace(hour=4, minute=0),
        "Sunrise": base_time.replace(hour=5, minute=30), # Included to test skipping
        "Dhuhr": base_time.replace(hour=13, minute=0),
        "Asr": base_time.replace(hour=17, minute=0),
        "Maghrib": base_time.replace(hour=20, minute=0),
        "Isha": base_time.replace(hour=22, minute=0),
        "Firstthird": base_time.replace(hour=1, minute=0), # Included to test skipping
        "Lastthird": base_time.replace(hour=3, minute=0),  # Included to test skipping
    }

@pytest.fixture
def mock_dependencies(mocker, mock_prayer_times):
    """
    A comprehensive fixture to mock all external dependencies for PrayerScheduler.
    This centralizes mocking logic, making tests cleaner.
    """
    # Mock the BlockingScheduler class to control its instances
    mock_scheduler_instance = MagicMock(spec=BlockingScheduler)
    mocker.patch("apscheduler.schedulers.blocking.BlockingScheduler", return_value=mock_scheduler_instance)

    # Mock the function that fetches prayer times
    mocker.patch("prayer.scheduler.today_times", return_value=mock_prayer_times)

    # Mock datetime.now() to return a fixed point in time
    # This is crucial for predictable testing of time-sensitive logic.
    mock_now = datetime(2025, 7, 10, 3, 0, tzinfo=TZ)
    mocker.patch("prayer.scheduler.datetime", MagicMock(now=MagicMock(return_value=mock_now)))

    # Mock helper functions and actions
    mocker.patch("prayer.scheduler.first_free_gap", side_effect=lambda dt, duration: dt)
    mocker.patch("prayer.scheduler.add_busy_block", return_value=True)
    mocker.patch("prayer.scheduler.play")
    mocker.patch("prayer.scheduler.focus_mode")
    mocker.patch("prayer.scheduler.duaa_path", return_value="mock/duaa/path.wav")

    # Return the mocked scheduler instance for assertions
    return mock_scheduler_instance

@pytest.fixture
def scheduler(mock_dependencies) -> PrayerScheduler:
    """
    Provides an instance of PrayerScheduler with all its dependencies mocked.
    The `mock_dependencies` fixture runs first, ensuring that when PrayerScheduler
    is initialized, it receives the mocked scheduler instance.
    """
    s = PrayerScheduler(audio_path="test_audio_path")
    s.scheduler = mock_dependencies
    return s

def test_refresh_schedules_all_jobs_correctly(scheduler: PrayerScheduler, mock_dependencies: MagicMock, mock_prayer_times: dict):
    """
    Verify that refresh() schedules all 3 jobs for each of the 5 main prayers,
    plus a single daily refresh job.
    """
    scheduler.refresh(city="TestCity", country="TestCountry", method=3, school=0)

    # 5 main prayers * 3 jobs each (adhan, duaa, focus) + 1 daily refresh job
    expected_job_count = (5 * 3) + 1
    assert mock_dependencies.add_job.call_count == expected_job_count

    # Check that the daily refresh job is scheduled correctly using kwargs
    mock_dependencies.add_job.assert_any_call(
        scheduler.refresh,
        "cron",
        hour=0,
        minute=5,
        id="daily-refresh",
        replace_existing=True,
        kwargs={"city": "TestCity", "country": "TestCountry", "method": 3, "school": 0}
    )

    # Verify that jobs are scheduled for a specific prayer (e.g., Fajr)
    fajr_time = mock_prayer_times["Fajr"]
    expected_fajr_calls = [
        call(scheduler.play_adhan, "date", run_date=fajr_time, id=f"adhan-Fajr-{fajr_time:%Y%m%d%H%M}", args=[scheduler.audio_path], misfire_grace_time=None),
        call(scheduler.play_duaa, "date", run_date=fajr_time + timedelta(minutes=2, seconds=53), id=f"duaa-Fajr-{fajr_time:%Y%m%d%H%M}"),
        call(scheduler.trigger_focus_mode, "date", run_date=fajr_time + timedelta(minutes=4), id=f"focus-Fajr-{fajr_time:%Y%m%d%H%M}"),
    ]
    mock_dependencies.add_job.assert_has_calls(expected_fajr_calls, any_order=True)

def test_refresh_skips_past_prayer_times(scheduler: PrayerScheduler, mock_dependencies: MagicMock, mocker):
    """
    Verify that if a prayer time is in the past, its jobs are not scheduled.
    The mock time is 03:00. Fajr is at 01:00 (past), Dhuhr is at 13:00 (future).
    """
    past_prayer_times = {
        "Fajr": datetime(2025, 7, 10, 1, 0, tzinfo=TZ),  # Past
        "Dhuhr": datetime(2025, 7, 10, 13, 0, tzinfo=TZ), # Future
    }
    mocker.patch("prayer.scheduler.today_times", return_value=past_prayer_times)

    scheduler.refresh(city="Any", country="Any")

    # Only Dhuhr jobs (3) and the daily refresh (1) should be scheduled.
    assert mock_dependencies.add_job.call_count == (1 * 3) + 1

    # Verify no job IDs containing "Fajr" were added
    for job_call in mock_dependencies.add_job.call_args_list:
        kwargs = job_call.kwargs
        if "id" in kwargs:
            assert "Fajr" not in kwargs["id"]

def test_refresh_is_idempotent_and_clears_old_jobs(scheduler: PrayerScheduler, mock_dependencies: MagicMock):
    """
    Verify that calling refresh multiple times first removes all existing jobs
    before scheduling new ones, preventing duplicate jobs.
    """
    # First call
    scheduler.refresh(city="Any", country="Any")
    assert mock_dependencies.remove_all_jobs.call_count == 1
    first_call_count = mock_dependencies.add_job.call_count
    assert first_call_count > 0

    # Second call
    scheduler.refresh(city="Any", country="Any")
    assert mock_dependencies.remove_all_jobs.call_count == 2
    # The number of jobs added should be double the first call
    assert mock_dependencies.add_job.call_count == first_call_count * 2


def test_schedule_day_skips_non_prayer_times(scheduler: PrayerScheduler, mock_dependencies: MagicMock, mock_prayer_times: dict):
    """
    Verify that _schedule_day correctly ignores non-essential times like
    'Sunrise', 'Firstthird', and 'Lastthird'.
    """
    # The mock_prayer_times includes 8 entries, but only 5 are main prayers.
    scheduler._schedule_day(mock_prayer_times)

    # Should only schedule jobs for the 5 main prayers (5 * 3 = 15)
    assert mock_dependencies.add_job.call_count == 15

    # Verify that no jobs for the skipped times were added
    for job_call in mock_dependencies.add_job.call_args_list:
        kwargs = job_call.kwargs
        if "id" in kwargs:
            job_id = kwargs["id"]
            assert "Sunrise" not in job_id
            assert "Firstthird" not in job_id
            assert "Lastthird" not in job_id

def test_schedule_day_handles_no_free_gap(scheduler: PrayerScheduler, mock_dependencies: MagicMock, mocker, mock_prayer_times: dict):
    """
    Verify that if a free calendar slot cannot be found, no jobs are scheduled
    for that prayer.
    """
    mocker.patch("prayer.scheduler.first_free_gap", return_value=None)

    scheduler._schedule_day(mock_prayer_times)

    # No jobs should be added at all if no free gaps can be found
    assert mock_dependencies.add_job.call_count == 0

def test_schedule_day_skips_if_already_in_calendar(scheduler: PrayerScheduler, mock_dependencies: MagicMock, mocker, mock_prayer_times: dict):
    """
    Verify that if the prayer is already marked as busy in the external
    calendar, no jobs are scheduled for it.
    """
    # Simulate that add_busy_block fails (returns False), indicating it's already there
    mocker.patch("prayer.scheduler.add_busy_block", return_value=False)

    scheduler._schedule_day(mock_prayer_times)

    # No jobs should be added if the calendar blocks can't be created
    assert mock_dependencies.add_job.call_count == 0

def test_play_duaa_is_silent_if_path_is_missing(scheduler: PrayerScheduler, mocker):
    """
    Verify that the duaa is not played if the audio file path is not found.
    """
    # Mock duaa_path to return an empty string, simulating a missing file
    mocker.patch("prayer.scheduler.duaa_path", return_value="")
    mock_play = mocker.patch("prayer.scheduler.play")

    # Re-initialize the scheduler to pick up the new mock
    s = PrayerScheduler("test_cmd")
    s.play_duaa()

    # Assert that the underlying 'play' function was not called
    mock_play.assert_not_called()
