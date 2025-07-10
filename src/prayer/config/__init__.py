# ---------------------------------------------------------------------------
# __init__.py – CLI and static constants
# ---------------------------------------------------------------------------

from __future__ import annotations
import argparse, logging, os, sys, json
import argcomplete
from datetime import timedelta
from zoneinfo import ZoneInfo
from importlib import resources

def adhan_path():
    with resources.path('prayer.assets', 'adhan.wav') as p:
        return str(p)

TZ           = ZoneInfo("Europe/Berlin")
TARGET_EMAIL = "omar.elkadi@cybus.io"
API_URL      = "https://api.aladhan.com/v1/timingsByCity"
NET_OFF_CMD, NET_ON_CMD = "nmcli networking off", "nmcli networking on"
BUSY_SLOT    = timedelta(minutes=15)
POST_DELAY   = timedelta(minutes=5)
FOCUS_DELAY  = timedelta(minutes=4)
FOCUS_LENGTH = timedelta(minutes=10)

# Determine the project root dynamically
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_DIR = os.path.join(PROJECT_ROOT, 'src', 'prayer', 'config')
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, 'config.json')

def load_config():
    if os.path.exists(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            LOG.warning(f"Could not decode JSON from {CONFIG_FILE_PATH}. Returning default config.")
            return {'city': 'Deggendorf', 'country': 'Germany', 'run_mode': 'background'}
    return {'city': 'Deggendorf', 'country': 'Germany', 'run_mode': 'background'}

def save_config(city, country, run_mode):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE_PATH, 'w') as f:
        json.dump({'city': city, 'country': country, 'run_mode': run_mode}, f, indent=4)
    LOG.info(f"Configuration saved to {CONFIG_FILE_PATH}")

# --- logging ---------------------------------------------------------------
LOG = logging.getLogger("adhan")
_log_stream = logging.StreamHandler(sys.stdout)
_log_stream.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s"))
LOG.addHandler(_log_stream)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser("Adhan scheduler daemon")
    argcomplete.autocomplete(ap)
    
    loaded_config = load_config()
    
    ap.add_argument("--city", default=loaded_config.get('city', "Deggendorf"))
    ap.add_argument("--country", default=loaded_config.get('country', "Germany"))
    ap.add_argument("--method", type=int, default=3)
    ap.add_argument("--school", type=int, default=0)
    ap.add_argument("--audio", default=adhan_path())
    ap.add_argument("--cmd", action="store_true", help="Treat --audio as shell cmd")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-net-off", action="store_true", help="Do not turn off network during focus mode in dry-run.")
    ap.add_argument("--log-level", default="INFO", choices=["DEBUG","INFO","WARNING","ERROR"])
    ap.add_argument("--focus-now", action="store_true",
                help="أطلق نافذة إعداد الخشوع فورًا ثم اخرج")
    ap.add_argument("--setup-calendar", action="store_true", help="Run the calendar setup and exit.")
    ap.add_argument("--reauthenticate-gcal", action="store_true", help="Force reauthentication for Google Calendar.")
    ns = ap.parse_args(argv)
    LOG.setLevel(ns.log_level)
    return ns