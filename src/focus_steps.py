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
import os
import re
import random
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

# --- Configuration Constants ---
# Using constants for better maintainability and clarity.
APP_TITLE = "تهيئة الخشوع"
WINDOW_WIDTH = 400
FONT_FAMILY = "Noto Sans Arabic"

# ==================================================================
# ❶ Asset and Content Loading
# ==================================================================

def get_asset_path(package, resource):
    """
    Safely retrieves the path to a resource file within a package.
    Returns an empty string if the file is not found.
    """
    try:
        with resources.path(package, resource) as p:
            return str(p)
    except (FileNotFoundError, ModuleNotFoundError):
        print(f"Warning: Asset '{resource}' not found in package '{package}'.")
        return ""

def load_steps_from_file(file_path):
    """
    Loads step content from a text file.
    Steps are separated by '---STEP_START---'.
    Each step has a title (first line) and a description.
    """
    if not file_path:
        return [("خطأ", "ملف محتوى الخطوات غير موجود.")]

    steps = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split content into individual step blocks
        raw_steps = content.split('---STEP_START---')
        for raw_step in raw_steps:
            if not raw_step.strip():
                continue
            
            # The description part ends at ---STEP_END---, but we only need the content before it.
            step_content = raw_step.split('---STEP_END---')[0].strip()
            
            # The title is the first line of the step content.
            title_end_idx = step_content.find('\n')
            if title_end_idx != -1:
                title = step_content[:title_end_idx].strip()
                description = step_content[title_end_idx:].strip()
            else:
                title = step_content
                description = ""
            
            steps.append((title, description))
    except FileNotFoundError:
        print(f"Error: Could not find the steps content file at '{file_path}'.")
        return [("خطأ", f"لم يتم العثور على ملف المحتوى:\n{file_path}")]
    
    return steps

from src.config.security import get_asset_path

# --- Constants ---
SOUND_PATH = get_asset_path('complete_sound.wav')
ICON_PATH = get_asset_path('mosque.png')
STEPS_FILE_PATH = str(resources.files('config').joinpath('steps_content.txt'))
STEPS = load_steps_from_file(STEPS_FILE_PATH)



# ==================================================================
# ❷ Main Application Window
# ==================================================================

