#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
نافذة «تهيئة الخشوع» التفاعلية (نسخة مُحسَّنة)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
• تطبيق إرشادي للمساعدة على تهيئة النفس للخشوع في الصلاة.
• يتكوّن من ثـماني مراحل: من ختم المهمّة وحتى المكافأة بعد الصلاة.
• لكل مرحلة عنوان واضح وشرح عملي مختصر ومُلهم.
• تصميم عصري وداكن مع دعم كامل للغة العربية (من اليمين لليسار).
• يتكيف حجم النافذة تلقائيًا مع طول النص في كل خطوة.
"""

import sys
from importlib import resources
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QFont, QIcon, QGuiApplication
from PySide6.QtMultimedia import QSoundEffect
from src.presenter.focus_steps_presenter import FocusStepsPresenter
from src.config.security import LOG

# --- Configuration Constants ---
# Using constants for better maintainability and clarity.
APP_TITLE = "تهيئة الخشوع"
WINDOW_WIDTH = 400
FONT_FAMILY = "Noto Sans Arabic"

def get_asset_path(package, resource):
    """
    Safely retrieves the path to a resource file within a package.
    Returns an empty string if the file is not found.
    """
    try:
        with resources.path(package, resource) as p:
            return str(p)
    except (FileNotFoundError, ModuleNotFoundError):
        LOG.warning(f"Asset '{resource}' not found in package '{package}'.")
        return ""

# --- Constants ---
SOUND_PATH = get_asset_path('assets', 'complete_sound.wav')
ICON_PATH = get_asset_path('assets', 'mosque.png')

# ==================================================================
# ❷ Main Application Window
# ==================================================================

class FocusStepsView(QWidget):
    """
    The main window for the application. It displays steps sequentially
    and handles user navigation. The window resizes to fit its content.
    """
    def __init__(self, presenter: FocusStepsPresenter, disable_sound: bool = False):
        super().__init__()
        
        # --- State Management ---
        self.presenter = presenter
        self.presenter.attach_view(self)
        self.disable_sound = disable_sound

        # --- Window Configuration ---
        self.setWindowTitle(APP_TITLE)
        if ICON_PATH:
            self.setWindowIcon(QIcon(str(ICON_PATH)))
        
        # --- Dynamic Sizing Setup ---
        self.setMinimumWidth(WINDOW_WIDTH)
        # Set max height to prevent window from becoming excessively tall
        max_height = QGuiApplication.primaryScreen().availableGeometry().height() * 0.9
        self.setMaximumHeight(int(max_height))
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)

        self.setLayoutDirection(Qt.RightToLeft) # Set layout direction for the whole window
        
        # --- Initial Setup ---
        self.setup_stylesheet()
        self.setup_ui_components()
        self.setup_layouts()
        self.setup_connections()
        self.setup_sound_effect()
        self.presenter._notify_view_update() # Notify presenter that view is ready

    def setup_stylesheet(self):
        """Sets the global QSS stylesheet for the application."""
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: #1a1a1a;
                border-radius: 18px;
                border: 1px solid #333333;
                font-family: "{FONT_FAMILY}", "Segoe UI", "Arial", sans-serif;
                color: #ffffff;
            }}
            QLabel#stepTitle {{
                font-size: 26px;
                font-weight: bold;
                padding-bottom: 10px;
            }}
            QLabel#sectionTitle {{
                color: #e0e0e0;
                font-size: 18px;
                font-weight: bold;
                margin-top: 15px;
            }}
            QLabel#sectionContent {{
                font-size: 16px;
                margin-bottom: 10px;
                padding-right: 15px; /* Indent content for clarity */
            }}
            QPushButton {{
                color: #ffffff;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3a3a3a, stop:1 #5a5a5a);
                border: none;
                border-radius: 18px;
                padding: 12px 30px;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4a4a4a, stop:1 #6a6a6a);
            }}
            QPushButton:pressed {{ background: #2a2a2a; }}
            QPushButton#navButton {{
                background: #2a2a2a;
                border: 1px solid #555555;
                border-radius: 12px;
                padding: 5px 15px;
                font-size: 14px;
                font-weight: normal;
            }}
            QPushButton#navButton:hover {{ background: #3a3a3a; }}
            QPushButton#navButton:pressed {{ background: #1a1a1a; }}
            QPushButton:disabled {{
                background-color: #404040;
                color: #888888;
            }}
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                border: none;
                background: #2a2a2a;
                width: 10px;
                margin: 0px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: #555555;
                min-height: 20px;
                border-radius: 5px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            """
        )

    def setup_ui_components(self):
        """Initializes all UI widgets."""
        # --- Main Title ---
        self.title_lbl = QLabel("", objectName="stepTitle")
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setWordWrap(True)

        # --- Scrollable Content Area ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignTop)
        self.content_layout.setContentsMargins(0, 0, 10, 0) # Margin on the left (due to RTL) for scrollbar
        self.scroll_area.setWidget(self.content_widget)

        # --- Navigation Controls ---
        self.prev_btn = QPushButton("السابق", objectName="navButton")
        self.next_btn = QPushButton("التالي", objectName="navButton")
        self.step_counter_lbl = QLabel("", alignment=Qt.AlignCenter)
        
        # --- Main Action Button ---
        self.action_btn = QPushButton("تم")
        self.action_btn.setCursor(Qt.PointingHandCursor)
        self.action_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def setup_layouts(self):
        """Arranges UI widgets into layouts."""
        # --- Navigation Layout ---
        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self.next_btn)
        nav_layout.addWidget(self.step_counter_lbl, 1) # Add stretch factor
        nav_layout.addWidget(self.prev_btn)

        # --- Main Layout ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(15)
        
        main_layout.addWidget(self.title_lbl)
        main_layout.addWidget(self.scroll_area, 1) # Content area takes available space
        main_layout.addLayout(nav_layout)
        main_layout.addWidget(self.action_btn)

    def setup_connections(self):
        """Connects widget signals to appropriate slots."""
        self.action_btn.clicked.connect(self.presenter.handle_action)
        self.next_btn.clicked.connect(self.presenter.go_to_next_step)
        self.prev_btn.clicked.connect(self.presenter.go_to_previous_step)

    def setup_sound_effect(self):
        """Initializes the sound effect player."""
        self.sound_effect = QSoundEffect()
        if SOUND_PATH:
            self.sound_effect.setSource(QUrl.fromLocalFile(SOUND_PATH))
            self.sound_effect.setVolume(0.7)

    def display_step_content(self, title: str, parsed_description: list[tuple[str, str]]):
        """Updates the UI with the current step's title and parsed description."""
        self.title_lbl.setText(title)
        # Clear previous content
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for item_type, content in parsed_description:
            if item_type == 'title':
                label = QLabel(content, objectName="sectionTitle")
                if "الفائدة الروحية" in content:
                    label.setStyleSheet("margin-top: 10px; font-size: 16px;")
                self.content_layout.addWidget(label)
            elif item_type == 'content':
                content_lbl = QLabel(content, objectName="sectionContent")
                content_lbl.setWordWrap(True)
                self.content_layout.addWidget(content_lbl)
        self.adjust_window_size()

    def set_navigation_state(self, prev_enabled: bool, next_enabled: bool, step_counter_text: str, action_button_text: str):
        """Updates the navigation controls' state and visibility."""
        self.prev_btn.setVisible(True) # Always visible, enabled/disabled by presenter
        self.next_btn.setVisible(True) # Always visible, enabled/disabled by presenter
        self.step_counter_lbl.setVisible(True) # Always visible

        self.step_counter_lbl.setText(step_counter_text)
        self.action_btn.setText(action_button_text)

        self.prev_btn.setEnabled(prev_enabled)
        self.next_btn.setEnabled(next_enabled)

    def adjust_window_size(self):
        """Adjusts the window size to fit the content."""
        content_height = self.content_widget.sizeHint().height()
        MIN_SCROLL_AREA_HEIGHT = 100
        self.scroll_area.setMinimumHeight(max(content_height, MIN_SCROLL_AREA_HEIGHT))
        self.adjustSize()

    def play_completion_sound(self):
        """Plays the completion sound if available."""
        if not self.disable_sound and SOUND_PATH and self.sound_effect.isLoaded():
            self.sound_effect.play()

    def close_view(self):
        """Closes the window."""
        self.close()


# ==================================================================
# ❸ Application Entry Point
# ==================================================================
def run(is_modal: bool = True):
    """
    Initializes and runs the QApplication.
    If is_modal is True, it runs the window in a blocking way.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app.setLayoutDirection(Qt.RightToLeft)
        font = QFont(FONT_FAMILY)
        app.setFont(font)

    presenter = FocusStepsPresenter()
    window = FocusStepsView(presenter)
    
    if is_modal:
        # For a true modal/blocking experience, we use exec_()
        window.setWindowModality(Qt.ApplicationModal)
        window.show()
        app.exec() # This will block until the window is closed
    else:
        window.show()
        # In non-modal mode, just show the window; the main app.exec() will handle its event loop.

if __name__ == "__main__":
    # This allows the script to be run directly.
    run(is_modal=False)
