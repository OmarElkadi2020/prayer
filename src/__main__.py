#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# __main__.py – wire everything together
# ---------------------------------------------------------------------------

from __future__ import annotations
import sys
from src.config.security import get_asset_path, load_config, LOG, parse_args
from src.scheduler import PrayerScheduler
from src.prayer_times import today_times
from src.auth.google_auth import get_google_credentials
from src.calendar_api.google_calendar import GoogleCalendarService
from src.shared.event_bus import EventBus
from src.services.config_service import ConfigService

from src.domain.config_messages import SaveConfigurationCommand

def duaa_path():
    return str(get_asset_path('duaa_after_adhan.wav'))

def main(argv: list[str] | None = None) -> int:
    """Main entry point for the application."""
    
    # --- Global Exception Handler ---
    def global_exception_handler(exc_type, exc_value, exc_traceback):
        """Catches and logs uncaught exceptions."""
        LOG.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        # Optionally, show a message to the user
        from PySide6.QtWidgets import QMessageBox
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setText("An unexpected error occurred. Please check the logs for details.")
        msg_box.setWindowTitle("Application Error")
        msg_box.exec()

    sys.excepthook = global_exception_handler
    
    # The main function now only decides which entry point to use based on
    # a simple check for --install-service, which doesn't require Qt.
    # All other logic, including arg parsing, is moved to the tray_icon
    # to ensure it runs after QApplication is initialized.

    raw_argv = sys.argv[1:] if argv is None else argv

    # Early exit for service installation, which should not launch a GUI.
    if '--install-service' in raw_argv:
        from src.platform.service import ServiceManager
        # LOG is already imported at the top level
        
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

    # Parse arguments here for dry-run check
    args = parse_args(raw_argv)

    # --- Event Bus Setup ---
    event_bus = EventBus()

    # --- Service Initialization ---
    config_service = ConfigService(event_bus)
    from src.gui.notification_service import NotificationService
    notification_service = NotificationService(event_bus)
    
    # --- Register Handlers ---
    event_bus.register(SaveConfigurationCommand, config_service.handle_save_command)

    # --- Composition Root ---
    config = load_config()

    # Override config with CLI arguments if provided
    if args.city: 
        config.city = args.city
    if args.country:
        config.country = args.country
    
    # Initialize services
    calendar_service = None
    if config.google_calendar_id:
        creds = get_google_credentials()
        if creds:
            calendar_service = GoogleCalendarService(creds)

    # Determine action executor
    from src.actions_executor import DefaultActionExecutor, DryRunActionExecutor
    action_executor = DryRunActionExecutor() if args.dry_run else DefaultActionExecutor(event_bus)

    # Initialize scheduler
    scheduler = PrayerScheduler(
        audio_path=duaa_path(),
        calendar_service=calendar_service,
        prayer_times_func=today_times,
        action_executor=action_executor,
        event_bus=event_bus
    )

    # Handle --dry-run directly
    if args.dry_run:
        LOG.info("Dry run mode activated from CLI execution.")
        if not config.city or not config.country:
            LOG.error("Dry run cannot proceed without city/country configuration.")
            return 1
        
        scheduler.run_dry_run_simulation(
            city=config.city,
            country=config.country,
            method=config.method,
            school=config.school
        )
        return 0

    # For all other cases, we launch the tray icon setup.
    from src import tray_icon
    
    # Initial refresh
    if config.city and config.country:
        scheduler.refresh(
            city=config.city,
            country=config.country,
            method=config.method,
            school=config.school
        )
        scheduler.run()
    else:
        LOG.warning("No city/country configured. Scheduler will not run.")

    return tray_icon.setup_tray_icon(raw_argv, scheduler, event_bus, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
