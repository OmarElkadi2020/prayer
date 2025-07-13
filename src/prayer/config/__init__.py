# ---------------------------------------------------------------------------
# __init__.py – CLI and static constants
# ---------------------------------------------------------------------------

from __future__ import annotations
import argparse, logging, os, sys, json
import argcomplete
from datetime import timedelta
from zoneinfo import ZoneInfo
from importlib import resources
from appdirs import user_config_dir

def adhan_path():
    with resources.path('prayer.assets', 'adhan.wav') as p:
        return str(p)

TZ           = ZoneInfo("Europe/Berlin")
TARGET_EMAIL = "omar.elkadi@cybus.io"
API_URL      = "https://api.aladhan.com/v1/timingsByCity"

BUSY_SLOT    = timedelta(minutes=15)
POST_DELAY   = timedelta(minutes=5)
FOCUS_DELAY  = timedelta(minutes=4)
FOCUS_LENGTH = timedelta(minutes=10)

APP_NAME = "PrayerPlayer"
APP_AUTHOR = "Omar"

CONFIG_DIR = user_config_dir(APP_NAME, APP_AUTHOR)
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, 'config.json')

def load_config():
    """Loads configuration from the JSON file, providing sensible defaults."""
    defaults = {
        'city': 'Deggendorf',
        'country': 'Germany',
        'method': 3,
        'school': 0,
        'enabled_prayers': ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"],
        'custom_audio_path': None,
        'run_mode': 'background'
    }
    if os.path.exists(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH, 'r') as f:
                config = json.load(f)
                # Merge loaded config with defaults to ensure all keys are present
                defaults.update(config)
                return defaults
        except json.JSONDecodeError:
            LOG.warning(f"Could not decode JSON from {CONFIG_FILE_PATH}. Returning default config.")
            return defaults
    return defaults

def save_config(**kwargs):
    """Saves the given configuration keys to the config file."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    
    # Load existing config to preserve any keys that aren't being updated
    current_config = load_config()
    current_config.update(kwargs)
    
    with open(CONFIG_FILE_PATH, 'w') as f:
        json.dump(current_config, f, indent=4)
    LOG.info(f"Configuration saved to {CONFIG_FILE_PATH}")

# --- logging ---------------------------------------------------------------
LOG = logging.getLogger("adhan")
# Ensure handlers are added only once to prevent duplicate log messages
if not LOG.handlers:
    _log_stream = logging.StreamHandler(sys.stdout)
    _log_stream.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s"))
    LOG.addHandler(_log_stream)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser("Adhan scheduler daemon")
    argcomplete.autocomplete(ap)
    
    loaded_config = load_config()
    
    ap.add_argument("--city", default=loaded_config.get('city', "Deggendorf"), help="City for prayer time calculations.")
    ap.add_argument("--country", default=loaded_config.get('country', "Germany"), help="Country for prayer time calculations.")
    ap.add_argument("--method", type=int, default=3, help="Calculation method for prayer times (e.g., 3 for Muslim World League).")
    ap.add_argument("--school", type=int, default=0, help="School for Asr prayer calculation (e.g., 0 for Shafii, 1 for Hanafi).")
    ap.add_argument("--audio", default=adhan_path(), help="Path to the Adhan audio file.")
    ap.add_argument("--dry-run", action="store_true", help="Run the scheduler in dry-run mode for testing.")
    ap.add_argument("--no-net-off", action="store_true", help="Do not turn off network during focus mode.")
    
    ap.add_argument("--log-level", default="INFO", choices=["DEBUG","INFO","WARNING","ERROR"], help="Set the logging level.")
    
    ap.add_argument("--setup-calendar", action="store_true", help="Runs the interactive calendar setup and then exits.")
    ap.add_argument("--install-service", action="store_true", help="Installs the application as a startup service.")
    # Add a reauthenticate flag
    ap.add_argument("--reauthenticate-gcal", action="store_true", help="Forces re-authentication for Google Calendar.")
    
    # Load from config file if it exists
    config = load_config()
    ap.add_argument("--focus-now", action="store_true", help="Run a focus session immediately.")
    ns = ap.parse_args(argv)

    if ns.reauthenticate_gcal and not ns.setup_calendar:
        ap.error("--reauthenticate-gcal can only be used in conjunction with --setup-calendar.")

    LOG.setLevel(ns.log_level)
    return ns