#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# __main__.py – wire everything together
# ---------------------------------------------------------------------------

from __future__ import annotations
import sys
from importlib import resources

from .config import parse_args, LOG, TZ
from .scheduler import PrayerScheduler
from .actions import focus_mode, play

def duaa_path():
    with resources.path('prayer.assets', 'duaa_after_adhan.wav') as p:
        return str(p)

def main(argv: list[str] | None = None):
    args = parse_args(argv)
    if args.setup_calendar:
        from prayer.auth.auth_manager import AuthManager
        auth_manager = AuthManager()
        auth_manager.setup_google_credentials(reauthenticate=args.reauthenticate_gcal)
        
        LOG.info("Calendar setup complete.")
        return
    
    audio_cmd = args.audio # Now audio_cmd is just the path, as play() handles playback directly

    pray_sched = PrayerScheduler(audio_cmd)

    # initial schedule and daily refresh at 00:05
    pray_sched.refresh(city=args.city, country=args.country, method=args.method, school=args.school)
    pray_sched.scheduler.add_job(lambda: pray_sched.refresh(city=args.city, country=args.country, method=args.method, school=args.school),
                                 "cron", hour=0, minute=5, id="daily-refresh")


    if args.dry_run:
        from datetime import datetime, timedelta, timezone as _tz
        t0 = datetime.now(tz=_tz.utc).astimezone(TZ) 

        LOG.info(f"Dry-run: Playing adhan at {t0.strftime('%H:%M:%S')}")
        play(audio_cmd)
        LOG.info(f"Dry-run: Playing duaa at {t0.strftime('%H:%M:%S')}")
        play(duaa_path())
        # If you want to test focus mode in dry-run, you can uncomment the line below
        # focus_mode(disable_network=not args.no_net_off)
        return # Exit after playing audio in dry-run

    if args.focus_now:        # خيار جديد
        focus_mode(disable_network=not args.no_net_off)
        return             # لا ندخل الجدول الزمني

    if not args.dry_run:
        try:
            pray_sched.run()
        except (KeyboardInterrupt, SystemExit):
            LOG.info("Exit.")


if __name__ == "__main__":
    main(sys.argv[1:])