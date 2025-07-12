# Prayer Player

Prayer Player is a Python application that automatically plays the Adhan (Islamic call to prayer) at the correct times. It fetches prayer times from an online API, schedules the Adhan playback, and can even integrate with your **google** calendar to block out busy slots.

It is designed to run as a background service on Linux desktops (specifically tested on Ubuntu 22.04 with GNOME).

## Features

-   **Automatic Prayer Times:** Fetches daily prayer times for any city using the aladhan.com API.
-   **Scheduling:** Uses `APScheduler` to reliably schedule the Adhan and other actions.
-   **Audio Playback:** Plays the Adhan audio file at the scheduled times.
-   **Calendar Integration:** (Optional) Can connect to your Google calendar to find free time slots and create busy events for prayers.
-   **Focus Mode:** Includes a "focus mode" that can be triggered around prayer times to minimize distractions.
-   **Systemd Service:** Designed to be run as a systemd user service for automatic startup.

---
## Prequests
Python 3 must be installed on your machine

## Quick Setup (Recommended)

To get Prayer Player up and running quickly on your system, use the provided setup script:

```bash
python setup_gui.py
```

This script will guide you through setting up the Python environment, installing dependencies, and configuring the application. The GUI allows you to set your city and country, and also to configure the application to run at startup.

---


### 2. Test the Script Manually

Before creating a service, test the application from your terminal to ensure it's working correctly.

```bash
prayer-player --city "Your City" --country "Your Country"
```

---

## Configuration

You can configure the application using command-line arguments.

| Argument      | Description                                                                                             | Default       | Example                               |
| :------------ | :------------------------------------------------------------------------------------------------------ | :------------ | :------------------------------------ |
| `--city`      | The city for which to fetch prayer times.                                                               | `Deggendorf`  | `--city "Cairo"`                      |
| `--country`   | The country for the city.                                                                               | `Germany`     | `--country "Egypt"`                   |
| `--method`    | The calculation method for prayer times. See [Aladhan API Docs](https://aladhan.com/prayer-times-api#GetTimingsByCity) for details. | `3`           | `--method 5`                          |
| `--school`    | The school of thought for Asr prayer (0 for Shafi'i, Maliki, Hanbali; 1 for Hanafi).                     | `0`           | `--school 1`                          |
| `--audio`     | The path to the Adhan audio file.                                                                       | (Internal)    | `--audio "/path/to/my/adhan.mp3"`     |
| `--cmd`       | If set, treats the `--audio` argument as a shell command instead of a file path.                        | `False`       | `--cmd --audio "aplay /path/to/adhan.wav"` |
| `--dry-run`   | Schedules jobs but does not run the scheduler. Useful for testing.                                      | `False`       | `--dry-run`                           |
| `--log-level` | Sets the logging level.                                                                                 | `INFO`        | `--log-level DEBUG`                   |
| `--focus-now` | Runs the focus mode immediately and then exits.                                                         | `False`       | `--focus-now`                         |
| `--setup-calendar` | Runs the interactive calendar setup and then exits.                                                 | `False`       | `--setup-calendar`                    |

## Calendar Integration

The application can integrate with your Google or Microsoft calendar to automatically find available slots for prayers and create events.

### Setup

1.  **Choose your provider:** Decide whether you want to use Google Calendar or Microsoft Calendar.
2.  **Obtain Credentials:**
    *   **Google Calendar:**
        1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
        2.  Create a new project.
        3.  Enable the "Google Calendar API".
        4.  Create credentials for a "Desktop app".
        5.  Download the `credentials.json` file and place it in the root of the project directory.
3.  **Run the setup command:**
    ```bash
    prayer-player --setup-calendar
    ```
    This will open a browser window and ask you to authorize the application. After running this command, ensure you successfully complete the authentication flow in your browser. A successful authentication will typically redirect you to a localhost page with a success message.

---

## Running as a Background Service

To ensure Prayer Player runs continuously in the background, you can set it up as a system service on your operating system.

### Linux (systemd User Service)

This is the recommended method for Linux distributions using systemd (e.g., Ubuntu, Fedora).


1.  **Managing the Service:**
    -   **Restart after code changes:** `systemctl --user restart prayer-player.service`
    -   **Stop the service:** `systemctl --user stop prayer-player.service`
    -   **Disable automatic startup:** `systemctl --user disable prayer-player.service`
    -   **Check logs:**  
        View recent logs with:  
        ```bash
        journalctl --user-unit prayer-player.service --since "1 hour ago"
        ```
        Or follow logs in real time:  
        ```bash
        journalctl --user-unit prayer-player.service -f
        ```

## Uninstallation

To remove the Prayer Player application and all related files, use the provided uninstaller script:

```bash
python uninstall.py
```

This script will stop any running background services, remove the service configurations, and delete the virtual environment and configuration files.