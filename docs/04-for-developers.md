# For Developers

This document provides information relevant to developers who wish to contribute to Prayer Player, build it from source, or understand its architecture.

## Development Setup

Before you begin, make sure you have followed the [Developer Installation](01-installation.md#developer-installation-from-source) instructions to set up your local environment.

### Running Tests

The project uses `pytest` for testing. To run the test suite, first ensure you have installed the development dependencies:

```bash
# Install both regular and dev requirements
python -m pip install -r requirements.txt -r requirements-dev.txt
```

Then, run `pytest` from the project root:

```bash
pytest
```

### Code Style and Linting

The project uses `ruff` for linting and code formatting to ensure a consistent style. Before committing code, it's a good practice to run the linter:

```bash
ruff check .
```

And the formatter:

```bash
ruff format .
```

## Building from Source

The `build.py` script is the entry point for all build-related tasks. It uses `PyInstaller` to package the Python application into a standalone executable and platform-specific tools to create installers.

### Build Commands

-   **Clean previous builds:**
    ```bash
    python build.py clean
    ```
-   **Install all dependencies:**
    ```bash
    python build.py deps
    ```
-   **Build the executable:**
    This creates a standalone executable in the `dist/` directory.
    ```bash
    python build.py build
    ```
-   **Create a distributable package:**
    This creates the platform-specific installer (`.deb`, `.dmg`, or `.exe`) in the `dist/` directory.
    ```bash
    python build.py package
    ```
-   **Perform all steps (clean, deps, build, package):**
    ```bash
    python build.py all
    ```
    For a full release build, you can use the `--release` flag:
    ```bash
    python build.py --release
    ```

## Calendar Integration (Developer Info)

To work with the Google Calendar API during development, you need to acquire your own credentials.

1.  **Go to the Google Cloud Console:** [console.cloud.google.com](https://console.cloud.google.com/)
2.  **Create a new project** or select an existing one.
3.  **Enable the "Google Calendar API"** for your project. You can find it in the API Library.
4.  **Configure the OAuth Consent Screen:**
    -   Choose **"External"** user type.
    -   Fill in the required app information (app name, user support email).
    -   In the "Test users" section, add the Google account email you will be using for testing.
5.  **Create Credentials:**
    -   Go to **Credentials -> Create Credentials -> OAuth client ID**.
    -   Select **"Desktop app"** as the application type.
    -   Give it a name (e.g., "Prayer Player Dev").
6.  **Download JSON:**
    -   After creating the client ID, click the **"Download JSON"** button.
    -   Rename the downloaded file to `google_client_config.json`.
    -   Place this file in the root directory of the project.

The `installer.py` script will automatically copy this file to the correct user data location when you run it. When you first run the application and configure the calendar, Google will prompt you to authorize access for the test user you specified.

## Project Structure

-   `src/`: Main application source code.
    -   `assets/`: Icons, sounds, and other static files.
    -   `auth/`: Google Calendar authentication logic.
    -   `calendar_api/`: Service for interacting with the calendar API.
    -   `config/`: Configuration management (loading, saving, schema).
    -   `gui/`: All PySide6 UI components (windows, widgets).
    -   `platform/`: OS-specific integration code (e.g., systemd services).
    -   `__main__.py`: Main entry point of the application.
-   `tests/`: Pytest test files.
-   `docs/`: Documentation files for the wiki.
-   `build.py`: The main build script.
-   `installer.py`: The developer setup script.
-   `uninstall.py`: The developer uninstallation script.
