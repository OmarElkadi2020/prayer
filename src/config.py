# ---------------------------------------------------------------------------
# config.py – CLI and static constants
# ---------------------------------------------------------------------------

from __future__ import annotations
import argparse, logging, os, sys
from datetime import timedelta
from zoneinfo import ZoneInfo

TZ           = ZoneInfo("Europe/Berlin")
TARGET_EMAIL = "omar.elkadi@cybus.io"
API_URL      = "https://api.aladhan.com/v1/timingsByCity"
NET_OFF_CMD, NET_ON_CMD = "nmcli networking off", "nmcli networking on"
BUSY_SLOT    = timedelta(minutes=15)
POST_DELAY   = timedelta(minutes=5)
FOCUS_DELAY  = timedelta(minutes=4)
FOCUS_LENGTH = timedelta(minutes=10)

# --- logging ---------------------------------------------------------------
LOG = logging.getLogger("adhan")
_log_stream = logging.StreamHandler(sys.stdout)
_log_stream.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s"))
LOG.addHandler(_log_stream)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser("Adhan scheduler daemon")
    ap.add_argument("--city", default="Deggendorf")
    ap.add_argument("--country", default="Germany")
    ap.add_argument("--method", type=int, default=3)
    ap.add_argument("--school", type=int, default=0)
    ap.add_argument("--audio", default="/home/omar/private/prayer/src/adhan.mp3")
    ap.add_argument("--cmd", action="store_true", help="Treat --audio as shell cmd")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--log-level", default="INFO", choices=["DEBUG","INFO","WARNING","ERROR"])
    ap.add_argument("--focus-now", action="store_true",
                help="أطلق نافذة إعداد الخشوع فورًا ثم اخرج")
    ns = ap.parse_args(argv)
    LOG.setLevel(ns.log_level)
    return ns
