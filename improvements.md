### Extended Existing Features:

**1. Reconfigure Prayer Time on Location Change**

*   **Extended Description:** When the user's geographical location changes, the application should automatically or manually reconfigure prayer times and associated calendar events/scheduling to reflect the new location's timings. This ensures the accuracy and relevance of prayer notifications and calendar entries.
*   **Technical Steps:**
    1.  **Location Detection:** Implement a mechanism to detect changes in the user's location (e.g., using IP-based geolocation, system location services if available, or manual input via settings).
    2.  **Trigger Reconfiguration:** Upon detecting a significant location change, prompt the user for confirmation to update prayer times.
    3.  **Prayer Time Calculation:** Recalculate prayer times using the new location's coordinates (latitude, longitude) and the user's chosen calculation method (e.g., ISNA, MWL).
    4.  **Calendar Update:** Update existing prayer time entries in the integrated calendar (e.g., Google Calendar) with the new timings. This may involve deleting old events and creating new ones.
    5.  **Scheduler Adjustment:** Adjust the internal scheduler (`scheduler.py`) to trigger notifications and actions based on the newly calculated prayer times.
    6.  **User Notification:** Inform the user about the successful update of prayer times and scheduling.
*   **Related Modules:**
    *   `src/prayer_times.py`: For prayer time calculation.
    *   `src/calendar_api/google_calendar.py`: For interacting with Google Calendar.
    *   `src/scheduler.py`: For managing scheduled events and notifications.
    *   `src/gui.py` / `src/tray_icon.py`: For user prompts and notifications.
    *   `src/state.py`: To store and retrieve user's location and prayer time settings.
    *   `src/config/schema.py`: To define location-related settings.

**2. Prompt for Calendar Integration if `token.json` is Missing**

*   **Extended Description:** If the `token.json` file (which stores Google API authentication tokens) is not found, the application should gracefully inform the user that calendar integration features are unavailable. It should then offer the user the option to authenticate and enable calendar integration, explaining the benefits (e.g., automatic prayer time events in their personal calendar).
*   **Technical Steps:**
    1.  **Check for `token.json`:** At application startup or when calendar features are accessed, verify the existence of `token.json`.
    2.  **Prompt User:** If `token.json` is missing, display a clear and user-friendly dialog box (`gui.py`) asking if they want to enable calendar integration.
    3.  **Explain Benefits:** Briefly explain the advantages of calendar integration (e.g., "Sync prayer times to your Google Calendar," "Get reminders directly in your calendar").
    4.  **Initiate Authentication Flow:** If the user agrees, initiate the Google OAuth 2.0 authentication flow (`src/auth/google_auth.py`) to obtain the necessary tokens.
    5.  **Handle Authentication Success/Failure:**
        *   On success, save the `token.json` file and enable calendar features.
        *   On failure, inform the user and allow them to retry or proceed without calendar integration.
    6.  **Update UI:** Reflect the calendar integration status in the application's UI.
*   **Related Modules:**
    *   `src/auth/google_auth.py`: Handles Google OAuth authentication and token management.
    *   `src/auth/auth_manager.py`: Manages authentication state.
    *   `src/gui.py`: For displaying prompts and dialogs.
    *   `src/calendar_api/google_calendar.py`: Relies on `token.json` for API calls.

### Suggested Other Important Features:

**1. Customizable Adhan/Notification Sounds**

*   **Description:** Allow users to select custom audio files (MP3, WAV) for Adhan and other prayer time notifications, providing a more personalized experience.
*   **Technical Steps:**
    *   Add a setting in the UI for users to browse and select audio files from their local system.
    *   Store the path to the custom audio file in the application's configuration.
    *   Modify the notification system to play the custom audio file if one is set; otherwise, fall back to the default sounds.
*   **Related Modules:** `src/gui.py`, `src/config/schema.py`, `src/scheduler.py`, `src/assets/`.

**4. Multi-language Support**

*   **Description:** Enable the application's interface and notifications to be displayed in multiple languages, broadening its accessibility and user base.
*   **Technical Steps:**
    *   Implement an internationalization (i18n) framework (e.g., `gettext` for Python/Qt's built-in i18n).
    *   Externalize all user-facing strings into translation files.
    *   Provide a language selection option in the settings.
    *   Translate the strings into desired languages.
*   **Related Modules:** `src/gui.py`, `src/config/schema.py`, and potentially new localization files/directories.