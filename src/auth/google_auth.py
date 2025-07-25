import os
import json
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from appdirs import user_data_dir
from src.config.security import LOG



class CredentialsNotFoundError(Exception):
    pass


SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/userinfo.email', 'openid']

APP_NAME = "PrayerPlayer"
APP_AUTHOR = "Omar"

# Path for user-specific, writable config files
USER_CONFIG_DIR = user_data_dir(APP_NAME, APP_AUTHOR)
TOKEN_FILE = os.path.join(USER_CONFIG_DIR, 'token.json')
# CREDENTIALS_FILE is now accessed via importlib.resources

def get_google_credentials(reauthenticate=False):
    creds = None
    # Ensure the user config directory exists.
    os.makedirs(USER_CONFIG_DIR, exist_ok=True)

    if reauthenticate and os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
        LOG.info("Existing token deleted. Re-authenticating...")

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as token:
            creds = Credentials.from_authorized_user_info(json.load(token), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Check if the credentials file exists in the user's config directory or the project root.
            try:
                config_path = None
                # Define system-wide config path for installed applications
                SYSTEM_CONFIG_PATH = os.path.join('/usr', 'share', APP_NAME.lower(), 'config', 'security', 'google_client_config.json')

                if os.path.exists(SYSTEM_CONFIG_PATH):
                    config_path = SYSTEM_CONFIG_PATH
                # 2. Check PyInstaller temporary extraction path (for bundled applications)
                elif getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                    pyinstaller_path = os.path.join(sys._MEIPASS, 'config', 'security', 'google_client_config.json')
                    if os.path.exists(pyinstaller_path):
                        config_path = pyinstaller_path
                # 3. Fallback to relative path (for local development)
                else:
                    dev_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'security', 'google_client_config.json')
                    if os.path.exists(dev_path):
                        config_path = dev_path

                if config_path: # Only proceed if a config_path was found
                    flow = InstalledAppFlow.from_client_secrets_file(config_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                else:
                    raise FileNotFoundError("Google API client configuration file not found.")

            except FileNotFoundError:
                message = (
                    "Google API credentials file not found within the application bundle.\n\n"
                    "Please ensure the application is correctly packaged or that 'src/config/security/google_client_config.json' exists in development mode."
                )
                raise CredentialsNotFoundError(message)
            except Exception as e:
                raise CredentialsNotFoundError(f"Failed to obtain new credentials: {e}") from e
        
        # If after all attempts, creds is still None or invalid, raise an error
        if not creds or not creds.valid:
            raise CredentialsNotFoundError("Could not obtain valid Google API credentials.")

        # Save the new token
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            
    return creds


def get_user_info(creds):
    """Fetches user info using the provided credentials."""
    try:
        service = build('oauth2', 'v2', credentials=creds)
        user_info = service.userinfo().get().execute()
        return user_info
    except Exception as e:
        LOG.error(f"An error occurred: {e}")
        return None

def get_calendar_list(creds):
    """Fetches the user's calendar list."""
    try:
        service = build('calendar', 'v3', credentials=creds)
        calendar_list = service.calendarList().list().execute()
        return calendar_list.get('items', [])
    except Exception as e:
        LOG.error(f"An error occurred while fetching calendar list: {e}")
        return []
