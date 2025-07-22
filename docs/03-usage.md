# Usage Guide

Prayer Player is designed to run quietly in the background and be controlled primarily through its system tray icon.

## Running the Application

How you start the application depends on your installation method.

### End-User Installation

If you installed Prayer Player using the `.exe`, `.dmg`, or `.deb` installer, the application should be available in your system's application menu or launcher. Simply find **"Prayer Player"** and open it.

On most systems, you can also configure it to start automatically when you log in.

### Developer Installation

If you followed the developer setup, you need to run the application from the command line within the project directory.

-   **On Linux or macOS:**
    ```bash
    ./myenv/bin/prayer-player
    ```
-   **On Windows:**
    ```bash
    .\myenv\Scripts\prayer-player.exe
    ```

Once launched, the application will add an icon to your system tray.

## Interacting with the Tray Icon

The system tray icon is the main control center for Prayer Player.

-   **Left-Click**: A single left-click on the tray icon will show the upcoming prayer times for the day.
-   **Right-Click**: A right-click opens a context menu with several options:
    -   **Upcoming Prayers**: Shows the same prayer time information as a left-click.
    -   **Settings**: Opens the [Configuration](02-configuration.md) window, allowing you to customize the application's behavior.
    -   **Quit**: Shuts down the application.

## Notifications and Focus Mode

-   **Adhan Notifications**: At each enabled prayer time, the application will play the Adhan sound you have configured.
-   **Focus Mode**: If enabled and configured with calendar integration, the application may also trigger a "Focus Mode." This feature is designed to help you disconnect from your work and prepare for prayer by, for example, dimming the screen or displaying a reminder.

## Command-Line Usage

In addition to the GUI, you can use command-line arguments for specific actions.

-   **Dry Run**: To see the prayer schedule that the application would create without actually running it, use the `--dry-run` flag. This is useful for testing your configuration.
    ```bash
    ./myenv/bin/prayer-player --dry-run
    ```
-   **Install as a Service (Linux)**: To have Prayer Player run automatically as a background service on system startup, you can install it as a systemd service.
    ```bash
    ./myenv/bin/prayer-player --install-service
    ```
    This command needs to be run only once. It will create and enable a systemd user service.

