from __future__ import annotations

import os
import sys
import requests
import threading
import json

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QPushButton, QLineEdit, QRadioButton, QButtonGroup, QMessageBox
)
from PySide6.QtCore import Signal, QObject, Qt, QTimer
from PySide6.QtGui import QStandardItemModel, QStandardItem

# Add the project root to the Python path
# Assuming this script is in the project root
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.prayer import config
from src.prayer.auth import google_auth
from src.prayer.platform.service import ServiceManager

class Worker(QObject):
    """Worker object for running tasks in a separate thread."""
    finished = Signal()
    error = Signal(str)
    countries_loaded = Signal(list)
    cities_loaded = Signal(list, str)
    status_updated = Signal(str, str)

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
            countries = sorted([country["country"] for country in data["data"]])
            self.countries_loaded.emit(countries)
            self.status_updated.emit("Countries loaded. Please select a country.", "green")
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

    def authenticate_google_calendar(self):
        self.status_updated.emit("Attempting Google Calendar authentication...", "blue")
        try:
            google_auth.get_google_credentials(reauthenticate=True)
            self.status_updated.emit("Google Calendar authentication successful!", "green")
        except Exception as e:
            self.status_updated.emit(f"Google Calendar authentication failed: {e}", "red")
            self.error.emit(f"Failed to authenticate Google Calendar: {e}")
        self.finished.emit()

class SetupGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Prayer Player Setup")
        self.setFixedSize(450, 400) # Fixed size for simplicity, adjust as needed

        self.countries = []
        self.cities = []

        self.service_manager = ServiceManager(
            service_name="prayer-player",
            service_display_name="Prayer Player",
            service_description="A service to play prayer times."
        )

        self.init_ui()
        self.load_initial_config()
        self.load_countries()

    def init_ui(self):
        layout = QGridLayout()
        self.setLayout(layout)

        # Country Selection
        layout.addWidget(QLabel("Country:"), 0, 0)
        self.country_combo = QComboBox()
        self.country_combo.setEditable(True)
        self.country_combo.currentIndexChanged.connect(self.on_country_select)
        self.country_combo.lineEdit().textEdited.connect(self.filter_country_dropdown)
        layout.addWidget(self.country_combo, 0, 1)

        # City Selection
        layout.addWidget(QLabel("City:"), 1, 0)
        self.city_combo = QComboBox()
        self.city_combo.setEditable(True)
        self.city_combo.setEnabled(False) # Disable until country is selected
        self.city_combo.lineEdit().textEdited.connect(self.filter_city_dropdown)
        layout.addWidget(self.city_combo, 1, 1)

        # Save Button
        self.save_button = QPushButton("Save Configuration")
        self.save_button.clicked.connect(self.save_configuration)
        layout.addWidget(self.save_button, 2, 0, 1, 2) # Span two columns

        # Google Calendar Authentication
        layout.addWidget(QLabel("Google Calendar Setup:"), 3, 0)
        self.auth_button = QPushButton("Authenticate Google Calendar")
        self.auth_button.clicked.connect(self.authenticate_google_calendar)
        layout.addWidget(self.auth_button, 3, 1)

        # Status Label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: blue;")
        layout.addWidget(self.status_label, 4, 0, 1, 2)

        # Run Mode Selection
        layout.addWidget(QLabel("Run Mode:"), 5, 0)
        run_mode_layout = QVBoxLayout()
        self.run_mode_group = QButtonGroup(self)

        self.background_radio = QRadioButton("Run in background (recommended)")
        self.background_radio.setChecked(True) # Default
        self.run_mode_group.addButton(self.background_radio)
        run_mode_layout.addWidget(self.background_radio)

        self.foreground_radio = QRadioButton("Run in foreground (for testing)")
        self.run_mode_group.addButton(self.foreground_radio)
        run_mode_layout.addWidget(self.foreground_radio)

        layout.addLayout(run_mode_layout, 5, 1, 2, 1) # Span two rows, one column

        # Finish Button
        self.finish_button = QPushButton("Finish Setup")
        self.finish_button.clicked.connect(self.finish_setup)
        layout.addWidget(self.finish_button, 8, 0, 1, 2)

        # Add a "Run at Startup" checkbox
        self.startup_checkbox = QCheckBox("Run at startup")
        self.startup_checkbox.setChecked(False) # Default to off
        layout.addWidget(self.startup_checkbox, 6, 1)

        # Adjust column stretch to make the second column expand
        layout.setColumnStretch(1, 1)

    def update_status(self, message: str, color: str = "blue"):
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color};")

    def load_initial_config(self):
        current_config = config.load_config()
        self.country_combo.setEditText(current_config.get('country', ''))
        self.city_combo.setEditText(current_config.get('city', ''))
        if current_config.get('run_mode', 'background') == "foreground":
            self.foreground_radio.setChecked(True)
        else:
            self.background_radio.setChecked(True)
        self.update_status("Configuration loaded.")

    def load_countries(self):
        self.worker = Worker()
        self.thread = threading.Thread(target=self.worker.load_countries, daemon=True)
        self.worker.countries_loaded.connect(self._on_countries_loaded)
        self.worker.status_updated.connect(self.update_status)
        self.worker.error.connect(lambda msg: QMessageBox.showerror("API Error", msg))
        self.thread.start()

    def _on_countries_loaded(self, countries):
        self.countries = countries
        self.country_combo.clear()
        self.country_combo.addItems(self.countries)
        self.country_combo.setEnabled(True)
        # If a country was loaded from config, trigger city loading
        if self.country_combo.currentText() in self.countries:
            self.on_country_select()

    def filter_country_dropdown(self, text):
        self.country_combo.clear()
        filtered_countries = [c for c in self.countries if text.lower() in c.lower()]
        self.country_combo.addItems(filtered_countries)
        self.country_combo.setEditText(text) # Keep the typed text
        self.country_combo.showPopup() # Show dropdown immediately

    def on_country_select(self):
        selected_country = self.country_combo.currentText()
        self.city_combo.clear()
        self.city_combo.setEnabled(False)
        if selected_country:
            self.worker = Worker()
            self.thread = threading.Thread(target=self.worker.load_cities, args=(selected_country,), daemon=True)
            self.worker.cities_loaded.connect(self._on_cities_loaded)
            self.worker.status_updated.connect(self.update_status)
            self.worker.error.connect(lambda msg: QMessageBox.showerror("API Error", msg))
            self.thread.start()

    def _on_cities_loaded(self, cities, country):
        self.cities = cities
        self.city_combo.clear()
        self.city_combo.addItems(self.cities)
        self.city_combo.setEnabled(True)
        # Set city from config if available
        current_config = config.load_config()
        if current_config.get('country') == country and current_config.get('city') in self.cities:
            self.city_combo.setEditText(current_config.get('city'))

    def filter_city_dropdown(self, text):
        self.city_combo.clear()
        filtered_cities = [c for c in self.cities if text.lower() in c.lower()]
        self.city_combo.addItems(filtered_cities)
        self.city_combo.setEditText(text) # Keep the typed text
        self.city_combo.showPopup() # Show dropdown immediately

    def save_configuration(self):
        city = self.city_combo.currentText().strip()
        country = self.country_combo.currentText().strip()
        run_mode = "background" if self.background_radio.isChecked() else "foreground"

        if not city or not country:
            QMessageBox.warning(self, "Input Error", "Country and City must be selected.")
            return

        try:
            config.save_config(city, country, run_mode)
            self.update_status("Configuration saved successfully!", "green")
        except Exception as e:
            self.update_status(f"Error saving config: {e}", "red")
            QMessageBox.showerror(self, "Save Error", f"Failed to save configuration: {e}")

    def authenticate_google_calendar(self):
        self.worker = Worker()
        self.thread = threading.Thread(target=self.worker.authenticate_google_calendar, daemon=True)
        self.worker.status_updated.connect(self.update_status)
        self.worker.error.connect(lambda msg: QMessageBox.showerror("Authentication Error", msg))
        self.thread.start()

    def finish_setup(self):
        self.save_configuration()
        if "successfully" in self.status_label.text():
            try:
                if self.startup_checkbox.isChecked():
                    self.service_manager.install()
                    self.service_manager.enable()
                    self.update_status("Service installed and enabled.", "green")
                else:
                    self.service_manager.uninstall()
                    self.update_status("Service uninstalled.", "green")
                
                QMessageBox.information(self, "Setup Complete", "Configuration saved. You can now close this window.")
                self.close()
            except Exception as e:
                self.update_status(f"Error managing service: {e}", "red")
                QMessageBox.showerror(self, "Service Error", f"Failed to manage service: {e}")
        else:
            QMessageBox.warning(self, "Setup Incomplete", "Please save the configuration before finishing.")

def main():
    app = QApplication(sys.argv)
    gui = SetupGUI()
    gui.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
