import sys
from importlib import resources

from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction, QPixmap
from PySide6.QtCore import Qt

from PIL import Image, ImageDraw
from PIL.ImageQt import ImageQt

from src.config.security import load_config, LOG
from src.gui.settings_window import SettingsWindow
from src import scheduler
from src.qt_utils import run_in_qt_thread
from src.shared.event_bus import EventBus
from src.shared.audio_player import stop_playback
from src.domain.enums import AppState
from src.domain.scheduler_messages import ApplicationStateChangedEvent, ScheduleRefreshedEvent
from src.domain.notification_messages import FocusModeRequestedEvent

# Globals
settings_window = None
focus_window = None

def get_asset_path(package, resource):
    """Safely retrieves the path to a resource file within a package."""
    try:
        with resources.path(package, resource) as p:
            return str(p)
    except (FileNotFoundError, ModuleNotFoundError):
        LOG.warning(f"Asset '{resource}' not found in package '{package}'.")
        return ""

BASE_ICON_PATH = get_asset_path('assets', 'mosque.png')
if not BASE_ICON_PATH:
    LOG.error("Could not find 'mosque.png'. The application cannot start.")
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
        
        qimage = ImageQt(pil_image)
        pixmap = QPixmap.fromImage(qimage)
        return QIcon(pixmap)
        
    except FileNotFoundError:
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        return QIcon(pixmap)

# --- Menu Actions ---
@run_in_qt_thread
def show_settings(checked: bool = False, event_bus: EventBus | None = None):
    """Creates and shows the settings window."""
    global settings_window
    if event_bus is None:
        LOG.error("Cannot open settings window without an event bus.")
        return

    if settings_window is None or not settings_window.isVisible():
        settings_window = SettingsWindow(event_bus)
        settings_window.show()
        settings_window.activateWindow()
    else:
        settings_window.activateWindow()

@run_in_qt_thread
def start_focus_mode(checked=False, event_bus: EventBus | None = None):
    """Triggers focus mode via the event bus."""
    if event_bus is None:
        LOG.error("Cannot trigger focus mode without an event bus.")
        return
    LOG.info("Triggering focus mode from tray icon.")
    event_bus.publish(FocusModeRequestedEvent())

@run_in_qt_thread
def check_for_updates(checked=False):
    """Placeholder for checking for new application updates."""
    QMessageBox.information(None, "Check for Updates", "You are currently running the latest version.")

@run_in_qt_thread
def quit_app(checked=False):
    """Safely quits the QApplication."""
    LOG.info("Quit action triggered from tray icon menu. Stopping audio playback and quitting application.")
    stop_playback()
    QApplication.instance().quit()


def setup_tray_icon(argv: list[str] | None = None, scheduler_instance: scheduler.PrayerScheduler = None, event_bus: EventBus | None = None, dry_run: bool = False):
    """
    Initializes the QApplication and the system tray icon.
    """
    app = QApplication.instance() or QApplication(sys.argv if argv is None else [sys.argv[0]] + argv)
    app.setQuitOnLastWindowClosed(False)

    if dry_run:
        LOG.info("Dry run mode activated. Skipping GUI initialization.")
        if scheduler_instance:
            scheduler_instance.run()
        return 0

    ICONS = {state: create_q_icon(BASE_ICON_PATH, state) for state in AppState}

    tray_icon = QSystemTrayIcon(ICONS[AppState.IDLE], app)
    tray_icon.setToolTip("Prayer Player")
    
    menu = QMenu()
    
    settings_action = QAction("Settings...", triggered=lambda: show_settings(event_bus=event_bus))
    focus_action = QAction("Start Focus Mode", triggered=lambda: start_focus_mode(event_bus=event_bus))
    update_action = QAction("Check for Updates...", triggered=check_for_updates)
    quit_action = QAction("Quit", triggered=quit_app)
    
    menu.addAction(settings_action)
    menu.addAction(focus_action)
    menu.addAction(update_action)
    menu.addSeparator()
    menu.addAction(quit_action)
    
    tray_icon.setContextMenu(menu)
    tray_icon.show()

    # --- Event Handlers ---
    @run_in_qt_thread
    def on_state_update(event: ApplicationStateChangedEvent):
        new_icon = ICONS.get(event.new_state, ICONS[AppState.IDLE])
        if new_icon:
            tray_icon.setIcon(new_icon)

    @run_in_qt_thread
    def on_schedule_refresh(event: ScheduleRefreshedEvent):
        tray_icon.setToolTip(f"Prayer Player\nNext: {event.next_prayer_info}")

    # --- Register Event Handlers ---
    event_bus.register(ApplicationStateChangedEvent, on_state_update)
    event_bus.register(ScheduleRefreshedEvent, on_schedule_refresh)

    if scheduler_instance:
        scheduler_instance.run()

    current_config = load_config()
    if not current_config.city or not current_config.country:
        LOG.info("Configuration not found, showing settings window.")
        show_settings(event_bus=event_bus)

    return app.exec()
