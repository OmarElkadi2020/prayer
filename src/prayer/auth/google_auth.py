import os
import json
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/userinfo.email', 'openid']

# Determine the project root dynamically
# This assumes google_auth.py is located at src/prayer/auth/google_auth.py
# and the project root is 4 levels up from this file.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CONFIG_DIR = os.path.join(PROJECT_ROOT, 'src', 'prayer', 'config')
TOKEN_FILE = os.path.join(CONFIG_DIR, 'token.json')

def get_google_credentials(reauthenticate=False):
    creds = None
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
            flow = InstalledAppFlow.from_client_secrets_file(
                os.path.join(CONFIG_DIR, 'credentials.json'), SCOPES)
            creds = flow.run_local_server(port=0)
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
