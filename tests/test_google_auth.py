import unittest
from unittest.mock import patch, mock_open, Mock

from src.auth.google_auth import get_google_credentials, SCOPES, TOKEN_FILE, USER_CONFIG_DIR

class TestGoogleAuth(unittest.TestCase):

    @patch('os.makedirs')
    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='{"token": "mock_token"}')
    @patch('google.oauth2.credentials.Credentials.from_authorized_user_info')
    def test_get_google_credentials_existing_valid_token(self, mock_from_authorized_user_info, mock_open_file, mock_exists, mock_makedirs):
        mock_creds = Mock()
        mock_creds.valid = True
        mock_from_authorized_user_info.return_value = mock_creds

        creds = get_google_credentials()

        mock_makedirs.assert_called_once_with(USER_CONFIG_DIR, exist_ok=True)
        mock_exists.assert_called_once_with(TOKEN_FILE)
        mock_open_file.assert_called_once_with(TOKEN_FILE, 'r')
        mock_from_authorized_user_info.assert_called_once_with({"token": "mock_token"}, SCOPES)
        self.assertEqual(creds, mock_creds)

    @patch('os.makedirs')
    @patch('os.path.exists', return_value=True) # TOKEN_FILE exists
    @patch('builtins.open', new_callable=mock_open, read_data='{"token": "expired_token"}')
    @patch('google.oauth2.credentials.Credentials.from_authorized_user_info')
    @patch('src.auth.google_auth.Request') # Patch the class directly
    def test_get_google_credentials_expired_token_refreshes(self, mock_request_class, mock_from_authorized_user_info, mock_open_file, mock_exists, mock_makedirs):
        mock_creds = Mock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = True

        def refresh_side_effect(request):
            mock_creds.valid = True

        mock_creds.refresh.side_effect = refresh_side_effect
        mock_from_authorized_user_info.return_value = mock_creds

        # Set the return value of the mocked Request class
        mock_request_instance = Mock()
        mock_request_class.return_value = mock_request_instance

        creds = get_google_credentials()

        mock_makedirs.assert_called_once_with(USER_CONFIG_DIR, exist_ok=True)
        mock_exists.assert_called_once_with(TOKEN_FILE)
        mock_open_file.assert_any_call(TOKEN_FILE, 'r')
        mock_from_authorized_user_info.assert_called_once_with({'token': 'expired_token'}, SCOPES)
        mock_creds.refresh.assert_called_once_with(mock_request_instance)
        mock_open_file.assert_called_with(TOKEN_FILE, 'w')
        self.assertEqual(creds, mock_creds)
        self.assertTrue(creds.valid)

if __name__ == '__main__':
    unittest.main()