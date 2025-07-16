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
from src import gui, focus_steps, scheduler
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
ICONS = {}

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
    from src.actions import focus_mode
    focus_mode(is_modal=True)

@run_in_qt_thread
def _show_modal_focus_window():
    """Shows the focus window, ensuring it runs on the main Qt thread."""
    from src.actions import focus_mode
    LOG.info("Triggering modal focus mode.")
    focus_mode(is_modal=True)


def _execute_dry_run_simulation():
    """
    Executes the logic for a dry run, including audio feedback and focus mode.
    This is designed to run in a background thread to avoid freezing the GUI.
    """
    LOG.info("Executing dry run simulation in background thread.")
    
    current_config = load_config()
    
    # Initialize services needed for the dry run
    calendar_service = None
    try:
        creds = get_google_credentials()
        calendar_service = GoogleCalendarService(creds)
    except (CredentialsNotFoundError, Exception) as e:
        LOG.warning(f"Could not initialize Google Calendar for dry run: {e}")

    # Create an event to signal when the audio is done
    audio_finished_event = threading.Event()

    # Get the scheduler instance
    scheduler_instance = scheduler.get_scheduler_instance(calendar_service)

    # For dry run, use the short completion sound instead of the full adhan
    from src.config.security import get_asset_path
    dry_run_audio_path = str(get_asset_path('complete_sound.wav'))
    scheduler_instance.set_audio_path(dry_run_audio_path)

    # Run a one-time refresh, passing the event to the scheduler
    scheduler_instance.refresh(
        city=current_config['city'],
        country=current_config['country'],
        method=current_config.get('method'),
        school=current_config.get('school'),
        dry_run=True,
        dry_run_event=audio_finished_event
    )
    scheduler_instance.run() # Start the scheduler to execute the job

    # Wait for the audio to finish playing, with a timeout
    LOG.info("Waiting for dry run job to execute and audio to play...")
    event_was_set = audio_finished_event.wait(timeout=90) # Wait up to 90s

    # If the event was set, the audio finished. Now trigger focus mode.
    if event_was_set:
        LOG.info("Audio finished. Now triggering focus mode on the main thread.")
        _show_modal_focus_window()
    else:
        LOG.warning("Dry run timed out waiting for audio to finish.")

    LOG.info("Dry run simulation finished.")


@run_in_qt_thread
def run_gui_dry_run(checked=False):
    """Triggers a one-time dry run of the scheduler with GUI/audio output."""
    LOG.info("GUI Dry run triggered from tray icon.")
    current_config = load_config()
    if not current_config.get('city') or not current_config.get('country'):
        QMessageBox.warning(None, "Configuration Missing", "Please configure city and country in settings before running a dry run.")
        return

    # Run the simulation in a background thread to avoid freezing the GUI
    dry_run_thread = threading.Thread(target=_execute_dry_run_simulation, daemon=True)
    dry_run_thread.start()

    

    

@run_in_qt_thread
def sync_calendar(checked=False):
    """Triggers a manual, one-time sync of the calendar."""
    LOG.info("Manual calendar sync triggered from tray icon.") # Changed to LOG.info
    scheduler.run_scheduler_in_thread(one_time_run=True)

@run_in_qt_thread
def check_for_updates(checked=False):
    """Placeholder for checking for new application updates."""
    QMessageBox.information(None, "Check for Updates", "You are currently running the latest version.")

@run_in_qt_thread
def quit_app(checked=False):
    """Safely quits the QApplication."""
    LOG.info("Quit action triggered from tray icon menu.") # Changed to LOG.info
    QApplication.instance().quit()

def setup_tray_icon(argv: list[str] | None = None):
    """
    Initializes the QApplication and the system tray icon.
    This is now the main entry point for any GUI-related activity.
    It handles argument parsing and decides the application's behavior.
    """
    app = QApplication(sys.argv if argv is None else [sys.argv[0]] + argv)
    app.setQuitOnLastWindowClosed(False)


    # --- Normal GUI Mode ---
    # Initialize icons after QApplication is created.
    global ICONS
    ICONS = {state: create_q_icon(BASE_ICON_PATH, state) for state in AppState}

    # Create the tray icon and menu
    tray_icon = QSystemTrayIcon(ICONS[AppState.IDLE], app)
    tray_icon.setToolTip("Prayer Player")
    
    menu = QMenu()
    
    # --- Menu Actions ---
    settings_action = QAction("Settings...", triggered=show_settings)
    focus_action = QAction("Start Focus Mode", triggered=start_focus_mode)
    sync_action = QAction("Sync Calendar", triggered=sync_calendar)
    dry_run_action = QAction("Run Dry Run", triggered=run_gui_dry_run)
    update_action = QAction("Check for Updates...", triggered=check_for_updates)
    quit_action = QAction("Quit", triggered=quit_app)
    
    menu.addAction(settings_action)
    menu.addAction(focus_action)
    menu.addAction(sync_action)
    menu.addAction(dry_run_action)
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

    # Initialize Calendar Service and pass to scheduler
    calendar_service = None
    try:
        creds = get_google_credentials()
        calendar_service = GoogleCalendarService(creds)
        LOG.info("Google Calendar service initialized in tray icon setup.")
    except CredentialsNotFoundError as e:
        LOG.warning(f"Google Calendar credentials not found or invalid: {e}. Calendar integration will be disabled.")
    except Exception as e:
        LOG.error(f"Error initializing Google Calendar service: {e}. Calendar integration will be disabled.")

    # Start the main prayer time scheduler loop, passing the calendar service
    scheduler.run_scheduler_in_thread(calendar_service=calendar_service)

    # On first run, if config is missing, show settings
    current_config = load_config()
    if not current_config.get('city') or not current_config.get('country'):
        LOG.info("Configuration not found, showing settings window.") # Changed to LOG.info
        show_settings()

    return app.exec()
