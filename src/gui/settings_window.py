from __future__ import annotations

import os
import sys
import requests
import threading

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QMessageBox, QCheckBox,
    QTabWidget, QFileDialog, QFrame
)
from PySide6.QtCore import Signal, QObject

from src.config.security import load_config, adhan_path, LOG
from src.auth import google_auth
from src.shared.event_bus import EventBus
from src.platform.service import ServiceManager
from src.shared.audio_player import play
from src.domain.notification_messages import FocusModeRequestedEvent
from src.focus_steps_view import FocusStepsView
from src.presenter.focus_steps_presenter import FocusStepsPresenter

class Worker(QObject):
    """Worker object for running tasks in a separate thread."""
    finished = Signal()
    error = Signal(str)
    countries_loaded = Signal(list)
    cities_loaded = Signal(list, str)
    status_updated = Signal(str, str)
    google_auth_finished = Signal(object) # Pass credentials object
    prompt_for_auth = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def _fetch_data(self, url, params=None):
        try:
            response = requests.post(url, json=params) if params else requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.status_updated.emit(f"API Error: {e}", "red")
            self.error.emit(f"Failed to fetch data: {e}")
            return None

    def load_countries(self):
        self.status_updated.emit("Loading countries...", "blue")
        data = self._fetch_data("https://countriesnow.space/api/v0.1/countries")
        if data and not data.get("error"):
            countries = sorted([c["country"] for c in data["data"]])
            self.countries_loaded.emit(countries)
            self.status_updated.emit("Countries loaded.", "green")
        else:
            self.status_updated.emit("Failed to load countries.", "red")
        self.finished.emit()

    def load_cities(self, country):
        self.status_updated.emit(f"Loading cities for {country}...", "blue")
        data = self._fetch_data("https://countriesnow.space/api/v0.1/countries/cities", {"country": country})
        if data and not data.get("error"):
            cities = sorted(data["data"])
            self.cities_loaded.emit(cities, country)
            self.status_updated.emit(f"Cities for {country} loaded.", "green")
        else:
            self.status_updated.emit(f"Failed to load cities for {country}.", "red")
        self.finished.emit()

    def authenticate_google_calendar(self, reauthenticate=False):
        self.status_updated.emit("Attempting Google Calendar authentication...", "blue")
        try:
            creds = google_auth.get_google_credentials(reauthenticate=reauthenticate)
            self.google_auth_finished.emit(creds)
            if creds:
                self.status_updated.emit("Google authentication successful!", "green")
        except google_auth.CredentialsNotFoundError as e:
            self.status_updated.emit(f"Google authentication failed: {e}", "red")
            self.prompt_for_auth.emit()
        except Exception as e:
            self.status_updated.emit(f"Google authentication failed: {e}", "red")
            self.error.emit(f"Failed to authenticate Google Calendar: {e}")
        self.finished.emit()

