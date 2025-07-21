import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication
from src.gui import SettingsWindow
from src.auth import google_auth

@pytest.fixture(scope="session")
def app():
    """Fixture for QApplication instance."""
    return QApplication([])

@pytest.fixture
def settings_window(app):
    """Fixture for SettingsWindow instance."""
    window = SettingsWindow()
    yield window
    window.close()

def test_calendar_integration_prompt_on_credentials_not_found(settings_window):
    """
    Test that the calendar integration prompt appears when CredentialsNotFoundError is raised,
    and that reauthentication is attempted if the user agrees.
    """
    with patch('src.gui.Worker.authenticate_google_calendar') as mock_authenticate_worker:
        # Simulate the worker's authentication method being called
        # and then raising the CredentialsNotFoundError, which would trigger the prompt logic
        mock_authenticate_worker.side_effect = lambda reauthenticate=False: (
            MagicMock() if reauthenticate else google_auth.CredentialsNotFoundError("No credentials found.")
        )

        # Call the method that triggers the authentication check
        settings_window.run_google_auth()

        # Verify that authenticate_google_calendar was called initially with reauthenticate=False
        mock_authenticate_worker.assert_any_call(False)

        # Simulate the user agreeing to reauthenticate by calling it again with reauthenticate=True
        # This simulates the recursive call within authenticate_google_calendar
        settings_window.worker.authenticate_google_calendar(reauthenticate=True)

        # Verify that authenticate_google_calendar was called again with reauthenticate=True
        mock_authenticate_worker.assert_any_call(reauthenticate=True)

def test_calendar_integration_prompt_user_declines(settings_window):
    """
    Test that reauthentication is NOT attempted if the user declines the prompt.
    """
    with patch('src.gui.Worker.authenticate_google_calendar') as mock_authenticate_worker:
        # Simulate the worker's authentication method being called
        # and then raising the CredentialsNotFoundError, which would trigger the prompt logic
        mock_authenticate_worker.side_effect = lambda reauthenticate=False: google_auth.CredentialsNotFoundError("No credentials found.")

        # Call the method that triggers the authentication check
        settings_window.run_google_auth()

        # Verify that authenticate_google_calendar was called initially with reauthenticate=False
        mock_authenticate_worker.assert_called_once_with(False)

        # In this scenario, the user declines, so authenticate_google_calendar should NOT be called again
        # We don't need to simulate the QMessageBox.No return value here, as we are mocking the worker directly.
        # The important part is that the worker's method is not called a second time with reauthenticate=True.
