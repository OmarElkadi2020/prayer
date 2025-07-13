import pystray
from PIL import Image, ImageDraw
import sys
import threading
import time
from importlib import resources
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer

from prayer import gui, focus_steps, scheduler, config
from prayer.state import state_manager, AppState

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

BASE_ICON_PATH = get_asset_path('prayer.assets', 'mosque.png')
if not BASE_ICON_PATH:
    print("Error: Could not find 'mosque.png'. The application cannot start.")
    sys.exit(1)

def create_icon(base_path, state: AppState):
    """Creates a dynamic icon by adding a colored dot to the base image."""
    try:
        image = Image.open(base_path).convert("RGBA")
        if state != AppState.IDLE:
            draw = ImageDraw.Draw(image)
            # Position and size of the dot
            width, height = image.size
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
        return image
    except FileNotFoundError:
        # Return a placeholder if the base icon is missing
        return Image.new("RGBA", (64, 64), (0, 0, 0, 0))

ICONS = {state: create_icon(BASE_ICON_PATH, state) for state in AppState}

def run_in_qt_thread(target_func):
    """Decorator to ensure a function runs in the Qt GUI thread."""
    def wrapper(*args, **kwargs):
        QTimer.singleShot(0, lambda: target_func(*args, **kwargs))
    return wrapper

@run_in_qt_thread
def show_settings():
    """Creates and shows the settings window."""
    global settings_window
    if settings_window is None or not settings_window.isVisible():
        settings_window = gui.SettingsWindow()
        settings_window.show()
        settings_window.activateWindow()
    else:
        settings_window.activateWindow()

@run_in_qt_thread
def start_focus_mode():
    """Creates and shows the focus steps window."""
    global focus_window
    if focus_window is None or not focus_window.isVisible():
        focus_window = focus_steps.StepWindow()
        focus_window.show()
        focus_window.activateWindow()
    else:
        focus_window.activateWindow()

def sync_calendar():
    """Triggers a manual, one-time sync of the calendar."""
    print("Manual calendar sync triggered from tray icon.")
    scheduler.run_scheduler_in_thread(one_time_run=True)

@run_in_qt_thread
def check_for_updates():
    """Placeholder for checking for new application updates."""
    QMessageBox.information(None, "Check for Updates", "You are currently running the latest version.")

def quit_action(icon):
    """Stops the tray icon and quits the application."""
    print("Quit action triggered.")
    icon.stop()
    QApplication.instance().quit()

def update_tray_status(icon):
    """
    This function runs in a loop in a separate thread to keep the tray icon
    and its menu text updated based on the global state.
    """
    while icon.visible:
        # Update Icon
        current_state = state_manager.state
        icon.icon = ICONS.get(current_state, ICONS[AppState.IDLE])

        # pystray menu items are tuples, so we have to rebuild the menu to update text
        new_menu = pystray.Menu(
            pystray.MenuItem('Settings...', show_settings),
            pystray.MenuItem('Quit', lambda: quit_action(icon))
        )
        icon.menu = new_menu
        
        time.sleep(ICON_UPDATE_INTERVAL)

def setup_tray_icon():
    """
    Initializes the QApplication and the system tray icon, and starts the main event loop.
    """
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Initial menu setup
    initial_menu = pystray.Menu(
        pystray.MenuItem('Settings...', show_settings),
        pystray.MenuItem('Quit', lambda: quit_action(icon))
    )
    icon = pystray.Icon("prayer_player", ICONS[AppState.IDLE], "Prayer Player", initial_menu)

    # Run pystray in its own thread
    icon_thread = threading.Thread(target=icon.run, daemon=True)
    icon_thread.start()

    # Start the status updater thread
    status_thread = threading.Thread(target=update_tray_status, args=(icon,), daemon=True)
    status_thread.start()

    # Start the main prayer time scheduler loop in a separate thread after the GUI is ready
    QTimer.singleShot(0, scheduler.run_scheduler_in_thread)

    # On first run, if config is missing, show settings
    current_config = config.load_config()
    if not current_config.get('city') or not current_config.get('country'):
        print("Configuration not found, showing settings window.")
        show_settings()

    sys.exit(app.exec())

if __name__ == '__main__':
    setup_tray_icon()
