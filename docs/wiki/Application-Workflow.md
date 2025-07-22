# Application Workflow

This document outlines the high-level flow and key interactions within the Prayer Player application.

## 1. Application Initialization

-   **Entry Point**: The application starts via `src/__main__.py`.
-   **Event Bus**: An `EventBus` instance is created to act as the central communication hub.
-   **Services**: `ConfigService` and `NotificationService` are initialized and registered with the `EventBus`.
-   **GUI**: The `SettingsWindow` is created, and it registers a handler for `FocusModeRequestedEvent`.
-   **Scheduler**: The `PrayerScheduler` is initialized and registers handlers for `ConfigurationChangedEvent` and `SimulatePrayerCommand`.
-   **Action Executor**: A `DefaultActionExecutor` is created and passed to the `PrayerScheduler`.

## 2. Configuration Management

-   **Loading**: On startup, `SettingsWindow` loads the saved configuration.
-   **Saving**: When the "Save and Close" button is clicked in the `SettingsWindow`:
    1.  A `SaveConfigurationCommand` is dispatched via the `EventBus`.
    2.  The `ConfigService` handles this command, saves the configuration, and publishes a `ConfigurationChangedEvent`.
    3.  The `PrayerScheduler` receives the `ConfigurationChangedEvent` and refreshes its schedule.

## 3. Prayer Time Scheduling

-   **Daily Refresh**: The `PrayerScheduler` refreshes the prayer times daily.
    -   It clears existing jobs.
    -   It fetches new prayer times.
    -   It schedules jobs for each prayer.
-   **Individual Prayer Scheduling**:
    -   For each prayer, it schedules two jobs:
        1.  `action_executor.trigger_focus_mode()`: Scheduled 10 seconds *before* the prayer time.
        2.  `play_adhan_and_duaa()`: Scheduled *at* the prayer time.
    -   If calendar integration is enabled, it also adds an event to the user's calendar.

## 4. Prayer Sequence Execution

-   **Focus Mode**:
    1.  The `action_executor.trigger_focus_mode()` job fires.
    2.  It publishes a `FocusModeRequestedEvent`.
    3.  The `NotificationService` handles the event and displays the `FocusStepsView`.
-   **Adhan and Duaa**:
    1.  The `play_adhan_and_duaa()` job fires.
    2.  It publishes an `AudioPlaybackRequestedEvent`.
    3.  The `NotificationService` handles the event and plays the Adhan and Duaa sounds.

## 5. Google Calendar Integration

-   **Authentication**: The user authenticates their Google account through the `SettingsWindow`.
-   **Event Creation**: The `PrayerScheduler` uses the `GoogleCalendarService` to create events in the user's calendar.

## 6. Prayer Simulation

-   **Trigger**: The user can trigger a prayer simulation from the `SettingsWindow`.
-   **Command**: A `SimulatePrayerCommand` is dispatched via the `EventBus`.
-   **Handling**: The `PrayerScheduler` handles the command and schedules a "dry-run" prayer job.
