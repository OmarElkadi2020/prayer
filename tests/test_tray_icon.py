import unittest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PySide6.QtGui import QIcon, QAction, QPixmap
from PySide6.QtCore import Qt

from src.tray_icon import setup_tray_icon, create_q_icon, show_settings, start_focus_mode, check_for_updates, quit_app
from src.shared.event_bus import EventBus
from src.domain.enums import AppState
from src.domain.scheduler_messages import ApplicationStateChangedEvent, ScheduleRefreshedEvent
from src.config.security import load_config

class TestTrayIcon(unittest.TestCase):

    def setUp(self):
        self.app = QApplication.instance() or QApplication([])
        self.mock_scheduler = MagicMock()
        self.mock_event_bus = MagicMock(spec=EventBus)
        self.mock_tray_icon = MagicMock(spec=QSystemTrayIcon)
        self.mock_menu = MagicMock(spec=QMenu)

        # Patch QSystemTrayIcon and QMenu during setup_tray_icon call
        self.patcher_tray_icon = patch('src.tray_icon.QSystemTrayIcon', return_value=self.mock_tray_icon)
        self.patcher_menu = patch('src.tray_icon.QMenu', return_value=self.mock_menu)
        self.mock_q_tray_icon_cls = self.patcher_tray_icon.start()
        self.mock_q_menu_cls = self.patcher_menu.start()

        # Mock load_config to return a default config
        self.patcher_load_config = patch('src.tray_icon.load_config')
        self.mock_load_config = self.patcher_load_config.start()
        self.mock_load_config.return_value.city = "TestCity"
        self.mock_load_config.return_value.country = "TestCountry"

        # Mock gui.SettingsWindow to prevent actual GUI creation
        self.patcher_settings_window = patch('src.tray_icon.gui.SettingsWindow')
        self.mock_settings_window_cls = self.patcher_settings_window.start()

        # Mock src.actions.run_focus_steps
        self.patcher_run_focus_steps = patch('src.tray_icon.start_focus_mode')
        self.mock_run_focus_steps = self.patcher_run_focus_steps.start()

        # Mock QMessageBox for check_for_updates
        self.patcher_qmessagebox_info = patch('src.tray_icon.QMessageBox.information')
        self.mock_qmessagebox_info = self.patcher_qmessagebox_info.start()

        # Mock QApplication.instance().quit()
        self.patcher_qapp_quit = patch('PySide6.QtWidgets.QApplication.instance')
        self.mock_qapp_instance = self.patcher_qapp_quit.start()
        self.mock_qapp_instance.return_value.quit.return_value = None


    def tearDown(self):
        self.patcher_tray_icon.stop()
        self.patcher_menu.stop()
        self.patcher_load_config.stop()
        self.patcher_settings_window.stop()
        self.patcher_run_focus_steps.stop()
        self.patcher_qmessagebox_info.stop()
        self.patcher_qapp_quit.stop()
        self.app.quit()

    def test_setup_tray_icon(self):
        tray_icon = setup_tray_icon(scheduler_instance=self.mock_scheduler, event_bus=self.mock_event_bus)
        self.assertIsInstance(tray_icon, MagicMock)
        self.mock_q_tray_icon_cls.assert_called_once()
        self.mock_menu.addAction.assert_called()
        self.mock_tray_icon.show.assert_called_once()

if __name__ == '__main__':
    unittest.main()