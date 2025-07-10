from __future__ import annotations

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from prayer.scheduler import PrayerScheduler, today_times # Import today_times directly
from prayer.config import TZ
from apscheduler.schedulers.blocking import BlockingScheduler # Import BlockingScheduler

@pytest.fixture
def mock_scheduler_dependencies(mocker):
    # Mock the external functions that PrayerScheduler depends on
    mocker.patch("prayer.scheduler.today_times", return_value={
        "Fajr": datetime(2025, 7, 10, 4, 0, tzinfo=TZ),
        "Dhuhr": datetime(2025, 7, 10, 13, 0, tzinfo=TZ),
        "Asr": datetime(2025, 7, 10, 17, 0, tzinfo=TZ),
        "Maghrib": datetime(2025, 7, 10, 20, 0, tzinfo=TZ),
        "Isha": datetime(2025, 7, 10, 22, 0, tzinfo=TZ),
    })
    mocker.patch("prayer.scheduler.first_free_gap", side_effect=lambda dt, duration: dt)
    mocker.patch("prayer.scheduler.add_busy_block", return_value=True)
    mocker.patch("prayer.scheduler.play")
    mocker.patch("prayer.scheduler.focus_mode")
    mocker.patch("prayer.scheduler.duaa_path", return_value="mock/duaa/path.wav")

    # Mock the BlockingScheduler class itself
    mock_blocking_scheduler_class = mocker.patch("apscheduler.schedulers.blocking.BlockingScheduler")
    # Return the mocked BlockingScheduler class
    return mock_blocking_scheduler_class

@pytest.fixture
def scheduler(mock_scheduler_dependencies):
    # When PrayerScheduler is instantiated, it will use the mocked BlockingScheduler class
    ps = PrayerScheduler("test_audio_cmd")
    # Ensure the PrayerScheduler instance uses the mocked scheduler
    ps.scheduler = mock_scheduler_dependencies.return_value
    return ps

def test_refresh_schedules_jobs(scheduler, mock_scheduler_dependencies, mocker):
    scheduler.refresh(city="TestCity", country="TestCountry", method=3, school=0)

    # Verify that add_job was called for each prayer time (excluding Sunrise, Firstthird, Lastthird)
    # and for the daily refresh
    # Each prayer time schedules 3 jobs (adhan, duaa, focus) + 1 daily refresh job
    assert mock_scheduler_dependencies.return_value.add_job.call_count == (5 * 3) + 1 # 5 prayers * (adhan, duaa, focus) + 1 daily refresh

    # Verify specific calls for prayer times
    expected_calls = [
        mocker.call(mocker.ANY, "date", run_date=datetime(2025, 7, 10, 4, 0, tzinfo=TZ), args=["test_audio_cmd"], id="adhan-Fajr-202507100400", misfire_grace_time=None),
        mocker.call(mocker.ANY, "date", run_date=datetime(2025, 7, 10, 4, 0, tzinfo=TZ) + timedelta(minutes=4), id="focus-Fajr-202507100400"),
        mocker.call(mocker.ANY, "date", run_date=datetime(2025, 7, 10, 4, 0, tzinfo=TZ) + timedelta(minutes=2, seconds=53), id="duaa-Fajr-202507100400", args=["mock/duaa/path.wav"]),

        mocker.call(mocker.ANY, "date", run_date=datetime(2025, 7, 10, 13, 0, tzinfo=TZ), args=["test_audio_cmd"], id="adhan-Dhuhr-202507101300", misfire_grace_time=None),
        mocker.call(mocker.ANY, "date", run_date=datetime(2025, 7, 10, 13, 0, tzinfo=TZ) + timedelta(minutes=4), id="focus-Dhuhr-202507101300"),
        mocker.call(mocker.ANY, "date", run_date=datetime(2025, 7, 10, 13, 0, tzinfo=TZ) + timedelta(minutes=2, seconds=53), id="duaa-Dhuhr-202507101300", args=["mock/duaa/path.wav"]),

        mocker.call(mocker.ANY, "date", run_date=datetime(2025, 7, 10, 17, 0, tzinfo=TZ), args=["test_audio_cmd"], id="adhan-Asr-202507101700", misfire_grace_time=None),
        mocker.call(mocker.ANY, "date", run_date=datetime(2025, 7, 10, 17, 0, tzinfo=TZ) + timedelta(minutes=4), id="focus-Asr-202507101700"),
        mocker.call(mocker.ANY, "date", run_date=datetime(2025, 7, 10, 17, 0, tzinfo=TZ) + timedelta(minutes=2, seconds=53), id="duaa-Asr-202507101700", args=["mock/duaa/path.wav"]),

        mocker.call(mocker.ANY, "date", run_date=datetime(2025, 7, 10, 20, 0, tzinfo=TZ), args=["test_audio_cmd"], id="adhan-Maghrib-202507102000", misfire_grace_time=None),
        mocker.call(mocker.ANY, "date", run_date=datetime(2025, 7, 10, 20, 0, tzinfo=TZ) + timedelta(minutes=4), id="focus-Maghrib-202507102000"),
        mocker.call(mocker.ANY, "date", run_date=datetime(2025, 7, 10, 20, 0, tzinfo=TZ) + timedelta(minutes=2, seconds=53), id="duaa-Maghrib-202507102000", args=["mock/duaa/path.wav"]),

        mocker.call(mocker.ANY, "date", run_date=datetime(2025, 7, 10, 22, 0, tzinfo=TZ), args=["test_audio_cmd"], id="adhan-Isha-202507102200", misfire_grace_time=None),
        mocker.call(mocker.ANY, "date", run_date=datetime(2025, 7, 10, 22, 0, tzinfo=TZ) + timedelta(minutes=4), id="focus-Isha-202507102200"),
        mocker.call(mocker.ANY, "date", run_date=datetime(2025, 7, 10, 22, 0, tzinfo=TZ) + timedelta(minutes=2, seconds=53), id="duaa-Isha-202507102200", args=["mock/duaa/path.wav"]),

        # Daily refresh job
        mocker.call(mocker.ANY, "cron", hour=0, minute=5, id="daily-refresh")
    ]
    mock_scheduler_dependencies.return_value.add_job.assert_has_calls(expected_calls, any_order=True)

