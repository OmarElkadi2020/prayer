# Event-Driven Architecture

The Prayer Player application uses an event-driven architecture to decouple its components. This is achieved through an **Event Bus**, which acts as a central messaging system. Components can publish events to the bus, and other components can subscribe to those events and react accordingly.

This approach allows for a modular and extensible system where components don't need to have direct knowledge of each other.

## Key Events

Here are some of the key events used in the application:

-   **`SaveConfigurationCommand`**: Dispatched when the user saves the settings.
    -   **Published by**: `SettingsWindow`
    -   **Handled by**: `ConfigService`

-   **`ConfigurationChangedEvent`**: Published after the configuration has been successfully saved.
    -   **Published by**: `ConfigService`
    -   **Handled by**: `PrayerScheduler`

-   **`SimulatePrayerCommand`**: Dispatched when the user wants to simulate a prayer.
    -   **Published by**: `SettingsWindow`
    -   **Handled by**: `PrayerScheduler`

-   **`FocusModeRequestedEvent`**: Published when it's time to trigger the focus mode.
    -   **Published by**: `DefaultActionExecutor`
    -   **Handled by**: `NotificationService`

-   **`AudioPlaybackRequestedEvent`**: Published when it's time to play an audio file.
    -   **Published by**: `DefaultActionExecutor`
    -   **Handled by**: `NotificationService`

-   **`ApplicationStateChangedEvent`**: Published when the application's state changes (e.g., from `IDLE` to `PRAYER_TIME`).
    -   **Published by**: `PrayerScheduler`
    -   **Handled by**: `TrayIcon`

-   **`ScheduleRefreshedEvent`**: Published after the prayer schedule has been refreshed.
    -   **Published by**: `PrayerScheduler`
    -   **Handled by**: `TrayIcon`
