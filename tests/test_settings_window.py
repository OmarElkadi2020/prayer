import unittest
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication
from src.shared.event_bus import EventBus
from src.gui.settings_window import SettingsWindow
from src.domain.config_messages import SaveConfigurationCommand
from src.config.schema import Config

class TestSettingsWindow(unittest.TestCase):

    def setUp(self):
        self.app = QApplication.instance() or QApplication([])
        self.mock_event_bus = MagicMock(spec=EventBus)
        self.patcher_load_config = patch('src.config.security.load_config')
        self.mock_load_config = self.patcher_load_config.start()
        self.mock_load_config.return_value = MagicMock(spec=Config)
        self.mock_load_config.return_value.country = ""
        self.mock_load_config.return_value.city = ""
        self.mock_load_config.return_value.method = 3
        self.mock_load_config.return_value.school = 0
        self.mock_load_config.return_value.enabled_prayers = []
        self.mock_load_config.return_value.custom_audio_path = None
        self.mock_load_config.return_value.google_calendar_id = None
        self.mock_load_config.return_value.log_level = "INFO"

        with patch.object(SettingsWindow, 'check_initial_auth_status'):
            self.settings_window = SettingsWindow(event_bus=self.mock_event_bus)

    def tearDown(self):
        self.patcher_load_config.stop()
        self.app.quit()

    @patch('src.config.security.load_config')
    def test_save_and_close_dispatches_command(self, mock_load_config):
        mock_config_instance = MagicMock(spec=Config)
        mock_config_instance.country = "TestCountry"
        mock_config_instance.city = "TestCity"
        mock_config_instance.dict.return_value = {}
        mock_load_config.return_value = mock_config_instance

        self.settings_window.country_combo.setCurrentText("TestCountry")
        self.settings_window.city_combo.setCurrentText("TestCity")

        self.settings_window.save_and_close()

        self.mock_event_bus.dispatch.assert_called_once()
        dispatched_command = self.mock_event_bus.dispatch.call_args[0][0]
        self.assertIsInstance(dispatched_command, SaveConfigurationCommand)
        self.assertEqual(dispatched_command.config.country, "TestCountry")
        self.assertEqual(dispatched_command.config.city, "TestCity")

if __name__ == '__main__':
    unittest.main()