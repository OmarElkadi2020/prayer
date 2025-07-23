# Prayer Player Application Workflow

This document outlines the high-level flow and key interactions within the Prayer Player application.

## 1. Application Initialization (`src/__main__.py` and `src/gui/settings_window.py`)

-   **Entry Point**: The application starts via `src/__main__.py` which sets up the core components.
-   **Event Bus**: An `EventBus` instance (`src/shared/event_bus.py`) is created, acting as the central communication hub for different parts of the application.
-   **Configuration Service**: A `ConfigService` (`src/services/config_service.py`) is initialized and registered with the `EventBus` to handle `SaveConfigurationCommand` events, managing application settings.
-   **GUI Initialization**: The `SettingsWindow` (`src/gui/settings_window.py`) is created, taking the `EventBus` as a dependency.
    -   `SettingsWindow` initializes its UI components (tabs, input fields, buttons).
    -   It loads the initial configuration.
    -   It initializes and owns instances of `FocusStepsPresenter` and `FocusStepsView`.
    -   Crucially, `SettingsWindow` registers a handler (`_handle_focus_mode_request`) with the `EventBus` for `FocusModeRequestedEvent`s.
-   **Scheduler Initialization**: The `PrayerScheduler` (`src/scheduler.py`) is initialized, also receiving the `EventBus`.
    -   It registers handlers for `ConfigurationChangedEvent` (to refresh the schedule) and `SimulatePrayerCommand` (to trigger simulations).
-   **Action Executor**: A `DefaultActionExecutor` (`src/actions_executor.py`) is created and passed to the `PrayerScheduler`. This executor publishes events (e.g., `AudioPlaybackRequestedEvent`, `FocusModeRequestedEvent`) when actions are needed.

## 2. Configuration Management

-   **Loading**: On startup, `SettingsWindow` calls `load_config()` (`src/config/security/__init__.py`) to retrieve saved settings.
-   **Saving**: When the "Save and Close" button in `SettingsWindow` is clicked:
    -   The current UI settings are gathered into a `Config` object.
    -   A `SaveConfigurationCommand` is dispatched via the `EventBus`.
    -   The `ConfigService` handles this command, saving the configuration to `config.json`.
    -   The `PrayerScheduler` receives a `ConfigurationChangedEvent` (published by `ConfigService` after saving) and refreshes its schedule based on the new settings.

## 3. Prayer Time Scheduling

-   **Daily Refresh**: The `PrayerScheduler.refresh()` method is called on startup and scheduled to run daily (e.g., at 00:05).
    -   It clears all existing jobs from its `BackgroundScheduler`.
    -   It fetches prayer times for the configured city/country.
    -   It calls `_schedule_day()` to add jobs for each prayer.
-   **Scheduling Individual Prayers (`_schedule_day` and `_schedule_single_prayer_job`)**:
    -   For each upcoming prayer time:
        -   If Google Calendar integration is active, it attempts to add a "busy block" event using `GoogleCalendarService.add_event()`. This involves `find_first_available_slot()` to avoid conflicts and now correctly ignores all-day events.
        -   It schedules two jobs with `apscheduler`:
            -   `action_executor.trigger_focus_mode()`: Scheduled 10 seconds *before* the prayer time.
            -   `play_adhan_and_duaa()`: Scheduled *at* the prayer time.

## 4. Prayer Sequence Execution (Adhan, Focus Steps, Duaa)

-   **Triggering Focus Mode**: When the scheduled `action_executor.trigger_focus_mode()` job fires:
    -   `DefaultActionExecutor.trigger_focus_mode()` publishes a `FocusModeRequestedEvent`.
    -   The `SettingsWindow`'s `_handle_focus_mode_request` method (registered with the `EventBus`) receives this event.
    -   `self.focus_view.show()` is called, making the `FocusStepsView` visible.
-   **Playing Adhan and Duaa**: When the scheduled `play_adhan_and_duaa()` job fires:
    -   It publishes an `ApplicationStateChangedEvent` to `AppState.PRAYER_TIME`.
    -   It calls `action_executor.play_audio()` for `adhan.wav` and `duaa_after_adhan.wav`.
    -   `DefaultActionExecutor.play_audio()` publishes `AudioPlaybackRequestedEvent`s, which are handled by the main application's audio playback logic (likely in `src/__main__.py` or a dedicated audio service, though not explicitly detailed in the provided snippets).
    -   After playback, it publishes `ApplicationStateChangedEvent` to `AppState.IDLE`.

## 5. Google Calendar Integration

-   **Authentication**: The "Authenticate with Google" button in `SettingsWindow` triggers `run_google_auth()`.
    -   A `Worker` thread handles the authentication process using `google_auth.get_google_credentials()`.
    -   If `token.json` is missing, a `CredentialsNotFoundError` is caught, and a `prompt_for_auth` signal is emitted, leading to a `QMessageBox` prompt for the user to re-authenticate.
-   **Event Creation**: As described in section 3, `GoogleCalendarService.add_event()` is called by the scheduler to create busy blocks for prayer times.

## 6. Prayer Simulation Feature

-   **UI Trigger**: In the "Notifications" tab of `SettingsWindow`, selecting a prayer from the dropdown and clicking "Simulate Selected Prayer" triggers `_on_simulate_prayer_clicked`.
-   **Command Dispatch**: `_on_simulate_prayer_clicked` dispatches a `SimulatePrayerCommand` via the `EventBus`.
-   **Scheduler Handling**: The `PrayerScheduler`'s `_handle_simulate_prayer_command` method receives this command.
    -   It schedules a "dry-run" prayer job (focus mode + adhan/duaa) to fire 5 seconds from the current time.
    -   The `is_dry_run=True` flag ensures that `DryRunActionExecutor` is used, which logs actions instead of performing them, and signals a `dry_run_event` when "audio" completes.
    -   A `ScheduleRefreshedEvent` is published to update the UI with simulation status.
