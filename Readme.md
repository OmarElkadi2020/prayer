# Prayer Player

Prayer Player is a Python application that automatically plays the Adhan (Islamic call to prayer) at the correct times. It fetches prayer times from an online API, schedules the Adhan playback, and can even integrate with your desktop calendar to block out busy slots.

It is designed to run as a background service on Linux desktops (specifically tested on Ubuntu 22.04 with GNOME).

## Features

-   **Automatic Prayer Times:** Fetches daily prayer times for any city using the aladhan.com API.
-   **Scheduling:** Uses `APScheduler` to reliably schedule the Adhan and other actions.
-   **Audio Playback:** Plays the Adhan audio file at the scheduled times.
-   **Calendar Integration:** (Optional) Can connect to the GNOME Evolution calendar to find free time slots and create busy events for prayers.
-   **Focus Mode:** Includes a "focus mode" that can be triggered around prayer times to minimize distractions.
-   **Systemd Service:** Designed to be run as a systemd user service for automatic startup.

---

## Installation and Setup

### 1. Prepare Your Environment

-   Clone this repository.
-   Create a virtual environment and activate it:

    ```bash
    python3 -m venv myenv
    source myenv/bin/activate
    ```

-   Install the project in editable mode. This will install all dependencies and make the `prayer-player` command available in your shell.

    ```bash
    pip install --upgrade pip
    pip install -e .
    ```

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
    *   **Microsoft Calendar:**
        1.  Go to the [Azure Active Directory admin center](https://aad.portal.azure.com/).
        2.  Create a new application registration.
        3.  Under "Authentication", add a new platform for "Mobile and desktop applications" and add the redirect URI `http://localhost`.
        4.  Get the "Application (client) ID" from the overview page and replace the placeholder value in `src/prayer/calendar_api/microsoft_calendar.py`.
3.  **Run the setup command:**
    ```bash
    prayer-player --setup-calendar
    ```
    This will open a browser window and ask you to authorize the application.

---

## Running as a Background Service (systemd)

### 1. Create a systemd User Service File

1.  Create the user systemd directory if it doesn't exist:

    ```bash
    mkdir -p ~/.config/systemd/user/
    ```

2.  Create and edit the service file:

    ```bash
    nano ~/.config/systemd/user/prayer-player.service
    ```

3.  Paste and adjust the following content.
    **Important:**
    -   Replace `/home/user/prayer/myenv/bin/prayer-player` with the **absolute path** to the `prayer-player` executable inside your virtual environment.
    -   Update the `--city` and `--country` arguments to your location.

    ```ini
    [Unit]
    Description=Prayer Player Scheduler

    [Service]
    Type=simple
    ExecStart=/home/user/prayer/myenv/bin/prayer-player --city "Cairo" --country "Egypt"
    Restart=always

    [Install]
    WantedBy=default.target
    ```

### 2. Enable and Start the Service

Reload and enable your user service:

```bash
systemctl --user daemon-reload
systemctl --user enable --now prayer-player.service
```

If you want the service to run even when you are not logged in, enable linger for your user:

```bash
loginctl enable-linger $USER
```

### 3. Check Service Status and Logs

Check if the service is running and view its logs:

```bash
systemctl --user status prayer-player.service
journalctl --user -u prayer-player.service -f
```

### 4. Managing the Service

-   **Restart after code changes:** If you modify the Python code, restart the service to apply the updates:
    ```bash
    systemctl --user restart prayer-player.service
    ```
-   **Stop the service:**
    ```bash
    systemctl --user stop prayer-player.service
    ```
-   **Disable automatic startup:**
    ```bash
    systemctl --user disable prayer-player.service
    ```
