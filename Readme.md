# Prayer Player
Prayer Player is an intelligent assistant that helps you seamlessly integrate your prayer routine into your busy schedule. By fetching accurate prayer times and intelligently arranging Adhan playback and focused prayer steps within your calendar's free slots, it ensures you never miss a prayer while maintaining work efficiency. Designed to run quietly in the background, Prayer Player automates scheduling and reminders, allowing you to prioritize your daily prayers without manual effort or disruption to your workflow.

## Feature
-   **Automatic Prayer Times:** Fetches daily prayer times for any city using the aladhan.com API.
-   **Scheduling:** Uses `APScheduler` to reliably schedule the Adhan and other actions.
-   **Audio Playback:** Plays the Adhan audio file at the scheduled times.
    -   **Calendar Integration:** The calendar integration is more sophisticated: it's about intelligently arranging adhan and focus steps within free slots
        identified within the broader prayer timespan in the user's calendar. This implies the application actively manages and optimizes the
        scheduling of these events based on calendar availability.
-   **Focus Mode:** Includes a "focus mode" that can be triggered around prayer times to minimize distractions.
-   **Systemd Service:** Designed to be run as a systemd user service for automatic startup.

---
## Prequests
Python 3 must be installed on your machine

## Installation

### For End-Users (Recommended)

For the easiest installation, download the pre-built installer for your operating system from the [releases page](https://github.com/your-repo/prayer-player/releases) (replace with actual releases URL). These installers handle all dependencies and system integration, including setting up the application to run at startup.

### For Developers and Advanced Users (Manual Setup)

If you want to run Prayer Player from source or contribute to its development, follow these steps:

#### Prerequisites
Python 3 must be installed on your machine.

#### Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-repo/prayer
    cd prayer
    ```
2.  **Run the installer script:**
    ```bash
    python installer.py
    ```
    This script will create a virtual environment, install all necessary Python dependencies, and run tests to verify the setup.

#### Running the Application

After installation, you can run the application from the project root:

**Linux/macOS:**
```bash
./myenv/bin/prayer-player
```

**Windows:**
```bash
.\myenv\Scripts\prayer-player.exe
```

The application will start with a system tray icon. Right-click the icon to access Settings and configure your location, prayer calculation methods, and Google Calendar integration. You can also configure the application to run at startup from within the Settings window.

---

## Configuration

The application is primarily configured through its graphical user interface (GUI) accessible via the system tray icon.

For advanced use cases, the `prayer-player` executable also supports command-line arguments:

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

The application intelligently integrates with your Google or Microsoft calendar to find free slots within prayer timespans, and then arranges adhan and focus steps within these available slots. This active management and optimization of scheduling is configured via the application's Settings GUI.

### Manual Setup (if not using GUI)

If you need to set up calendar integration without using the GUI (e.g., for headless environments or troubleshooting), you can follow these steps:

1.  **Choose your provider:** Decide whether you want to use Google Calendar or Microsoft Calendar.
2.  **Obtain Credentials:**
    *   **Google Calendar:**
        1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
        2.  Create a new project.
        3.  Enable the "Google Calendar API".
        4.  Create credentials for a "Desktop app".
        5.  Download the `google_client_config.json` file and place it in the root of the project directory.
3.  **Run the setup command:**
    ```bash
    prayer-player --setup-calendar
    ```
    This will open a browser window and ask you to authorize the application. After running this command, ensure you successfully complete the authentication flow in your browser. A successful authentication will typically redirect you to a localhost page with a success message.

---

## Uninstallation

To remove the Prayer Player application and all related files (for manual/developer setups), use the provided uninstaller script:

```bash
python uninstall.py
This script will remove the virtual environment and configuration files. If you installed via a standalone installer, please use your operating system's standard uninstallation method (e.g., "Add or Remove Programs" on Windows, dragging to Trash on macOS).

---

## License

This project is licensed under the GPLv3 License - see the [LICENSE](LICENSE) file for details.