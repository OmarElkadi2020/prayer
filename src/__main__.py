#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# __main__.py – wire everything together
# ---------------------------------------------------------------------------

from __future__ import annotations
import sys
from importlib import resources

from src.config.security import parse_args, LOG, TZ, load_config, get_asset_path
from src.scheduler import PrayerScheduler
from src.actions import focus_mode, play
from src.calendar_api.google_calendar import GoogleCalendarService
from src.auth.google_auth import get_google_credentials

def duaa_path():
    return str(get_asset_path('duaa_after_adhan.wav'))

def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else [] # Ensure argv is always a list

    # If no command-line arguments are provided, launch the default GUI tray mode.
    # If --dry-run is present, do not launch the GUI.
    if not argv or (argv and "--dry-run" not in argv):
        from src import tray_icon
        return tray_icon.setup_tray_icon()

    # If arguments are present, proceed with CLI mode.
    args = parse_args(argv)

    # Check if config exists, if not, run setup GUI
    config = load_config()
    if not config.get('city') or not config.get('country'):
        LOG.info("Configuration not found. Starting setup GUI.")
        from src.gui import main as setup_main
        setup_main()

        # After setup, re-check config
        config = load_config()
        if not config.get('city') or not config.get('country'):
            LOG.error("Configuration is still missing after setup. Exiting.")
            return 1

    if args.install_service:
        from src.platform.service import ServiceManager
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
            return 1
        return 0
    if args.setup_calendar:
        from src.gui import main as setup_main
        setup_main()
        return 0
    
    audio_path = args.audio

    # Initialize Google Calendar Service
    creds = get_google_credentials()
    calendar_service = GoogleCalendarService(creds)
    calendar_service.setup_credentials()

    pray_sched = PrayerScheduler(audio_path, calendar_service)

    # initial schedule and daily refresh at 00:05
    pray_sched.refresh(city=args.city, country=args.country, method=args.method, school=args.school, dry_run=args.dry_run)

    if args.dry_run:
        LOG.info("Dry run completed. No GUI or audio triggered.")
        return 0
    else:
        try:
            pray_sched.run()
        except (KeyboardInterrupt, SystemExit):
            LOG.info("Exit.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))