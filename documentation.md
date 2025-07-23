---

## File: `src/services/config_service.py`

**Purpose**: Handles the business logic for loading and saving application configuration.

### Class: `ConfigService`

*   **Description**: A service responsible for managing the application's configuration. It listens for `SaveConfigurationCommand` to save the configuration and publishes `ConfigurationChangedEvent` after a successful save.
*   **Dependencies**: `src.shared.event_bus.EventBus`, `src.config.security.save_config`, `src.domain.config_messages.SaveConfigurationCommand`, `src.domain.config_messages.ConfigurationChangedEvent`, `LOG`

#### `handle_save_command(self, command: SaveConfigurationCommand)`

*   **Description**: Handles the `SaveConfigurationCommand`. It saves the configuration to disk and then publishes a `ConfigurationChangedEvent`.

---

## File: `src/gui/notification_service.py`

**Purpose**: Handles GUI-related notifications and actions, such as playing audio and showing the focus mode window.

### Class: `NotificationService`

*   **Description**: A service within the GUI layer that subscribes to action-request events and performs the corresponding UI actions. This decouples the core application logic from direct GUI manipulation.
*   **Dependencies**: `src.shared.event_bus.EventBus`, `src.domain.notification_messages.AudioPlaybackRequestedEvent`, `src.domain.notification_messages.FocusModeRequestedEvent`, `src.focus_steps_view.FocusStepsView`, `src.presenter.focus_steps_presenter.FocusStepsPresenter`, `PySide6.QtMultimedia.QSoundEffect`, `PySide6.QtCore.QUrl`, `src.config.security.get_asset_path`, `LOG`

#### `handle_audio_playback_request(self, event: AudioPlaybackRequestedEvent)`

*   **Description**: Handles the `AudioPlaybackRequestedEvent` by playing the specified audio file using `QSoundEffect`.

#### `handle_focus_mode_request(self, event: FocusModeRequestedEvent)`

*   **Description**: Handles the `FocusModeRequestedEvent` by displaying the `FocusStepsView`.

---