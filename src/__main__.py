#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# __main__.py – wire everything together
# ---------------------------------------------------------------------------

from __future__ import annotations
import sys
import threading
from src.config.security import get_asset_path, load_config, LOG, parse_args
from src.scheduler import get_scheduler_instance

def duaa_path():
    return str(get_asset_path('duaa_after_adhan.wav'))

def execute_cli_dry_run(args) -> int:
    """
    Executes the dry run simulation when triggered from the command line.
    This function is designed to be called directly from __main__.py
    when the --dry-run argument is present.
    """
    LOG.info("Dry run mode activated from CLI execution.")
    current_config = load_config()
    if not current_config.get('city') or not current_config.get('country'):
        LOG.error("Dry run cannot proceed without city/country configuration.")
        return 1

    scheduler_instance = get_scheduler_instance(calendar_service=None) # No calendar service needed for dry run
    scheduler_instance.run_dry_run_simulation(
        city=current_config['city'],
        country=current_config['country'],
        method=current_config.get('method'),
        school=current_config.get('school')
    )
    return 0

def main(argv: list[str] | None = None) -> int:
    """Main entry point for the application."""
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

    # Handle --dry-run directly
    if args.dry_run:
        return execute_cli_dry_run(args)

    # For all other cases, we launch the tray icon setup.
    from src import tray_icon
    return tray_icon.setup_tray_icon(raw_argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
