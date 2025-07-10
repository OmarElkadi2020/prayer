from .google_auth import get_google_credentials
class AuthManager:
    def setup_google_credentials(self, reauthenticate=False):
        print("Setting up Google Calendar credentials...")
        get_google_credentials(reauthenticate=reauthenticate)
        print("Google Calendar credentials setup complete.")
