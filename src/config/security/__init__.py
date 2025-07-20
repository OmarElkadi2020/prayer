# ---------------------------------------------------------------------------
# __init__.py – CLI and static constants
# ---------------------------------------------------------------------------

from __future__ import annotations
import argparse
import logging
import os
import sys
import json
import argcomplete
from datetime import timedelta
from zoneinfo import ZoneInfo
from importlib import resources
from appdirs import user_config_dir
from src.config.schema import Config

def get_asset_path(filename):
    """
    Returns a path-like object for an asset in the 'prayer.assets' package.
    This works for both development and PyInstaller-packaged modes.
    """
    return resources.files('assets').joinpath(filename)

# --- Default Paths ---
DEFAULT_ADHAN_PATH = get_asset_path('adhan.wav')

def adhan_path():
    with resources.path('assets', 'adhan.wav') as p:
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
print(f"CONFIG_DIR: {CONFIG_DIR}")
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, 'config.json')

def load_config() -> Config:
    """
    Loads configuration from a JSON file, validates it with Pydantic,
    and returns a Config object.
    """
    if not os.path.exists(CONFIG_FILE_PATH):
        return Config()
    
    try:
        with open(CONFIG_FILE_PATH, 'r') as f:
            config_data = json.load(f)
        return Config(**config_data)
    except (json.JSONDecodeError, TypeError) as e:
        LOG.warning(f"Could not load or validate config from {CONFIG_FILE_PATH}: {e}. Using default config.")
        return Config()


def save_config(config: Config):
    """Saves the given Config object to the config file."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE_PATH, 'w') as f:
        json.dump(config.dict(), f, indent=4)
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
    
    ap.add_argument("--city", help="City for prayer time calculations.")
    ap.add_argument("--country", help="Country for prayer time calculations.")
    ap.add_argument("--method", type=int, default=loaded_config.method, help="Calculation method for prayer times (e.g., 3 for Muslim World League).")
    ap.add_argument("--school", type=int, default=loaded_config.school, help="School for Asr prayer calculation (e.g., 0 for Shafii, 1 for Hanafi).")
    ap.add_argument("--audio", default=str(DEFAULT_ADHAN_PATH), help="Path to the Adhan audio file.")
    ap.add_argument("--dry-run", action="store_true", help="Run the scheduler in dry-run mode for testing.")
    ap.add_argument("--no-net-off", action="store_true", help="Do not turn off network during focus mode.")
    ap.add_argument("--custom-audio-path", default=loaded_config.custom_audio_path, help="Path to a custom Adhan audio file.")
    ap.add_argument("--google-calendar-id", default=loaded_config.google_calendar_id, help="Google Calendar ID to use for events.")
    ap.add_argument("--run-mode", default=loaded_config.run_mode, choices=["background", "foreground"], help="Run mode of the application (background or foreground).")
    
    ap.add_argument("--log-level", default=loaded_config.log_level, choices=["DEBUG","INFO","WARNING","ERROR"], help="Set the logging level.")
    
    ap.add_argument("--setup-calendar", action="store_true", help="Runs the interactive calendar setup and then exits.")
    ap.add_argument("--install-service", action="store_true", help="Installs the application as a startup service.")
    # Add a reauthenticate flag
    ap.add_argument("--reauthenticate-gcal", action="store_true", help="Forces re-authentication for Google Calendar.")
    
    ap.add_argument("--focus-now", action="store_true", help="Run a focus session immediately.")
    ns = ap.parse_args(argv)

    if ns.reauthenticate_gcal and not ns.setup_calendar:
        ap.error("--reauthenticate-gcal can only be used in conjunction with --setup-calendar.")

    LOG.setLevel(ns.log_level)
    return ns

# --- constants -------------------------------------------------------------
CREDENTIALS_PATH = os.path.join(CONFIG_DIR, 'google_client_config.json')
TOKEN_PATH = os.path.join(CONFIG_DIR, 'token.json')