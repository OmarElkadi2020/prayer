from .google_auth import get_google_credentials
from src.config.security import LOG
class AuthManager:
    def setup_google_credentials(self, reauthenticate=False):
        LOG.info("Setting up Google Calendar credentials...")
        get_google_credentials(reauthenticate=reauthenticate)
        LOG.info("Google Calendar credentials setup complete.")
