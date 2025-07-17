import sys
import threading
import time
from importlib import resources
import logging # Added for logging

from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction, QPixmap
from PySide6.QtCore import QTimer, QObject, Signal
from datetime import datetime, timedelta

from PIL import Image, ImageDraw
from PIL.ImageQt import ImageQt

from src.config.security import load_config, LOG # Import LOG
from src import gui, focus_steps_view, scheduler
from src.state import state_manager, AppState
from src.calendar_api.google_calendar import GoogleCalendarService # Added
from src.auth.google_auth import get_google_credentials, CredentialsNotFoundError # Added

# Globals
settings_window = None
focus_window = None
ICON_UPDATE_INTERVAL = 2  # seconds

def get_asset_path(package, resource):
    """Safely retrieves the path to a resource file within a package."""
    try:
        with resources.path(package, resource) as p:
            return str(p)
    except (FileNotFoundError, ModuleNotFoundError):
        LOG.warning(f"Asset '{resource}' not found in package '{package}'.") # Changed to LOG.warning
        return ""

BASE_ICON_PATH = get_asset_path('src.assets', 'mosque.png')
if not BASE_ICON_PATH:
    LOG.error("Could not find 'mosque.png'. The application cannot start.") # Changed to LOG.error
    sys.exit(1)

def create_q_icon(base_path, state: AppState):
    """Creates a dynamic QIcon by adding a colored dot to the base image."""
    try:
        pil_image = Image.open(base_path).convert("RGBA")
        if state != AppState.IDLE:
            draw = ImageDraw.Draw(pil_image)
            width, height = pil_image.size
            dot_radius = width // 6
            dot_pos = (width - dot_radius * 2, height - dot_radius * 2)
            
            color = {
                AppState.SYNCING: "blue",
                AppState.PRAYER_TIME: "green",
                AppState.ERROR: "red",
            }.get(state, "transparent")

            draw.ellipse(
                (dot_pos[0], dot_pos[1], dot_pos[0] + dot_radius*2, dot_pos[1] + dot_radius*2),
                fill=color,
                outline="white"
            )
        
        # Convert PIL image to QPixmap for use in QIcon
        qimage = ImageQt(pil_image)
        pixmap = QPixmap.fromImage(qimage)
        return QIcon(pixmap)
        
    except FileNotFoundError:
        # Return a placeholder QIcon if the base icon is missing
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        return QIcon(pixmap)

# ICONS will be initialized inside setup_tray_icon after QApplication is created.
# ICONS = {}

# --- GUI Thread Safety ---
# Use a QObject with a signal to safely update the GUI from a background thread.
class IconUpdater(QObject):
    # Signal will emit the application's state, not a GUI object.
    update_state_signal = Signal(AppState)

    def run(self):
        """
        This function runs in a loop in a separate thread and emits the current
        application state periodically.
        """
        while True: # The thread will be a daemon, so it will exit with the app
            current_state = state_manager.state
            self.update_state_signal.emit(current_state)
            time.sleep(ICON_UPDATE_INTERVAL)

from src.qt_utils import run_in_qt_thread

# --- Menu Actions ---
@run_in_qt_thread
def show_settings(checked=False):
    """Creates and shows the settings window."""
    global settings_window
    if settings_window is None or not settings_window.isVisible():
        settings_window = gui.SettingsWindow()
        settings_window.show()
        settings_window.activateWindow()
    else:
        settings_window.activateWindow()

@run_in_qt_thread
def start_focus_mode(checked=False):
    """Creates and shows the focus steps window."""
    from src.actions import run_focus_steps
    run_focus_steps(is_modal=True)

@run_in_qt_thread
def _show_modal_focus_window():
    """Shows the focus window, ensuring it runs on the main Qt thread."""
    from src.actions import run_focus_steps
    LOG.info("Triggering modal focus mode.")
    run_focus_steps(is_modal=True)


