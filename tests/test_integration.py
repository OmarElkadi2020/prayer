from __future__ import annotations

import pytest
from prayer.__main__ import main
from prayer.config import TZ
from datetime import datetime

@pytest.fixture
def mock_prayer_times(mocker):
    """Fixture to mock the prayer_times module."""
    prayer_times = mocker.patch("prayer.scheduler.today_times")
    prayer_times.return_value = {
        "Fajr": datetime(2025, 7, 10, 3, 30, tzinfo=TZ),
        "Dhuhr": datetime(2025, 7, 10, 13, 0, tzinfo=TZ),
        "Asr": datetime(2025, 7, 10, 17, 0, tzinfo=TZ),
        "Maghrib": datetime(2025, 7, 10, 20, 30, tzinfo=TZ),
        "Isha": datetime(2025, 7, 10, 22, 0, tzinfo=TZ),
    }
    return prayer_times

@pytest.fixture
def mock_calendar_utils(mocker):
    """Fixture to mock the calendar_utils module."""
    mocker.patch("prayer.scheduler.first_free_gap", side_effect=lambda dt, duration: dt)
    mocker.patch("prayer.scheduler.add_busy_block", return_value=True)

def test_dry_run_integration(mock_prayer_times, mock_calendar_utils, mocker):
    """Test the main application in --dry-run mode."""
    # Mock focus_mode to prevent it from starting its internal scheduler
    mock_focus_mode = mocker.patch("prayer.__main__.focus_mode")
    
    # Mock the main scheduler's run method to prevent it from blocking
    mock_main_scheduler_run = mocker.patch("prayer.scheduler.PrayerScheduler.run")
    
    main(["--dry-run"])

    # The main scheduler should be started in dry-run mode
    mock_main_scheduler_run.assert_called_once()
