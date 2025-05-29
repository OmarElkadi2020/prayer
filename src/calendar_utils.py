# ---------------------------------------------------------------------------
# calendar_utils.py – Evolution calendar access with de-duplication
# ---------------------------------------------------------------------------

from __future__ import annotations

import uuid
from datetime import datetime, date, time, timedelta, timezone
from typing import Dict

import gi
gi.require_version("EDataServer", "1.2")
gi.require_version("ECal",        "2.0")
gi.require_version("ICalGLib",    "3.0")
from gi.repository import EDataServer, ECal, ICalGLib, Gio, GLib

from intervaltree import Interval, IntervalTree

from config import TZ, TARGET_EMAIL, BUSY_SLOT, LOG

# ---------------------------------------------------------------------------
# globals & caches
# ---------------------------------------------------------------------------

CANCELLABLE = Gio.Cancellable.new()

_SENTINEL = object()
_CAL_CLIENT: ECal.Client | None | object = _SENTINEL
_CAL_TREE: Dict[date, IntervalTree] = {}

# ---------------------------------------------------------------------------
# internal helpers
# ---------------------------------------------------------------------------

# NEW ────────────────────────────────────────────────────────────────────────
def _norm(summary: str) -> str:
    """Canonical form for duplicate checks (lower-case, trimmed)."""
    return summary.strip().casefold() if isinstance(summary, str) else summary.get_value().strip().casefold()


# ---------------------------------------------------------------------------
# public helpers
# ---------------------------------------------------------------------------

def calendar_client() -> ECal.Client | None:
    """Return (and cache) the ECal client that belongs to TARGET_EMAIL."""
    global _CAL_CLIENT
    if _CAL_CLIENT is not _SENTINEL:          # already initialised
        return _CAL_CLIENT                    # may be None

    reg = EDataServer.SourceRegistry.new_sync(CANCELLABLE)
    for src in EDataServer.SourceRegistry.list_enabled(
        reg, EDataServer.SOURCE_EXTENSION_CALENDAR
    ):
        if TARGET_EMAIL.lower() in src.get_display_name().lower():
            _CAL_CLIENT = ECal.Client.connect_sync(
                src, ECal.ClientSourceType.EVENTS, 2, CANCELLABLE
            )
            break
    else:
        LOG.warning(
            "Calendar %s not found – busy-event support disabled", TARGET_EMAIL
        )
        _CAL_CLIENT = None
    return _CAL_CLIENT


def ical_to_dt(t: ICalGLib.Time) -> datetime:
    """Convert an ICalGLib.Time to TZ-aware datetime."""
    return datetime(
        t.get_year(), t.get_month(), t.get_day(),
        t.get_hour(), t.get_minute(), t.get_second(),
        tzinfo=TZ,
    )


# ---------------------------------------------------------------------------
# cache-aware calendar queries
# ---------------------------------------------------------------------------

def load_tree(day: date) -> IntervalTree:
    """
    Return *and cache* the IntervalTree for *day*.
    Each interval’s .data keeps the **raw** SUMMARY string.
    """
    if day in _CAL_TREE:
        return _CAL_TREE[day]

    tree = IntervalTree()
    client = calendar_client()
    if client:
        utc0  = datetime.combine(day, time.min, tzinfo=timezone.utc)
        utc24 = utc0 + timedelta(days=1)
        sexp  = (
            f'(occur-in-time-range? (make-time "{utc0:%Y%m%dT%H%M%SZ}") '
            f'(make-time "{utc24:%Y%m%dT%H%M%SZ}"))'
        )
        ok, comps = client.get_object_list_as_comps_sync(sexp, CANCELLABLE)
        if ok:
            for comp in comps:
                start  = ical_to_dt(comp.get_dtstart().get_value())
                end    = ical_to_dt(comp.get_dtend  ().get_value())
                summery = comp.get_summary()
                if not summery.get_value().lower().strip() in ["abwesend", "ausfall", "mittag", "absent"]:
                    tree.add(Interval(start, end, summery))
    tree.merge_overlaps(data_reducer=lambda a, b: next(iter({a, b})))
    _CAL_TREE[day] = tree
    LOG.debug("Loaded %d busy ranges for %s", len(tree), day.isoformat())
    return tree


# ---------------------------------------------------------------------------
# high-level API
# ---------------------------------------------------------------------------

def first_free_gap(start: datetime) -> datetime | None:
    """Earliest ≥start with a BUSY_SLOT-long free gap on the same day."""
    cand    = start
    day_end = datetime.combine(start.date(), time.max, tzinfo=TZ)
    tree    = load_tree(start.date())

    while cand + BUSY_SLOT <= day_end:
        if not tree.overlaps(cand, cand + BUSY_SLOT):
            return start
        cand = max(iv.end for iv in tree[cand]) + timedelta(minutes=1)
    return None


def add_busy_block(slot_start: datetime, summary: str) -> bool:
    """
    Create a BUSY calendar entry **iff** another event with the *same title*
    already **does not** exist on that date.  Returns True when created.
    """
    tree = load_tree(slot_start.date())
    key  = _norm(summary)            # NEW normalised form

    # NEW: refuse any event that already has the same title today,
    # regardless of its time range
    if any(_norm(iv.data) == key for iv in tree):
        LOG.debug("Skip duplicate %s on %s (already present)",
                  summary, slot_start.date())
        return False

    # Respect unrelated BUSY blocks
    if tree.overlaps(slot_start, slot_start + BUSY_SLOT):
        return False

    client = calendar_client()
    if not client:
        return False

    end = slot_start + BUSY_SLOT
    ics = (
        "BEGIN:VEVENT\r\n"
        f"UID:{uuid.uuid4()}\r\n"
        f"DTSTAMP:{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}\r\n"
        f"DTSTART;TZID={TZ.key}:{slot_start:%Y%m%dT%H%M%S}\r\n"
        f"DTEND;TZID={TZ.key}:{end:%Y%m%dT%H%M%S}\r\n"
        f"SUMMARY:{summary}\r\n"
        "TRANSP:OPAQUE\r\n"
        "CLASS:PRIVATE\r\n"
        "END:VEVENT\r\n"
    )

    try:
        comp = ICalGLib.Component.new_from_string(ics)
        client.create_objects_sync(
            [comp], ECal.OperationFlags.NONE, CANCELLABLE
        )
        tree.add(Interval(slot_start, end, summary))
        LOG.info(
            "📅 Added busy block: %-8s %s-%s",
            summary,
            slot_start.strftime("%H:%M"),
            end.strftime("%H:%M"),
        )
        return True
    except GLib.Error as err:
        if err.code == 8:            # read-only calendar
            LOG.warning("Calendar is read-only – skipping busy block")
            return False
        raise
