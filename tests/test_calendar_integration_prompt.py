import unittest
from unittest.mock import patch, MagicMock
import os

# Assuming these are the relevant modules
from src.gui import Worker, SettingsWindow # Import Worker and SettingsWindow
from src.auth import google_auth

class TestCalendarIntegrationPrompt(unittest.TestCase):

    @patch('src.auth.google_auth.get_google_credentials')
    @patch('PySide6.QtWidgets.QMessageBox.question')
    @patch('src.gui.Worker.status_updated') # Mock status updates to avoid GUI calls
    @patch('src.gui.Worker.error') # Mock error signals
    @patch('src.gui.Worker.google_auth_finished') # Mock finished signal
    def test_token_missing_user_agrees_auth_success(self, mock_google_auth_finished, mock_error, mock_status_updated, mock_qmessagebox_question, mock_get_google_credentials):
        # Simulate token.json missing by making get_google_credentials raise an error
        mock_get_google_credentials.side_effect = google_auth.CredentialsNotFoundError("token.json not found")
        # Simulate user agreeing to integrate
        mock_qmessagebox_question.return_value = MagicMock(spec=int) # Mock the return value as an integer
        mock_qmessagebox_question.return_value = 16384 # QMessageBox.Yes

        # Simulate successful re-authentication after the prompt
        mock_get_google_credentials.side_effect = [google_auth.CredentialsNotFoundError("token.json not found"), MagicMock()] # First call fails, second succeeds

        worker = Worker()
        worker.authenticate_google_calendar(reauthenticate=False)

        # Assertions
        self.assertEqual(mock_get_google_credentials.call_count, 2)
        mock_get_google_credentials.call_args_list[0].assert_called_with(reauthenticate=False)
        mock_qmessagebox_question.assert_called_once()
        mock_get_google_credentials.call_args_list[1].assert_called_with(reauthenticate=True)
        mock_google_auth_finished.emit.assert_called_once() # Should emit success signal
        mock_error.emit.assert_not_called()

    @patch('src.auth.google_auth.get_google_credentials')
    @patch('PySide6.QtWidgets.QMessageBox.question')
    @patch('src.gui.Worker.status_updated')
    @patch('src.gui.Worker.error')
    @patch('src.gui.Worker.google_auth_finished')
    def test_token_missing_user_agrees_auth_failure(self, mock_google_auth_finished, mock_error, mock_status_updated, mock_qmessagebox_question, mock_get_google_credentials):
        mock_get_google_credentials.side_effect = [google_auth.CredentialsNotFoundError("token.json not found"), Exception("Auth failed")]
        mock_qmessagebox_question.return_value = 16384 # QMessageBox.Yes

        worker = Worker()
        worker.authenticate_google_calendar(reauthenticate=False)

        mock_get_google_credentials.call_args_list[0].assert_called_with(reauthenticate=False)
        mock_qmessagebox_question.assert_called_once()
        self.assertEqual(mock_get_google_credentials.call_count, 2)
        mock_get_google_credentials.call_args_list[1].assert_called_with(reauthenticate=True)
        mock_google_auth_finished.emit.assert_not_called() # Should not emit success signal on failure
        mock_error.emit.assert_called_once() # Should emit error signal

    @patch('src.auth.google_auth.get_google_credentials')
    @patch('PySide6.QtWidgets.QMessageBox.question')
    @patch('src.gui.Worker.status_updated')
    @patch('src.gui.Worker.error')
    @patch('src.gui.Worker.google_auth_finished')
    def test_token_missing_user_declines(self, mock_google_auth_finished, mock_error, mock_status_updated, mock_qmessagebox_question, mock_get_google_credentials):
        mock_get_google_credentials.side_effect = google_auth.CredentialsNotFoundError("token.json not found")
        mock_qmessagebox_question.return_value = 65536 # QMessageBox.No

        worker = Worker()
        worker.authenticate_google_calendar(reauthenticate=False)

        mock_get_google_credentials.assert_called_once_with(reauthenticate=False)
        mock_qmessagebox_question.assert_called_once()
        mock_google_auth_finished.emit.assert_not_called() # Should not attempt re-auth or emit success
        mock_error.emit.assert_called_once() # Should still emit an error because the initial get_credentials failed

    @patch('src.auth.google_auth.get_google_credentials')
    @patch('PySide6.QtWidgets.QMessageBox.question')
    @patch('src.gui.Worker.status_updated')
    @patch('src.gui.Worker.error')
    @patch('src.gui.Worker.google_auth_finished')
    def test_token_exists(self, mock_google_auth_finished, mock_error, mock_status_updated, mock_qmessagebox_question, mock_get_google_credentials):
        # Simulate token.json existing by making get_google_credentials return a mock credential object
        mock_get_google_credentials.return_value = MagicMock()

        worker = Worker()
        worker.authenticate_google_calendar(reauthenticate=False)

        mock_get_google_credentials.assert_called_once_with(reauthenticate=False)
        mock_qmessagebox_question.assert_not_called() # Should not prompt
        mock_google_auth_finished.emit.assert_called_once() # Should emit success signal
        mock_error.emit.assert_not_called()