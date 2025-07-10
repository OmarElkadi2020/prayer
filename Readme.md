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

## Quick Setup (Recommended)

To get Prayer Player up and running quickly on your system, use the provided platform-specific setup scripts:

*   **Linux:**
    ```bash
    ./setup_linux.sh
    ```

*   **Windows:**
    Open PowerShell as Administrator and run:
    ```powershell
    .\setup_windows.ps1
    ```

*   **macOS:**
    ```bash
    ./setup_macos.sh
    ```

These scripts will guide you through setting up the Python environment, installing dependencies, and configuring Prayer Player to run in the background or foreground.

---

## Installation and Setup (Manual)

If you prefer a manual setup or need to troubleshoot, follow these steps:

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

## Running as a Background Service

To ensure Prayer Player runs continuously in the background, you can set it up as a system service on your operating system.

### Linux (systemd User Service)

This is the recommended method for Linux distributions using systemd (e.g., Ubuntu, Fedora).

1.  **Create a systemd User Service File:**
    First, ensure your user systemd directory exists:
    ```bash
    mkdir -p ~/.config/systemd/user/
    ```
    Then, create and edit the service file:
    ```bash
    nano ~/.config/systemd/user/prayer-player.service
    ```
    Paste the following content, adjusting the `ExecStart` path and arguments as needed:
    **Important:**
    -   Replace `/home/user/prayer/myenv/bin/prayer-player` with the **absolute path** to the `prayer-player` executable inside your virtual environment.
    -   Update the `--city` and `--country` arguments to your location.

    ```ini
    [Unit]
    Description=Prayer Player Scheduler
    After=network.target

    [Service]
    Type=simple
    ExecStart=/home/user/prayer/myenv/bin/prayer-player --city "Cairo" --country "Egypt"
    Restart=always
    StandardOutput=journal
    StandardError=journal

    [Install]
    WantedBy=default.target
    ```

2.  **Enable and Start the Service:**
    Reload systemd and enable your user service:
    ```bash
    systemctl --user daemon-reload
    systemctl --user enable --now prayer-player.service
    ```
    If you want the service to run even when you are not logged in (e.g., after a reboot without logging in to the desktop), enable linger for your user:
    ```bash
    loginctl enable-linger $USER
    ```

3.  **Check Service Status and Logs:**
    To check if the service is running:
    ```bash
    systemctl --user status prayer-player.service
    ```
    To view its logs:
    ```bash
    journalctl --user -u prayer-player.service -f
    ```

4.  **Managing the Service:**
    -   **Restart after code changes:** `systemctl --user restart prayer-player.service`
    -   **Stop the service:** `systemctl --user stop prayer-player.service`
    -   **Disable automatic startup:** `systemctl --user disable prayer-player.service`

### Windows (using pywin32)

For Windows, you can set up Prayer Player as a native Windows Service using the `pywin32` library.

1.  **Install `pywin32`:**
    Ensure you have `pywin32` installed in your environment:
    ```bash
    pip install pywin32
    ```

2.  **Install the Service:**
    Open an **administrative command prompt** (Run as administrator), navigate to your project's root directory, and run the `windows_service.py` script with the `install` command:
    ```bash
    python src\prayer\windows_service.py install
    ```
    You can specify a username and password if the service needs to run under a specific account with network access:
    ```bash
    python src\prayer\windows_service.py --username ".\LocalSystem" --password "YourPassword" install
    ```

3.  **Start the Service:**
    You can start the service from the Services Manager (search for "Services" in Windows Start Menu) or from the administrative command prompt:
    ```bash
    python src\prayer\windows_service.py start
    ```

4.  **Manage the Service:**
    -   **Stop:** `python src\prayer\windows_service.py stop`
    -   **Restart:** `python src\prayer\windows_service.py restart`
    -   **Uninstall:** `python src\prayer\windows_service.py remove`

    You can also manage the service via the Windows Services Manager GUI.

