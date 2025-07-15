import os
import json
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from appdirs import user_data_dir
from PySide6.QtWidgets import QApplication, QMessageBox

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
            # Check if the credentials file exists in the user's config directory.
            # If not, the user needs to place it there manually.
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"ERROR: 'credentials.json' not found.")
                print(f"Please place your Google API credentials file at: {CREDENTIALS_FILE}")
                # In a GUI context, you would show a dialog here.
                # For now, we exit if run in a context without a GUI parent.
                if QApplication.instance() is None:
                    sys.exit(1)
                else:
                    # If a GUI is running, show an error message.
                    QMessageBox.critical(
                        None, 
                        "Credentials Not Found",
                        f"'credentials.json' not found.\n\nPlease place your Google API credentials file at:\n{CREDENTIALS_FILE}"
                    )
                    return None

            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
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