@run_in_qt_thread
def check_for_updates(checked=False):
    """Placeholder for checking for new application updates."""
    QMessageBox.information(None, "Check for Updates", "You are currently running the latest version.")

@run_in_qt_thread
def quit_app(checked=False):
    """Safely quits the QApplication."""
    LOG.info("Quit action triggered from tray icon menu.") # Changed to LOG.info
    QApplication.instance().quit()


def setup_tray_icon(argv: list[str] | None = None, scheduler_instance: scheduler.PrayerScheduler = None, dry_run: bool = False):
    """
    Initializes the QApplication and the system tray icon.
    This is now the main entry point for any GUI-related activity.
    It handles argument parsing and decides the application's behavior.
    """
    app = QApplication.instance() or QApplication(sys.argv if argv is None else [sys.argv[0]] + argv)
    app.setQuitOnLastWindowClosed(False)

    if dry_run:
        LOG.info("Dry run mode activated. Skipping GUI initialization.")
        if scheduler_instance:
            scheduler_instance.run()
        return 0 # Return 0 for success in dry run mode, as there's no GUI event loop to run

    # Move create_q_icon and ICONS initialization inside here
    def create_q_icon(base_path, state: AppState):
        """Creates a dynamic QIcon by adding a colored dot to the base image."""
        try:
            pil_image = Image.open(base_path).convert("RGBA")
            if state != AppState.IDLE:
                draw = ImageDraw.Draw(pil_image)
                width, height = pil_image.size
                dot_radius = width // 6
                dot_pos = (width - dot_radius * 2, height - dot_radius * 2)
                
                color = {
                    AppState.SYNCING: "blue",
                    AppState.PRAYER_TIME: "green",
                    AppState.ERROR: "red",
                }.get(state, "transparent")

                draw.ellipse(
                    (dot_pos[0], dot_pos[1], dot_pos[0] + dot_radius*2, dot_pos[1] + dot_radius*2),
                    fill=color,
                    outline="white"
                )
            
            # Convert PIL image to QPixmap for use in QIcon
            qimage = ImageQt(pil_image)
            pixmap = QPixmap.fromImage(qimage)
            return QIcon(pixmap)
            
        except FileNotFoundError:
            # Return a placeholder QIcon if the base icon is missing
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.transparent)
            return QIcon(pixmap)

    # Initialize icons after QApplication is created.
    ICONS = {state: create_q_icon(BASE_ICON_PATH, state) for state in AppState}

    # Create the tray icon and menu
    tray_icon = QSystemTrayIcon(ICONS[AppState.IDLE], app)
    tray_icon.setToolTip("Prayer Player")
    
    menu = QMenu()
    
    # --- Menu Actions ---
    settings_action = QAction("Settings...", triggered=show_settings)
    focus_action = QAction("Start Focus Mode", triggered=start_focus_mode)
    update_action = QAction("Check for Updates...", triggered=check_for_updates)
    quit_action = QAction("Quit", triggered=quit_app)
    
    menu.addAction(settings_action)
    menu.addAction(focus_action)
    menu.addAction(update_action)
    menu.addSeparator()
    menu.addAction(quit_action)
    
    tray_icon.setContextMenu(menu)
    tray_icon.show()

    # --- Background Threads ---
    # This slot will run on the main GUI thread.
    def on_state_update(state):
        new_icon = ICONS.get(state, ICONS[AppState.IDLE])
        if new_icon:
            tray_icon.setIcon(new_icon)

    # Start the icon updater thread
    icon_updater = IconUpdater()
    icon_updater.update_state_signal.connect(on_state_update)
    
    status_thread = threading.Thread(target=icon_updater.run, daemon=True)
    status_thread.start()

    # Start the main prayer time scheduler loop, passing the calendar service
    if scheduler_instance:
        scheduler_instance.run()

    # On first run, if config is missing, show settings
    current_config = load_config()
    if not current_config.city or not current_config.country:
        LOG.info("Configuration not found, showing settings window.") # Changed to LOG.info
        show_settings()

    return app.exec()