**Alternative for Windows: NSSM (Non-Sucking Service Manager)**
If you prefer not to use `pywin32` or want to run a PyInstaller-generated executable as a service, `nssm` is a powerful and flexible service wrapper.
1.  Download `nssm` from [https://nssm.cc/download/](https://nssm.cc/download/).
2.  Open an **administrative command prompt** and navigate to the `nssm.exe` directory.
3.  Install the service, pointing to your Python executable and the `__main__.py` script:
    ```bash
    nssm install PrayerPlayer "C:\path\to\your\myenv\Scripts\python.exe" "C:\path\to\your\prayer\src\prayer\__main__.py"
    ```
    Or, if you've created a standalone executable with PyInstaller:
    ```bash
    nssm install PrayerPlayer "C:\path\to\your\dist\prayer-player.exe"
    ```
    You can then start, stop, and manage the service using `nssm start PrayerPlayer`, `nssm stop PrayerPlayer`, etc.

### macOS (launchd Agent)

For macOS, you can use `launchd` to run Prayer Player as a background agent that starts when you log in.

1.  **Create the LaunchAgents Directory:**
    If it doesn't exist, create the `LaunchAgents` directory in your user's Library:
    ```bash
    mkdir -p ~/Library/LaunchAgents/
    ```

2.  **Copy and Edit the `.plist` File:**
    Copy the provided template from the `deployment/` directory to your `LaunchAgents` folder:
    ```bash
    cp deployment/prayer-player.plist ~/Library/LaunchAgents/
    ```
    Then, open the copied file for editing:
    ```bash
    nano ~/Library/LaunchAgents/prayer-player.plist
    ```
    **Important:**
    -   Update the `<string>` tags within `<ProgramArguments>` to point to the **absolute path** of your Python interpreter (e.g., `/usr/bin/env python3` or `/path/to/your/myenv/bin/python3`) and the `__main__.py` script (`/path/to/your/prayer/src/prayer/__main__.py`).
    -   Adjust the `WorkingDirectory` to the absolute path of your project root (e.g., `/path/to/your/prayer`).
    -   Modify the `StandardOutPath` and `StandardErrorPath` to desired log file locations (e.g., `/tmp/prayer-player.stdout.log`).

3.  **Load the Agent:**
    Load the `launchd` agent using `launchctl`:
    ```bash
    launchctl load ~/Library/LaunchAgents/prayer-player.plist
    ```

4.  **Check Agent Status (Optional):**
    To verify if the agent is loaded and running:
    ```bash
    launchctl list | grep com.prayerplayer.scheduler
    ```
    You should see an entry with `com.prayerplayer.scheduler` and a PID if it's active.

5.  **Manage the Agent:**
    -   **Unload (Stop):** `launchctl unload ~/Library/LaunchAgents/prayer-player.plist`
    -   **Load (Start):** `launchctl load ~/Library/LaunchAgents/prayer-player.plist`
    -   To apply changes to the `.plist` file, you must unload and then load it again.

## Standalone Executables (PyInstaller)

For users who prefer not to manage Python environments, you can create a single executable file for Windows, macOS, or Linux using PyInstaller.

1.  **Install PyInstaller:**
    ```bash
    pip install pyinstaller
    ```

2.  **Create the Executable:**
    Navigate to your project's root directory and run:
    ```bash
    pyinstaller src/prayer/__main__.py --name prayer-player --onefile --windowed
    ```
    -   `--name prayer-player`: Sets the name of the executable.
    -   `--onefile`: Creates a single executable file.
    -   `--windowed` (or `-w`): Prevents a console window from opening when the app runs (useful for background apps).

    The executable will be created in the `dist/` directory. You can then distribute this executable. Note that for background services, you would typically use `nssm` (Windows) or `launchd` (macOS) to run this executable.

---

## Uninstallation

To remove the Prayer Player application and all related files, use the provided uninstall scripts. These scripts will stop any running background services, remove the service configurations, and delete the virtual environment and configuration files.

*   **Linux:**
    ```bash
    ./uninstall_linux.sh
    ```

*   **Windows:**
    Open PowerShell as Administrator and run:
    ```powershell
    .\uninstall_windows.ps1
    ```

*   **macOS:**
    ```bash
    ./uninstall_macos.sh
    ```

