from __future__ import annotations

import pytest
import requests.exceptions
from prayer import prayer_times
from datetime import datetime
from prayer.config import TZ

@pytest.fixture
def mock_requests_get(mocker):
    """Fixture to mock requests.get."""
    return mocker.patch("requests.Session.get")

@pytest.fixture
def sample_api_response():
    """Sample successful API response."""
    return {
        "data": {
            "timings": {
                "Fajr": "03:30",
                "Dhuhr": "13:00",
                "Asr": "17:00",
                "Maghrib": "20:30",
                "Isha": "22:00",
                "Imsak": "03:20",
                "Sunset": "20:25",
                "Midnight": "00:00"
            }
        }
    }

def test_today_times_success(mock_requests_get, sample_api_response):
    """Test today_times with a successful API response."""
    prayer_times._fetch_raw.cache_clear()
    mock_requests_get.return_value.json.return_value = sample_api_response
    mock_requests_get.return_value.raise_for_status.return_value = None

    times = prayer_times.today_times("TestCity", "TestCountry", 1, 0)

    assert "Fajr" in times
    assert "Dhuhr" in times
    assert "Asr" in times
    assert "Maghrib" in times
    assert "Isha" in times
    
    # Check that non-prayer times are filtered out
    assert "Imsak" not in times
    assert "Sunset" not in times
    assert "Midnight" not in times

    # Check that the time is a timezone-aware datetime object
    fajr_time = times["Fajr"]
    assert isinstance(fajr_time, datetime)
    assert fajr_time.hour == 3
    assert fajr_time.minute == 30
    assert fajr_time.tzinfo is not None
    assert fajr_time.tzinfo == TZ

def test_today_times_api_failure_no_cache(mock_requests_get, mocker):
    """Test API failure when no cache is available."""
    prayer_times._fetch_raw.cache_clear()
    mock_requests_get.side_effect = requests.exceptions.RequestException("API is down")
    mocker.patch("prayer.prayer_times._disk_cache", {}) # Ensure cache is empty

    with pytest.raises(requests.exceptions.RequestException, match="API is down"):
        prayer_times.today_times("TestCity", "TestCountry", 1, 0)

def test_today_times_api_failure_with_cache(mock_requests_get, mocker, sample_api_response):
    """Test API failure when a cached result is available."""
    prayer_times._fetch_raw.cache_clear()
    mock_requests_get.side_effect = requests.exceptions.RequestException("API is down")
    
    # Pre-populate the cache
    today = datetime.now(TZ).date()
    cache_key = f"{today.isoformat()}_TestCity_TestCountry_1_0"
    mocker.patch("prayer.prayer_times._disk_cache", {cache_key: sample_api_response["data"]["timings"]})

    times = prayer_times.today_times("TestCity", "TestCountry", 1, 0)
    
    # Verify that the cached data is used
    assert "Fajr" in times
    assert times["Fajr"].hour == 3
    assert times["Fajr"].minute == 30
