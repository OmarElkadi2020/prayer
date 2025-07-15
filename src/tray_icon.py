import sys
import threading
import time
from importlib import resources

from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction, QPixmap
from PySide6.QtCore import QTimer, QObject, Signal
from datetime import datetime, timedelta

from PIL import Image, ImageDraw
from PIL.ImageQt import ImageQt

from src.config.security import load_config
from src import gui, focus_steps, scheduler
from src.state import state_manager, AppState

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
        print(f"Warning: Asset '{resource}' not found in package '{package}'.")
        return ""

BASE_ICON_PATH = get_asset_path('src.assets', 'mosque.png')
if not BASE_ICON_PATH:
    print("Error: Could not find 'mosque.png'. The application cannot start.")
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

def run_in_qt_thread(target_func):
    """Decorator to ensure a function runs in the Qt GUI thread."""
    def wrapper(*args, **kwargs):
        print(f"[DEBUG] Scheduling {target_func.__name__} on Qt thread.")
        QTimer.singleShot(0, lambda: target_func(*args, **kwargs))
    return wrapper

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
    global focus_window
    if focus_window is None or not focus_window.isVisible():
        focus_window = focus_steps.StepWindow()
        focus_window.show()
        focus_window.activateWindow()
    else:
        focus_window.activateWindow()

@run_in_qt_thread
def run_gui_dry_run(checked=False):
    """Triggers a one-time dry run of the scheduler with GUI/audio output."""
    print("GUI Dry run triggered from tray icon.")
    # Get the scheduler instance (it will be created if it doesn't exist)
    current_config = load_config()
    if not current_config.get('city') or not current_config.get('country'):
        QMessageBox.warning(None, "Configuration Missing", "Please configure city and country in settings before running a dry run.")
        return

    # Ensure the scheduler is running in the background
    scheduler_instance = scheduler.get_scheduler_instance()
    scheduler_instance.run() # Start if not already running

    # Refresh the schedule with dry_run=True to get immediate jobs
    scheduler_instance.refresh(
        city=current_config['city'],
        country=current_config['country'],
        method=current_config.get('method'),
        school=current_config.get('school'),
        dry_run=True
    )
    print("Jobs in scheduler after refresh:")
    for job in scheduler_instance.scheduler.get_jobs():
        print(f"- Job ID: {job.id}, Next Run Time: {job.next_run_time}")

    

    

@run_in_qt_thread
def sync_calendar(checked=False):
    """Triggers a manual, one-time sync of the calendar."""
    print("Manual calendar sync triggered from tray icon.")
    scheduler.run_scheduler_in_thread(one_time_run=True)

@run_in_qt_thread
def check_for_updates(checked=False):
    """Placeholder for checking for new application updates."""
    QMessageBox.information(None, "Check for Updates", "You are currently running the latest version.")

@run_in_qt_thread
def quit_app(checked=False):
    """Safely quits the QApplication."""
    print("Quit action triggered from tray icon menu.")
    QApplication.instance().quit()

def setup_tray_icon():
    """
    Initializes the QApplication and the system tray icon using PySide6.
    """
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

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

    # Start the main prayer time scheduler loop
    scheduler.run_scheduler_in_thread()

    # On first run, if config is missing, show settings
    current_config = load_config()
    if not current_config.get('city') or not current_config.get('country'):
        print("Configuration not found, showing settings window.")
        show_settings()

    return app.exec()