class StepWindow(QWidget):
    """
    The main window for the application. It displays steps sequentially
    and handles user navigation. The window resizes to fit its content.
    """
    def __init__(self, initial_step_index: int = 0, disable_sound: bool = False):
        super().__init__()
        
        # --- State Management ---
        self.current_step_index = initial_step_index
        self.all_steps = STEPS + [("انتهيت", "تقبّل الله طاعتك.")]
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

        # --- First UI Update ---
        self.update_ui_for_current_step()

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
        self.action_btn.clicked.connect(self.handle_action_button)
        self.next_btn.clicked.connect(self.go_to_next_step)
        self.prev_btn.clicked.connect(self.go_to_previous_step)

    def setup_sound_effect(self):
        """Initializes the sound effect player."""
        self.sound_effect = QSoundEffect()
        if SOUND_PATH:
            self.sound_effect.setSource(QUrl.fromLocalFile(SOUND_PATH))
            self.sound_effect.setVolume(0.7)

    def parse_and_display_step_content(self, description):
        """Parses the description and populates the content area."""
        # Clear previous content
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Regex to find sections like **الهدف:**, **الدليل:**, *الفائدة الروحية:*
        goal_pattern = re.compile(r'\*\*الهدف:\*\*\s*(.*?)(?=\n\d+\.\s\*\*الدليل:|\Z)', re.DOTALL)
        evidence_pattern = re.compile(r'\d+\.\s\*\*الدليل:\*\*\s*(.*?)\s*\*الفائدة الروحية:\*\s*(.*?)(?=\n\d+\.\s\*\*الدليل:|\Z)', re.DOTALL)
        
        goals = goal_pattern.findall(description)
        evidences = evidence_pattern.findall(description)

        display_items = []
        if goals:
            display_items.append(('goal', random.choice(goals).strip()))
        if evidences:
            evidence_text, benefit_text = random.choice(evidences)
            display_items.append(('evidence', (evidence_text.strip(), benefit_text.strip())))
        
        random.shuffle(display_items)

        if not display_items:
             # If no special sections, display the whole description
            content_lbl = QLabel(description, objectName="sectionContent")
            content_lbl.setWordWrap(True)
            self.content_layout.addWidget(content_lbl)
            return

        for item_type, content in display_items:
            if item_type == 'goal':
                self.content_layout.addWidget(QLabel("<b>الهدف:</b>", objectName="sectionTitle"))
                content_lbl = QLabel(content, objectName="sectionContent")
                content_lbl.setWordWrap(True)
                self.content_layout.addWidget(content_lbl)
            elif item_type == 'evidence':
                evidence_text, benefit_text = content
                self.content_layout.addWidget(QLabel("<b>الدليل:</b>", objectName="sectionTitle"))
                
                evidence_lbl = QLabel(evidence_text, objectName="sectionContent")
                evidence_lbl.setWordWrap(True)
                self.content_layout.addWidget(evidence_lbl)

                benefit_title_lbl = QLabel("<em>الفائدة الروحية:</em>", objectName="sectionTitle")
                benefit_title_lbl.setStyleSheet("margin-top: 10px; font-size: 16px;")
                self.content_layout.addWidget(benefit_title_lbl)

                benefit_lbl = QLabel(benefit_text, objectName="sectionContent")
                benefit_lbl.setWordWrap(True)
                self.content_layout.addWidget(benefit_lbl)

    def update_ui_for_current_step(self):
        """Updates the entire UI based on the current step index."""
        is_final_step = self.current_step_index == len(STEPS)
        
        title, description = self.all_steps[self.current_step_index]

        # Update text content
        self.title_lbl.setText(title)
        self.parse_and_display_step_content(description)
        
        # Update navigation controls visibility and state
        self.prev_btn.setVisible(not is_final_step)
        self.next_btn.setVisible(not is_final_step)
        self.step_counter_lbl.setVisible(not is_final_step)
        
        if not is_final_step:
            self.step_counter_lbl.setText(f"{self.current_step_index + 1} / {len(STEPS)}")
            self.action_btn.setText("تم")
        else:
            # Configure for the final "Finished" screen
            self.action_btn.setText("إغلاق")

        # Enable/disable navigation buttons
        self.prev_btn.setEnabled(self.current_step_index > 0)
        self.next_btn.setEnabled(self.current_step_index < len(STEPS) - 1)
        
        self.play_sound()
        
        # --- Adjust window size to content ---
        # Let the content widget determine its required height.
        content_height = self.content_widget.sizeHint().height()
        
        # Set the scroll area's minimum height. Add a lower bound to avoid it becoming too small.
        MIN_SCROLL_AREA_HEIGHT = 100
        self.scroll_area.setMinimumHeight(max(content_height, MIN_SCROLL_AREA_HEIGHT))
        
        # Ask the window to resize to the new optimal size.
        self.adjustSize()

    def play_sound(self):
        """Plays the completion sound if available."""
        # Ensure SOUND_PATH is valid and the sound effect is loaded before playing.
        if SOUND_PATH and self.sound_effect.isLoaded():
            self.sound_effect.play()

    def handle_action_button(self):
        """
        Handles the click of the main action button.
        
        It either proceeds to the next step or closes the application
        if it's on the final step.
        """
        if self.current_step_index == len(STEPS):
            self.close()
        else:
            self.go_to_next_step()

    def go_to_next_step(self):
        """Advances to the next step if not on the last one."""
        if self.current_step_index < len(STEPS):
            self.current_step_index += 1
            self.update_ui_for_current_step()

    def go_to_previous_step(self):
        """Goes back to the previous step if not on the first one."""
        if self.current_step_index > 0:
            self.current_step_index -= 1
            self.update_ui_for_current_step()


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

    window = StepWindow()
    
    if is_modal:
        # For a true modal/blocking experience, we use exec_()
        window.setWindowModality(Qt.ApplicationModal)
        window.show()
        window.exec() # This will block until the window is closed
    else:
        window.show()
        # In non-modal mode, just show the window; the main app.exec() will handle its event loop.

if __name__ == "__main__":
    # This allows the script to be run directly.
    run(is_modal=False)
