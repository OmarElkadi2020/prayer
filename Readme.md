[![Build Status](https://github.com/Omar-Elawady/prayer-player/actions/workflows/build.yml/badge.svg)](https://github.com/Omar-Elawady/prayer-player/actions/workflows/build.yml)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/Omar-Elawady/prayer-player)](https://github.com/Omar-Elawady/prayer-player/releases/latest)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

# Prayer Player

Prayer Player is an intelligent assistant that helps you seamlessly integrate your prayer routine into your busy schedule. By fetching accurate prayer times and intelligently arranging Adhan playback and focused prayer steps within your calendar's free slots, it ensures you never miss a prayer while maintaining work efficiency. Designed to run quietly in the background, Prayer Player automates scheduling and reminders, allowing you to prioritize your daily prayers without manual effort or disruption to your workflow.

## Features

- **Automatic Prayer Times**: Fetches daily prayer times for any city using the aladhan.com API.
- **Intelligent Scheduling**: Integrates with your Google Calendar to find available slots for prayers, ensuring your spiritual duties don't clash with your work.
- **Audio Reminders**: Plays the Adhan (call to prayer) at the scheduled times.
- **Focus Mode**: Helps you concentrate on your prayers by minimizing distractions on your computer.
- **Cross-Platform**: Works on Windows, macOS, and Linux.
- **System Tray Icon**: Provides easy access to settings and controls.

## Installation

### For End-Users (Recommended)

Download the latest installer for your operating system from the [**Releases**](https://github.com/OmarElkadi2020/prayer/releases) page.

| OS      | File Type |
| :------ | :-------- |
| Windows | `.exe`    |
| macOS   | `.dmg`    |
| Linux   | `.deb`    |

### For Developers

If you want to run the application from the source code:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Omar-Elawady/prayer-player.git
    cd prayer-player
    ```

2.  **Run the installer script:**
    This will create a virtual environment and install all the required dependencies.
    ```bash
    python installer.py
    ```

3.  **Run the application:**
    -   **Linux/macOS:**
        ```bash
        ./myenv/bin/prayer-player
        ```
    -   **Windows:**
        ```bash
        .\myenv\Scripts\prayer-player.exe
        ```

## Configuration

The application can be configured through the settings window, which is accessible from the system tray icon.

### Command-line Arguments

| Argument           | Description                                                                                             |
| :----------------- | :------------------------------------------------------------------------------------------------------ |
| `--city`           | The city for which to fetch prayer times.                                                               |
| `--country`        | The country for the city.                                                                               |
| `--method`         | The calculation method for prayer times. See [Aladhan API Docs](https://aladhan.com/prayer-times-api#GetTimingsByCity) for details. |
| `--school`         | The school of thought for Asr prayer (0 for Shafi'i, Maliki, Hanbali; 1 for Hanafi).                     |
| `--dry-run`        | Schedules jobs but does not run the scheduler. Useful for testing.                                      |
| `--log-level`      | Sets the logging level (e.g., `DEBUG`, `INFO`, `WARNING`, `ERROR`).                                       |
| `--install-service`| Installs the application as a systemd service for automatic startup (Linux only).                       |

## Calendar Integration

To integrate with Google Calendar:

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a new project.
3.  Enable the **Google Calendar API**.
4.  Create credentials for a **Desktop app**.
5.  Download the `google_client_config.json` file.
6.  Place the `google_client_config.json` file in the root of the project directory if you are running from source, or in the user's data directory if you are using the installed version. The installer script will handle this for you.

## Uninstallation

-   **Windows**: Use the "Add or Remove Programs" feature.
-   **macOS**: Drag the application to the Trash.
-   **Linux**: Use your package manager to remove the `prayer-player` package (e.g., `sudo apt remove prayer-player`).
-   **Developer Install**: Run the `uninstall.py` script to remove the virtual environment and configuration files.
    ```bash
    python uninstall.py
    ```

## License

This project is licensed under the GPLv3 License - see the [LICENSE](LICENSE) file for details.