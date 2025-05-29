from __future__ import annotations
import functools
import json
from datetime import datetime, date
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import TZ, API_URL, LOG

# ---- Persistent cache setup ----
CACHE_DIR = Path.home() / ".cache" / "prayer_times"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE = CACHE_DIR / "cache.json"
LATEST_FILE = CACHE_DIR / "latest_times.json"


def _load_json(path: Path) -> dict:
    try:
        with path.open("r") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_json(path: Path, data: dict) -> None:
    try:
        with path.open("w") as f:
            json.dump(data, f)
    except Exception as e:
        LOG.warning("Failed to save JSON to %s: %s", path, e)

# Initialize disk cache
_disk_cache: dict = _load_json(CACHE_FILE)

# ---- HTTP session with retry ----
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

@functools.lru_cache(maxsize=32)
def _fetch_raw(today: date, city: str, country: str, method: int, school: int) -> dict[str, str]:
    """
    Fetch prayer times from API with in-memory cache and persistent disk fallback.
    """
    cache_key = f"{today.isoformat()}_{city}_{country}_{method}_{school}"

    try:
        resp = session.get(
            API_URL,
            params={
                "city": city,
                "country": country,
                "method": method,
                "school": school,
                "date": today.strftime("%d-%m-%Y"),
            },
            timeout=10,
        )
        resp.raise_for_status()
        timings = resp.json()["data"]["timings"]

        # Update disk cache
        _disk_cache[cache_key] = timings
        _save_json(CACHE_FILE, _disk_cache)
        return timings

    except requests.RequestException as e:
        LOG.warning("API request failed, loading from cache: %s", e)
        if cache_key in _disk_cache:
            LOG.info("Loaded prayer times from cache for %s", cache_key)
            return _disk_cache[cache_key]
        LOG.error("No cached data for %s", cache_key)
        raise


def today_times(city: str, country: str, method: int, school: int) -> dict[str, datetime]:
    """
    Return today's prayer times as datetimes, caching and retrying as needed, and persist latest times.
    """
    today = datetime.now(TZ).date()
    raw = _fetch_raw(today, city, country, method, school)

    out: dict[str, datetime] = {}
    latest: dict[str, str] = _load_json(LATEST_FILE)

    for name, timestr in raw.items():
        key = name.lower()
        if key in {"imsak", "sunset", "midnight"}:
            continue
        hour, minute = map(int, timestr.split(':'))
        dt = datetime(
            year=today.year,
            month=today.month,
            day=today.day,
            hour=hour,
            minute=minute,
            tzinfo=TZ,
        )
        out[name] = dt
        # Update latest on disk
        latest[name] = dt.isoformat()

    # Persist latest prayer times
    _save_json(LATEST_FILE, latest)

    LOG.info(
        "Prayer times for %s on %s: %s",
        city,
        today,
        ", ".join(f"{k}:{v:%H:%M}" for k, v in out.items()),
    )
    return out
