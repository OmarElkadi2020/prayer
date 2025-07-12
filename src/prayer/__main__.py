#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# __main__.py – wire everything together
# ---------------------------------------------------------------------------

from __future__ import annotations
import sys
from importlib import resources

from .config import parse_args, LOG, TZ, load_config
from .scheduler import PrayerScheduler
from .actions import focus_mode, play

def duaa_path():
    with resources.path('prayer.assets', 'duaa_after_adhan.wav') as p:
        return str(p)

def main(argv: list[str] | None = None):
    # Check if config exists, if not, run setup GUI
    config = load_config()
    if not config.get('city') or not config.get('country'):
        LOG.info("Configuration not found. Starting setup GUI.")
        # We need to find the setup_gui script.
        # When running from a PyInstaller bundle, the script will be in the same directory.
        # When running from source, it's in the root of the project.
        # This is tricky. A better approach would be to include the GUI code in the `prayer` package.
        # For now, let's assume the user runs `__main__.py` from the project root.
        try:
            from setup_gui import main as setup_main
            setup_main()
        except ImportError:
            LOG.error("Could not import setup_gui. Please run this script from the project root.")
            return

        # After setup, re-check config
        config = load_config()
        if not config.get('city') or not config.get('country'):
            LOG.error("Configuration is still missing after setup. Exiting.")
            return

    args = parse_args(argv)
    if args.install_service:
        from prayer.platform.service import ServiceManager
        service_manager = ServiceManager(
            service_name="prayer-player",
            service_display_name="Prayer Player",
            service_description="A service to play prayer times."
        )
        try:
            service_manager.install()
            service_manager.enable()
            LOG.info("Service installed and enabled successfully.")
        except Exception as e:
            LOG.error(f"Failed to install or enable service: {e}")
        return
    if args.setup_calendar:
        try:
            from setup_gui import main as setup_main
            setup_main()
        except ImportError:
            LOG.error("Could not import setup_gui. Please run this script from the project root.")
        return
    
    audio_path = args.audio

    pray_sched = PrayerScheduler(audio_path)

    # initial schedule and daily refresh at 00:05
    pray_sched.refresh(city=args.city, country=args.country, method=args.method, school=args.school)


    if args.dry_run:
        from datetime import datetime, timedelta

        # Clear the regular schedule to only run the dry-run jobs
        pray_sched.scheduler.remove_all_jobs()
        
        LOG.info("Starting dry run with scheduler...")
        now = datetime.now(TZ)
        start_time = now + timedelta(seconds=4)
        
        # Adhan duration is approximated from original scheduler logic
        adhan_duration = timedelta(minutes=2, seconds=53)
        duaa_time = start_time + adhan_duration

        LOG.info(f"Scheduling Adhan and Focus Mode at: {start_time.strftime('%H:%M:%S')}")
        LOG.info(f"Scheduling Duaa at: {duaa_time.strftime('%H:%M:%S')}")

        # 1. Schedule Adhan
        pray_sched.scheduler.add_job(
            pray_sched.play_adhan, "date", run_date=start_time,
            id="dry-run-adhan", args=[pray_sched.audio_path]
        )

        # 2. Schedule Focus Mode
        pray_sched.scheduler.add_job(
            pray_sched.trigger_focus_mode, "date", run_date=start_time,
            id="dry-run-focus"
        )

        # 3. Schedule Duaa
        pray_sched.scheduler.add_job(
            pray_sched.play_duaa, "date", run_date=duaa_time,
            id="dry-run-duaa"
        )
        
        # Run the scheduler for the dry run
        LOG.info("Dry run setup complete. Scheduler would have started here.")
        try:
            pray_sched.run()
        except (KeyboardInterrupt, SystemExit):
            LOG.info("Dry run exit.")
        
        return # Exit after the dry run

    

    if not args.dry_run:
        try:
            pray_sched.run()
        except (KeyboardInterrupt, SystemExit):
            LOG.info("Exit.")


if __name__ == "__main__":
    main(sys.argv[1:])