#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# __main__.py – wire everything together
# ---------------------------------------------------------------------------

from __future__ import annotations
import sys

from config import parse_args, LOG, TZ
from scheduler import PrayerScheduler
from actions import focus_mode, play


def main(argv: list[str] | None = None):
    args = parse_args(argv)
    audio_cmd = args.audio if args.cmd else f"ffplay -nodisp -autoexit -loglevel quiet '{args.audio}'"

    pray_sched = PrayerScheduler(audio_cmd)

    # initial schedule and daily refresh at 00:05
    pray_sched.refresh(city=args.city, country=args.country, method=args.method, school=args.school)
    pray_sched.scheduler.add_job(lambda: pray_sched.refresh(city=args.city, country=args.country, method=args.method, school=args.school),
                                 "cron", hour=0, minute=5, id="daily-refresh")


    if args.dry_run:
        from datetime import datetime, timedelta, timezone as _tz
        t0 = datetime.now(tz=_tz.utc).astimezone(TZ) 

        pray_sched.scheduler.add_job(focus_mode, "date", run_date=t0, id="focus-test")
        pray_sched.scheduler.add_job(play, "date", run_date=t0, id="adhan-test", args=[audio_cmd])
        pray_sched.scheduler.add_job(play, "date", run_date=t0 + timedelta(minutes=2, seconds=53), id="duaa-adhan-test", args=[f"ffplay -nodisp -autoexit -loglevel quiet 'duaa_after_adhan.wav'"])
        LOG.info("Dry-run focus at %s\", t.strftime('%H:%M:%S')")

    if args.focus_now:        # خيار جديد
        focus_mode()
        return             # لا ندخل الجدول الزمني


    try:
        pray_sched.run()
    except (KeyboardInterrupt, SystemExit):
        LOG.info("Exit.")


if __name__ == "__main__":
    main(sys.argv[1:])