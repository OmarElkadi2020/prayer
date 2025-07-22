import unittest
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication, QMessageBox
from src.shared.event_bus import EventBus
from src.gui.settings_window import SettingsWindow, Worker
from src.auth import google_auth
from src.domain.config_messages import SaveConfigurationCommand, ConfigurationChangedEvent
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

    @patch('src.gui.settings_window.Worker')
    def test_calendar_integration_prompt_on_credentials_not_found(self, MockWorker):
        # Configure the mock worker instance
        mock_worker_instance = MockWorker.return_value
        mock_worker_instance.authenticate_google_calendar.side_effect = [
            google_auth.CredentialsNotFoundError("No credentials found."),
            MagicMock() # Simulate successful reauthentication
        ]

        # Patch the handle_google_auth_prompt method to simulate user accepting the prompt
        with patch.object(self.settings_window, 'handle_google_auth_prompt') as mock_handle_prompt:
            mock_handle_prompt.side_effect = lambda: self.settings_window.run_google_auth(reauthenticate=True)

            # Connect the mocked worker's signal to the settings window's slot
            mock_worker_instance.prompt_for_auth.connect(self.settings_window.handle_google_auth_prompt)

            self.settings_window.run_google_auth()
            self.settings_window.thread.join() # Wait for the worker thread to finish
            QApplication.processEvents() # Process events to ensure signal is handled

            # Manually emit the signal to trigger the prompt handling
            mock_worker_instance.prompt_for_auth.emit()
            QApplication.processEvents() # Process events after emitting signal

            # Assertions
            MockWorker.assert_called_once() # Ensure a Worker instance was created
            mock_worker_instance.authenticate_google_calendar.assert_called_with(False)
            mock_handle_prompt.assert_called_once() # Ensure the prompt was handled
            # The second call to authenticate_google_calendar comes from handle_google_auth_prompt
            self.assertEqual(mock_worker_instance.authenticate_google_calendar.call_count, 2)
            self.assertEqual(mock_worker_instance.authenticate_google_calendar.call_args_list[0].kwargs['reauthenticate'], False)
            self.assertEqual(mock_worker_instance.authenticate_google_calendar.call_args_list[1].kwargs['reauthenticate'], True)

    @patch('src.gui.settings_window.Worker')
    def test_calendar_integration_prompt_user_declines(self, MockWorker):
        # Configure the mock worker instance
        mock_worker_instance = MockWorker.return_value
        mock_worker_instance.authenticate_google_calendar.side_effect = google_auth.CredentialsNotFoundError("No credentials found.")

        # Patch the handle_google_auth_prompt method to simulate user declining the prompt
        with patch.object(self.settings_window, 'handle_google_auth_prompt') as mock_handle_prompt:
            mock_handle_prompt.side_effect = lambda: None # Simulate user declining

            # Connect the mocked worker's signal to the settings window's slot
            mock_worker_instance.prompt_for_auth.connect(self.settings_window.handle_google_auth_prompt)

            self.settings_window.run_google_auth()
            self.settings_window.thread.join() # Wait for the worker thread to finish
            QApplication.processEvents() # Process events to ensure signal is handled

            # Manually emit the signal to trigger the prompt handling
            mock_worker_instance.prompt_for_auth.emit()
            QApplication.processEvents() # Process events after emitting signal

            # Assertions
            MockWorker.assert_called_once() # Ensure a Worker instance was created
            mock_worker_instance.authenticate_google_calendar.assert_called_once_with(False)
            mock_handle_prompt.assert_called_once() # Ensure the prompt was handled

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