class SettingsWindow(QWidget):
    def __init__(self, event_bus: EventBus):
        super().__init__()
        self.event_bus = event_bus
        self.setWindowTitle("Prayer Player Settings")
        self.setMinimumSize(550, 650)
        self.countries = []
        self.cities = []
        self.service_manager = ServiceManager("prayer-player", "Prayer Player", "A service to play prayer times.")
        self.calendar_service = None

        # Initialize FocusStepsView and Presenter
        self.focus_presenter = FocusStepsPresenter()
        self.focus_view = FocusStepsView(self.focus_presenter, disable_sound=True)

        self.init_ui()
        self.load_initial_config()
        self.load_countries()
        self.check_initial_auth_status()

        # Register event handler for focus mode
        self.event_bus.register(FocusModeRequestedEvent, self._handle_focus_mode_request)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        # Create tabs
        self.general_tab = QWidget()
        self.notifications_tab = QWidget()
        self.about_tab = QWidget()

        tab_widget.addTab(self.general_tab, "General")
        tab_widget.addTab(self.notifications_tab, "Notifications")
        tab_widget.addTab(self.about_tab, "About")

        # Populate tabs
        self.init_general_tab()
        self.init_notifications_tab()
        self.init_about_tab()

        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)
        self.save_button = QPushButton("Save and Close")
        self.save_button.clicked.connect(self.save_and_close)
        main_layout.addWidget(self.save_button)

    def init_general_tab(self):
        layout = QGridLayout(self.general_tab)
        
        # --- Location Settings ---
        layout.addWidget(QLabel("<b>Location</b>"), 0, 0, 1, 2)
        layout.addWidget(QLabel("Country:"), 1, 0)
        self.country_combo = QComboBox()
        self.country_combo.setEditable(True)
        self.country_combo.currentIndexChanged.connect(self.on_country_select)
        layout.addWidget(self.country_combo, 1, 1)
        
        layout.addWidget(QLabel("City:"), 2, 0)
        self.city_combo = QComboBox()
        self.city_combo.setEditable(True)
        self.city_combo.setEnabled(False)
        layout.addWidget(self.city_combo, 2, 1)

        # --- Prayer Times Settings ---
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line1, 3, 0, 1, 2)
        
        layout.addWidget(QLabel("<b>Prayer Time Calculation</b>"), 4, 0, 1, 2)
        layout.addWidget(QLabel("Calculation Method:"), 5, 0)
        self.method_combo = QComboBox()
        methods = {
            "Muslim World League": 3, "Islamic Society of North America (ISNA)": 2,
            "Egyptian General Authority of Survey": 5, "Umm Al-Qura University, Makkah": 4,
            "University of Islamic Sciences, Karachi": 1, "Institute of Geophysics, University of Tehran": 7,
            "Shia Ithna-Ashari, Leva Institute, Qum": 8, "Gulf Region": 9, "Kuwait": 10,
            "Qatar": 11, "Majlis Ugama Islam Singapura, Singapore": 12,
            "Union Organization Islamic de France": 13, "Diyanet İşleri Başkanlığı, Turkey": 14,
            "Spiritual Administration of Muslims of Russia": 15
        }
        for name, number in methods.items():
            self.method_combo.addItem(name, userData=number)
        layout.addWidget(self.method_combo, 5, 1)
        
        layout.addWidget(QLabel("Asr Juristic Method:"), 6, 0)
        self.school_combo = QComboBox()
        self.school_combo.addItem("Shafii (Standard)", userData=0)
        self.school_combo.addItem("Hanafi", userData=1)
        layout.addWidget(self.school_combo, 6, 1)

        # --- Calendar Settings ---
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line2, 7, 0, 1, 2)
        
        layout.addWidget(QLabel("<b>Google Calendar Integration</b>"), 8, 0, 1, 2)
        self.auth_button = QPushButton("(Re)Authenticate with Google")
        self.auth_button.clicked.connect(lambda: self.run_google_auth(reauthenticate=True))
        layout.addWidget(self.auth_button, 9, 0, 1, 2)
        
        layout.addWidget(QLabel("Authentication Status:"), 10, 0)
        self.google_user_label = QLabel("Not authenticated.")
        layout.addWidget(self.google_user_label, 10, 1)
        
        layout.addWidget(QLabel("Select Calendar:"), 11, 0)
        self.calendar_combo = QComboBox()
        self.calendar_combo.setEnabled(False)
        layout.addWidget(self.calendar_combo, 11, 1)

        # --- System Settings ---
        line3 = QFrame()
        line3.setFrameShape(QFrame.HLine)
        line3.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line3, 12, 0, 1, 2)
        
        layout.addWidget(QLabel("<b>System</b>"), 13, 0, 1, 2)
        self.startup_checkbox = QCheckBox("Run at system startup")
        layout.addWidget(self.startup_checkbox, 14, 0, 1, 2)
        
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(15, 1)

    def init_notifications_tab(self):
        layout = QGridLayout(self.notifications_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(QLabel("Play Adhan for:"), 0, 0, 1, 2)
        self.prayer_checkboxes = {}
        prayers = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
        for i, prayer in enumerate(prayers):
            self.prayer_checkboxes[prayer] = QCheckBox(prayer)
            layout.addWidget(self.prayer_checkboxes[prayer], i + 1, 0)
        
        custom_audio_layout = QHBoxLayout()
        self.custom_audio_button = QPushButton("Select Custom Adhan Sound")
        self.custom_audio_button.clicked.connect(self.select_custom_audio)
        self.test_audio_button = QPushButton("Test")
        self.test_audio_button.clicked.connect(self.test_audio)
        custom_audio_layout.addWidget(self.custom_audio_button)
        custom_audio_layout.addWidget(self.test_audio_button)
        layout.addLayout(custom_audio_layout, len(prayers) + 1, 0, 1, 2)
        
        self.custom_audio_label = QLabel("Using default adhan sound.")
        layout.addWidget(self.custom_audio_label, len(prayers) + 2, 0, 1, 2)

        # --- Simulate Prayer Section ---
        simulate_line = QFrame()
        simulate_line.setFrameShape(QFrame.HLine)
        simulate_line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(simulate_line, len(prayers) + 3, 0, 1, 2)

        layout.addWidget(QLabel("<b>Simulate Prayer</b>"), len(prayers) + 4, 0, 1, 2)
        
        self.simulate_prayer_combo = QComboBox()
        self.simulate_prayer_combo.addItems(prayers)
        layout.addWidget(self.simulate_prayer_combo, len(prayers) + 5, 0)

        self.simulate_prayer_button = QPushButton("Simulate Selected Prayer")
        self.simulate_prayer_button.clicked.connect(self._on_simulate_prayer_clicked)
        layout.addWidget(self.simulate_prayer_button, len(prayers) + 5, 1)

        layout.setRowStretch(len(prayers) + 6, 1)

    def init_about_tab(self):
        layout = QGridLayout(self.about_tab)
        
        title = QLabel("<b>Prayer Player v1.0</b>")
        layout.addWidget(title, 0, 0)

        app_target_label = QLabel(
            "This application is designed to help busy professionals maintain their daily prayers.<br>"
            "It automates prayer time organization and helps you stay on track."
        )
        app_target_label.setWordWrap(True)
        layout.addWidget(app_target_label, 1, 0)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line, 2, 0)

        features_title = QLabel("<b>Key Features:</b>")
        layout.addWidget(features_title, 3, 0)

        calendar_desc = QLabel(
            "<b>Smart Slot Finder:</b> The app can automatically finds a free slot after start of each prayer time window and reserve it."
            "ensuring your prayer is scheduled around your existing commitments."
            "<b>Calendar Integration:</b> Automatically blocks out prayer times in your Google Calendar. "
            "This prevents colleagues from scheduling meetings during your prayers, helping you reserve that time.<br>"
        )
        calendar_desc.setWordWrap(True)
        layout.addWidget(calendar_desc, 4, 0)

        focus_desc = QLabel(
            "<b>Focus Mode Reminders:</b> At each prayer time, a simple, non-intrusive window appears to "
            "remind you it's time to pray, helping you transition from work to worship."
        )
        focus_desc.setWordWrap(True)
        layout.addWidget(focus_desc, 5, 0)

        link_label = QLabel("<a href='https://github.com/OmarElkadi2020/prayer/'>Visit on GitHub</a>")
        link_label.setOpenExternalLinks(True)
        layout.addWidget(link_label, 6, 0)

        # --- Log Level Setting ---
        log_level_line = QFrame()
        log_level_line.setFrameShape(QFrame.HLine)
        log_level_line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(log_level_line, 7, 0, 1, 2)

        layout.addWidget(QLabel("<b>Logging</b>"), 8, 0, 1, 2)
        layout.addWidget(QLabel("Log Level:"), 9, 0)
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        layout.addWidget(self.log_level_combo, 9, 1)
        
        layout.setRowStretch(10, 1)
        layout.setColumnStretch(0, 1)

    def select_custom_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Adhan Sound", "", "Audio Files (*.wav *.mp3)")
        if file_path:
            self.custom_audio_label.setText(os.path.basename(file_path))
            self.custom_audio_path = file_path
            self.update_status("Custom adhan sound selected.", "green")

    def test_audio(self):
        audio_path = getattr(self, 'custom_audio_path', adhan_path())
        if audio_path and os.path.exists(audio_path):
            self.update_status(f"Testing sound: {os.path.basename(audio_path)}", "blue")
            play(audio_path)
        else:
            self.update_status("Audio file not found.", "red")

    def _on_simulate_prayer_clicked(self):
        selected_prayer = self.simulate_prayer_combo.currentText()
        if selected_prayer:
            self.update_status(f"Simulating {selected_prayer} prayer...", "blue")
            from src.shared.commands import SimulatePrayerCommand
            self.event_bus.dispatch(SimulatePrayerCommand(prayer_name=selected_prayer))
        else:
            self.update_status("Please select a prayer to simulate.", "red")

    def update_status(self, message: str, color: str = "blue"):
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color};")

    def load_initial_config(self):
        current_config = load_config()
        self.country_combo.setEditText(current_config.country or '')
        self.city_combo.setEditText(current_config.city or '')
        method_index = self.method_combo.findData(current_config.method)
        self.method_combo.setCurrentIndex(method_index if method_index != -1 else 0)
        school_index = self.school_combo.findData(current_config.school)
        self.school_combo.setCurrentIndex(school_index if school_index != -1 else 0)
        
        for name, checkbox in self.prayer_checkboxes.items():
            checkbox.setChecked(name in current_config.enabled_prayers)
            
        self.custom_audio_path = current_config.custom_audio_path
        if self.custom_audio_path:
            self.custom_audio_label.setText(os.path.basename(self.custom_audio_path))
            
        self.startup_checkbox.setChecked(self.service_manager.is_enabled())
        
        self.log_level_combo.setCurrentText(current_config.log_level)
        self.update_status("Configuration loaded.")

    def save_and_close(self):
        current_config = load_config()
        
        current_config.country = self.country_combo.currentText().strip()
        current_config.city = self.city_combo.currentText().strip()
        current_config.method = self.method_combo.currentData()
        current_config.school = self.school_combo.currentData()
        current_config.enabled_prayers = [name for name, cb in self.prayer_checkboxes.items() if cb.isChecked()]
        current_config.custom_audio_path = getattr(self, 'custom_audio_path', None)
        current_config.google_calendar_id = self.calendar_combo.currentData()
        current_config.log_level = self.log_level_combo.currentText()

        if not current_config.city or not current_config.country:
            QMessageBox.warning(self, "Input Error", "Country and City must be selected.")
            return
            
        try:
            from src.domain.config_messages import SaveConfigurationCommand
            self.event_bus.dispatch(SaveConfigurationCommand(config=current_config))

            LOG.setLevel(current_config.log_level)
            self.update_status("Configuration saved successfully!", "green")
            
            if self.startup_checkbox.isChecked() != self.service_manager.is_enabled():
                if self.startup_checkbox.isChecked():
                    self.service_manager.install()
                    self.service_manager.enable()
                else:
                    self.service_manager.disable()
                    self.service_manager.uninstall()
            
            self.close()
        except Exception as e:
            self.update_status(f"Error saving config: {e}", "red")
            QMessageBox.critical(self, "Save Error", f"Failed to save configuration: {e}")

    def load_countries(self):
        self.worker = Worker()
        self.thread = threading.Thread(target=self.worker.load_countries, daemon=True)
        self.worker.countries_loaded.connect(self._on_countries_loaded)
        self.worker.status_updated.connect(self.update_status)
        self.worker.error.connect(lambda msg: QMessageBox.critical(self, "API Error", msg))
        self.thread.start()

    def _on_countries_loaded(self, countries):
        self.countries = countries
        self.country_combo.addItems(self.countries)
        current_config = load_config()
        if current_config.country in self.countries:
            self.country_combo.setCurrentText(current_config.country)
            self.on_country_select()

    def on_country_select(self):
        selected_country = self.country_combo.currentText()
        if selected_country:
            self.worker = Worker()
            self.thread = threading.Thread(target=self.worker.load_cities, args=(selected_country,), daemon=True)
            self.worker.cities_loaded.connect(self._on_cities_loaded)
            self.worker.status_updated.connect(self.update_status)
            self.worker.error.connect(lambda msg: QMessageBox.critical(self, "API Error", msg))
            self.thread.start()

    def _on_cities_loaded(self, cities, country):
        self.cities = cities
        self.city_combo.clear()
        self.city_combo.addItems(self.cities)
        self.city_combo.setEnabled(True)
        current_config = load_config()
        if current_config.country == country:
            self.city_combo.setCurrentText(current_config.city or '')

    def check_initial_auth_status(self):
        self.run_google_auth(reauthenticate=False)

    def run_google_auth(self, reauthenticate=False):
        self.worker = Worker()
        self.thread = threading.Thread(target=self.worker.authenticate_google_calendar, args=(reauthenticate,), daemon=True)
        self.worker.google_auth_finished.connect(self.on_google_auth_finished)
        self.worker.status_updated.connect(self.update_status)
        self.worker.error.connect(lambda msg: QMessageBox.critical(self, "Authentication Error", msg))
        self.worker.prompt_for_auth.connect(self.handle_google_auth_prompt)
        self.thread.start()

    def handle_google_auth_prompt(self):
        reply = QMessageBox.question(
            self,
            "Calendar Integration",
            "Google Calendar integration is not set up. This feature allows the app to automatically "
            "block out prayer times in your Google Calendar, helping you reserve that time and "
            "preventing meeting conflicts.\n\nWould you like to set it up now?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.run_google_auth(reauthenticate=True)
        else:
            self.update_status("Google authentication setup declined.", "red")

    def on_google_auth_finished(self, creds):
        if not creds:
            self.google_user_label.setText("Authentication failed.")
            self.calendar_combo.clear()
            self.calendar_combo.setEnabled(False)
            return

        from src.calendar_api.google_calendar import GoogleCalendarService
        self.calendar_service = GoogleCalendarService(creds)
        self.update_status("Google Calendar service initialized.", "green")

        user_info = google_auth.get_user_info(creds)
        self.google_user_label.setText(f"Authenticated as: {user_info.get('email', 'Unknown')}")
        
        calendars = google_auth.get_calendar_list(creds)
        self.calendar_combo.clear()
        for cal in calendars:
            self.calendar_combo.addItem(cal['summary'], userData=cal['id'])
        self.calendar_combo.setEnabled(True)

        current_config = load_config()
        if current_config.google_calendar_id:
            index = self.calendar_combo.findData(current_config.google_calendar_id)
            if index != -1:
                self.calendar_combo.setCurrentIndex(index)

    def _handle_focus_mode_request(self, event: FocusModeRequestedEvent):
        LOG.info("Received FocusModeRequestedEvent. Showing FocusStepsView.")
        # Ensure the view is shown on the Qt thread
        self.focus_view.show()
        self.focus_view.activateWindow()

def main(app: QApplication | None = None):
    if app is None:
        app = QApplication.instance() or QApplication(sys.argv)
    
    # For standalone execution, we need to set up a minimal event system.
    from src.shared.event_bus import EventBus
    from src.services.config_service import ConfigService
    from src.domain.config_messages import SaveConfigurationCommand

    event_bus = EventBus()
    config_service = ConfigService(event_bus)
    event_bus.register(SaveConfigurationCommand, config_service.handle_save_command)

    gui = SettingsWindow(event_bus)
    gui.show()
    
    if app.exec() != 0:
        LOG.error("Application exited with an error.")
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
