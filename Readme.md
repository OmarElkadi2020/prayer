[![Build and Release Prayer Player](https://github.com/OmarElkadi2020/prayer/actions/workflows/build.yml/badge.svg)](https://github.com/OmarElkadi2020/prayer/actions/workflows/build.yml)

# Prayer Player

Prayer Player is an intelligent assistant that helps you seamlessly integrate your prayer routine into your busy schedule. By fetching accurate prayer times and intelligently arranging Adhan playback and focused prayer steps within your calendar's free slots, it ensures you never miss a prayer while maintaining work efficiency. Designed to run quietly in the background, Prayer Player automates scheduling and reminders, allowing you to prioritize your daily prayers without manual effort or disruption to your workflow.

## Features

-   **Automatic Prayer Times:** Fetches daily prayer times for any city.
-   **Intelligent Scheduling:** Integrates with your Google Calendar to find available slots for prayers and focus sessions, avoiding conflicts with your existing schedule.
-   **Audio Notifications:** Plays the Adhan (call to prayer) at the scheduled times.
-   **Focus Mode:** Helps you minimize distractions during prayer times.
-   **Cross-Platform:** Runs on Windows, macOS, and Linux.
-   **System Tray Integration:** Provides a convenient tray icon to access settings and control the application.

## Installation

The easiest way to install Prayer Player is to download the latest installer for your operating system from the [**GitHub Releases**](https://github.com/OmarElkadi2020/prayer/actions/workflows/release.yml) page.

| OS      | File Type |
| :------ | :-------- |
| Windows | `.exe`    |
| macOS   | `.dmg`    |
| Linux   | `.deb`    |

## Getting Started

1.  **Launch the application.** After installation, you can find Prayer Player in your system's application menu.
2.  **Configure your location.** When you first run the application, a settings window will appear. Set your city and country to ensure accurate prayer times.
3.  **Customize settings.** Use the settings window to choose your preferred prayer time calculation method, select a custom Adhan sound, and connect your Google Calendar.
4.  **Let it run.** The application will run in the background and notify you at prayer times. You can access the settings at any time from the system tray icon.

---

## Contributing

We welcome contributions to Prayer Player! Whether you want to fix a bug, add a feature, or improve the documentation, your help is appreciated.

### Development Setup

To get started with development, you'll need to set up a local development environment.

1.  **Prerequisites:**
    -   [Python 3.8+](https://www.python.org/downloads/)
    -   [Git](https://git-scm.com/downloads)

2.  **Clone the repository:**
    ```bash
    git clone https://github.com/Omar-Elawady/prayer-player.git
    cd prayer-player
    ```

3.  **Run the installer script:**
    This script will create a virtual environment (`myenv`) and install all the necessary dependencies.
    ```bash
    python installer.py
    ```

4.  **Run the application:**
    -   **Linux/macOS:**
        ```bash
        ./myenv/bin/prayer-player
        ```
    -   **Windows:**
        ```bash
        .\myenv\Scripts\prayer-player.exe
        ```

### Running Tests

The project uses `pytest` for testing. To run the tests, first install the development dependencies:

```bash
pip install -r requirements-dev.txt
```

Then, run `pytest` from the project root:

```bash
pytest
```

### Building from Source

The `build.py` script handles the process of building the application from source.

-   **Build the executable:**
    ```bash
    python build.py build
    ```
-   **Create an installer package:**
    ```bash
    python build.py package
    ```

## License

This project is licensed under the GPLv3 License. See the [LICENSE](LICENSE) file for details.
