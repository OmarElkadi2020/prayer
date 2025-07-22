# Configuration

Prayer Player is designed to be highly configurable to suit your personal needs. Configuration is primarily handled through a user-friendly graphical interface, accessible via the system tray icon.

## Settings Window

To open the settings window, find the Prayer Player icon in your system tray, right-click it, and select **"Settings"**.

The settings window is organized into several tabs:

### 1. Location & Prayer Times

This is the most critical section for ensuring accurate prayer timings.

-   **City & Country**: Enter your current city and country. The application uses this information to fetch the correct prayer times from the aladhan.com API.
-   **Calculation Method**: The API provides several calculation methods used by different Islamic organizations and conventions around the world. Select the one that is most appropriate for your location or personal preference.
-   **Asr Jurisprudence**: Choose the school of thought for calculating the Asr prayer time.
    -   **Standard**: Shafi'i, Maliki, Hanbali
    -   **Hanafi**

### 2. Enabled Prayers

You can customize which prayers you want to be notified for. By default, all five daily prayers are enabled. Simply uncheck any prayer you wish to disable.

### 3. Audio Settings

-   **Custom Adhan Sound**: While the application comes with a default Adhan sound, you can select your own audio file to be played for notifications. Click the **"Browse"** button to choose a local audio file (`.mp3` or `.wav`).

### 4. Calendar Integration

Prayer Player can intelligently schedule prayers and focus sessions by finding free slots in your Google Calendar.

-   **Google Calendar ID**: To enable this feature, you need to provide your Google Calendar ID (this is usually your email address).
-   **Setup**:
    1.  First, you must obtain your `google_client_config.json` file from the Google Cloud Console. For instructions, see [For Developers - Calendar Integration](04-for-developers.md#calendar-integration).
    2.  Place this file in the application's configuration directory. The `installer.py` script handles this for developer setups if the file is in the project root. For installed versions, you may need to place it manually in the user data directory.
    3.  Once the configuration is in place, the application will guide you through a one-time authentication process in your web browser to grant it access to your calendar.

## Command-line Arguments

For advanced users or for scripting purposes, some configuration options can be set via command-line arguments when launching the application. These arguments will override the settings saved in the configuration file for the current session.

| Argument        | Description                                      |
| :-------------- | :----------------------------------------------- |
| `--city`        | Set the city for prayer times.                   |
| `--country`     | Set the country for the city.                    |
| `--method`      | Set the prayer time calculation method ID.       |
| `--school`      | Set the Asr prayer school (0 for Standard, 1 for Hanafi). |
| `--log-level`   | Set the logging verbosity (e.g., `DEBUG`, `INFO`). |
| `--dry-run`     | Simulate scheduling without running actions.     |
| `--install-service` | Install the app as a systemd service (Linux). |

**Example:**
```bash
# Run Prayer Player for Cairo, Egypt, using the Egyptian General Authority of Survey method.
./myenv/bin/prayer-player --city "Cairo" --country "Egypt" --method 5
```