def test_refresh_skips_past_times(scheduler, mock_scheduler_dependencies, mocker):
    mocker.patch("prayer.scheduler.today_times", return_value={
        "Fajr": datetime(2025, 7, 10, 1, 0, tzinfo=TZ), # Past time
        "Dhuhr": datetime(2025, 7, 10, 13, 0, tzinfo=TZ),
    })
    mocker.patch("prayer.scheduler.datetime")
    mocker.patch("prayer.scheduler.datetime.now", return_value=datetime(2025, 7, 10, 2, 0, tzinfo=TZ))
    mocker.patch("prayer.scheduler.datetime.now().astimezone", return_value=datetime(2025, 7, 10, 2, 0, tzinfo=TZ))

    scheduler.refresh(city="TestCity", country="TestCountry", method=3, school=0)

    # Only Dhuhr should be scheduled, plus the daily refresh
    assert mock_scheduler_dependencies.return_value.add_job.call_count == (1 * 3) + 1 # 1 prayer * (adhan, duaa, focus) + 1 daily refresh

    # Verify Fajr was not scheduled
    for call_args in mock_scheduler_dependencies.return_value.add_job.call_args_list:
        assert "Fajr" not in str(call_args)

def test_refresh_handles_duplicate_scheduling(scheduler, mock_scheduler_dependencies, mocker):
    # Schedule once
    scheduler.refresh(city="TestCity", country="TestCountry", method=3, school=0)
    initial_call_count = mock_scheduler_dependencies.return_value.add_job.call_count

    # Schedule again with the same parameters
    scheduler.refresh(city="TestCity", country="TestCountry", method=3, school=0)

    # The call count should be the same as initial + 1 for the new daily refresh job
    # because the prayer times are marked as duplicates by scheduler memory
    assert mock_scheduler_dependencies.return_value.add_job.call_count == initial_call_count + 1

def test_schedule_day_skips_sunrise_and_thirds(scheduler, mock_scheduler_dependencies, mocker):
    # Mock today_times to return specific prayer times including those to be skipped
    mocker.patch("prayer.scheduler.today_times", return_value={
        "Fajr": datetime(2025, 7, 10, 4, 0, tzinfo=TZ),
        "Sunrise": datetime(2025, 7, 10, 5, 0, tzinfo=TZ),
        "Firstthird": datetime(2025, 7, 10, 1, 0, tzinfo=TZ),
        "Lastthird": datetime(2025, 7, 10, 3, 0, tzinfo=TZ),
        "Dhuhr": datetime(2025, 7, 10, 13, 0, tzinfo=TZ),
    })
    # Mock datetime.now to control the current time for filtering past events
    mocker.patch("prayer.scheduler.datetime")
    mocker.patch("prayer.scheduler.datetime.now", return_value=datetime(2025, 7, 10, 2, 0, tzinfo=TZ))
    mocker.patch("prayer.scheduler.datetime.now().astimezone", return_value=datetime(2025, 7, 10, 2, 0, tzinfo=TZ))

    # Call _schedule_day directly, passing the mocked today_times result
    scheduler._schedule_day(mock_today_times_func.return_value) # Use the return value of the mocked function

    # Only Fajr and Dhuhr should be scheduled (2 prayers * 3 jobs each)
    assert mock_scheduler_dependencies.return_value.add_job.call_count == 2 * 3 # 2 prayers * (adhan, duaa, focus)

    # Verify Sunrise, Firstthird, Lastthird were not scheduled
    for call_args in mock_scheduler_dependencies.return_value.add_job.call_args_list:
        assert "Sunrise" not in str(call_args)
        assert "Firstthird" not in str(call_args)
        assert "Lastthird" not in str(call_args)

def test_schedule_day_handles_no_free_gap(scheduler, mock_scheduler_dependencies, mocker):
    mocker.patch("prayer.scheduler.first_free_gap", return_value=None)
    mock_today_times_func = mocker.patch("prayer.scheduler.today_times", return_value={
        "Fajr": datetime(2025, 7, 10, 4, 0, tzinfo=TZ),
    })

    scheduler._schedule_day(mock_today_times_func.return_value)

    # No jobs should be added if no free gap
    assert mock_scheduler_dependencies.return_value.add_job.call_count == 0

def test_schedule_day_skips_if_already_in_calendar(scheduler, mock_scheduler_dependencies, mocker):
    mocker.patch("prayer.scheduler.add_busy_block", return_value=False) # Simulate already in calendar
    mock_today_times_func = mocker.patch("prayer.scheduler.today_times", return_value={
        "Fajr": datetime(2025, 7, 10, 4, 0, tzinfo=TZ),
    })

    scheduler._schedule_day(mock_today_times_func.return_value)

    # No jobs should be added if already in calendar
    assert mock_scheduler_dependencies.return_value.add_job.call_count == 0
