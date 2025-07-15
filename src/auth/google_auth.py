import os
import json
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from appdirs import user_data_dir


class CredentialsNotFoundError(Exception):
    pass


SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/userinfo.email', 'openid']

APP_NAME = "PrayerPlayer"
APP_AUTHOR = "Omar"

# Determine the base path for resources, considering PyInstaller bundling.
# In a PyInstaller bundle, sys._MEIPASS points to the temporary directory
# where the application's data files are extracted.
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    BASE_PATH = sys._MEIPASS
else:
    # For development, determine the project root dynamically.
    # This assumes google_auth.py is located at src/prayer/auth/google_auth.py
    # and the project root is 4 levels up from this file.
    BASE_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Path for user-specific, writable config files
USER_CONFIG_DIR = user_data_dir(APP_NAME, APP_AUTHOR)
TOKEN_FILE = os.path.join(USER_CONFIG_DIR, 'token.json')
CREDENTIALS_FILE = os.path.join(USER_CONFIG_DIR, 'credentials.json')

def get_google_credentials(reauthenticate=False):
    creds = None
    # Ensure the user config directory exists.
    os.makedirs(USER_CONFIG_DIR, exist_ok=True)

    if reauthenticate and os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
        print("Existing token deleted. Re-authenticating...")

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as token:
            creds = Credentials.from_authorized_user_info(json.load(token), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Check if the credentials file exists in the user's config directory or the project root.
            credentials_path = CREDENTIALS_FILE
            if not os.path.exists(credentials_path):
                credentials_path = os.path.join(BASE_PATH, 'src', 'config', 'security', 'credentials.json')

            if not os.path.exists(credentials_path):
                message = f"'credentials.json' not found.\n\nPlease place your Google API credentials file at:\n{CREDENTIALS_FILE}"
                raise CredentialsNotFoundError(message)

            try:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
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
        print(f"An error occurred: {e}")
        return None

def get_calendar_list(creds):
    """Fetches the user's calendar list."""
    try:
        service = build('calendar', 'v3', credentials=creds)
        calendar_list = service.calendarList().list().execute()
        return calendar_list.get('items', [])
    except Exception as e:
        print(f"An error occurred while fetching calendar list: {e}")
        return []
