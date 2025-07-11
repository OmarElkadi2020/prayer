# ------------------------------------------------------------------------
# prayer_times.py – Fetches prayer times from an API
# ------------------------------------------------------------------------
from __future__ import annotations
import functools
import requests
from datetime import datetime
from typing import Dict

from .config import TZ, LOG, API_URL

# A simple in-memory cache for API responses to avoid hitting the API on every call
_disk_cache: Dict[str, Dict[str, str]] = {}

@functools.lru_cache(maxsize=None)
def _fetch_raw(city: str, country: str, method: int | None, school: int | None) -> Dict[str, str]:
    """
    Fetches raw prayer time data from the Aladhan API.
    This function is cached to prevent repeated API calls with the same parameters.
    """
    today = datetime.now(TZ).date()
    cache_key = f"{today.isoformat()}_{city}_{country}_{method}_{school}"

    if cache_key in _disk_cache:
        LOG.info("Returning prayer times from disk cache.")
        return _disk_cache[cache_key]

    params = {
        "city": city,
        "country": country,
        "school": school if school is not None else 1, # Default to Shafi
        "method": method if method is not None else 3, # Default to Muslim World League
    }
    
    LOG.info(f"Fetching prayer times for {city}, {country} from API...")
    try:
        session = requests.Session()
        response = session.get(API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        timings = data["data"]["timings"]
        _disk_cache[cache_key] = timings
        LOG.info("Successfully fetched and cached prayer times.")
        return timings
    except requests.exceptions.RequestException as e:
        LOG.error(f"API request failed: {e}")
        if cache_key in _disk_cache:
            LOG.warning("Returning stale data from disk cache due to API failure.")
            return _disk_cache[cache_key]
        raise

def today_times(city: str, country: str, method: int | None = None, school: int | None = None) -> Dict[str, datetime]:
    """
    Provides a dictionary of today's prayer times.
    
    Fetches data from the Aladhan API, with caching to prevent excessive calls.
    Filters out non-prayer events and returns timezone-aware datetime objects.
    """
    timings_raw = _fetch_raw(city, country, method, school)
    
    prayer_times = {}
    today = datetime.now(TZ).date()
    
    for name, time_str in timings_raw.items():
        if name in {"Imsak", "Sunset", "Midnight", "Firstthird", "Lastthird", "Sunrise"}:
            continue
        
        hour, minute = map(int, time_str.split(":"))
        dt = datetime(today.year, today.month, today.day, hour, minute, tzinfo=TZ)
        prayer_times[name] = dt
        
    return prayer_times