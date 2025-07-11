#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for the focus steps window.
"""

import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
import sys
import os
import re

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.prayer.focus_steps import StepWindow, STEPS

# ------------------------------------------------------------------
# ❶ Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def app(qtbot):
    """Create a StepWindow instance for testing."""
    window = StepWindow(disable_sound=True) # Disable sound for tests by default
    qtbot.addWidget(window)
    return window

# ------------------------------------------------------------------
# ❷ Tests
# ------------------------------------------------------------------

def test_initial_state(app):
    """Test the initial state of the window."""
    assert app.windowTitle() == "تهيئة الخشوع"
    # The first step is loaded on initialization
    first_step_title, first_step_desc = STEPS[0]
    # Use regex to strip HTML tags for comparison
    import re
    clean_title = re.sub(r'<[^>]+>', '', app.title_lbl.text()).strip()
    assert clean_title == first_step_title
    assert app.action_btn.text() == "تم"

def test_initial_step_index(qtbot):
    """Test that the window can be initialized to a specific step."""
    initial_index = 2 # Test with the third step (index 2)
    window = StepWindow(initial_step_index=initial_index, disable_sound=True)
    qtbot.addWidget(window)

    expected_title, _ = STEPS[initial_index]
    clean_title = re.sub(r'<[^>]+>', '', window.title_lbl.text()).strip()
    assert clean_title == expected_title
    assert window.current_step_index == initial_index
    assert window.step_counter_lbl.text() == f"{initial_index + 1} / {len(STEPS)}"

def test_step_progression(app, qtbot):
    """Test that clicking the button progresses through the steps."""
    for i, (title, desc) in enumerate(STEPS[1:]):
        qtbot.mouseClick(app.action_btn, Qt.MouseButton.LeftButton)
        # Use regex to strip HTML tags for comparison
        import re
        clean_title = re.sub(r'<[^>]+>', '', app.title_lbl.text()).strip()
        assert clean_title == title
        assert app.action_btn.text() == "تم"

def test_final_step(app, qtbot):
    """Test the final step and window closing."""
    app.go_to_next_step() # Load first step
    # Go through all the steps
    for _ in STEPS:
        qtbot.mouseClick(app.action_btn, Qt.MouseButton.LeftButton)

    # After the last step, the final message is shown
    assert app.title_lbl.text() == "انتهيت"
    assert app.action_btn.text() == "إغلاق"

    # Clicking the button again should close the window
    qtbot.mouseClick(app.action_btn, Qt.MouseButton.LeftButton)
    assert app.isHidden()

def test_play_sound(qtbot, monkeypatch):
    """Test that the sound is played on each step."""
    # Mock QSoundEffect before StepWindow is instantiated
    mock_qsound_effect = MagicMock()
    monkeypatch.setattr('src.prayer.focus_steps.QSoundEffect', mock_qsound_effect)

    # Create a StepWindow instance with sound enabled for this specific test
    app_with_sound = StepWindow(disable_sound=False)
    qtbot.addWidget(app_with_sound)

    # The play method of the mocked QSoundEffect should have been called once during init
    assert mock_qsound_effect.return_value.play.call_count == 1

    # Manually call go_to_next_step to simulate the first step
    app_with_sound.go_to_next_step()
    assert mock_qsound_effect.return_value.play.call_count == 2 # After init (1) and first go_to_next_step (1)

    # Click through the rest of the steps
    for i in range(len(STEPS) - 1): # Iterate through remaining steps (excluding the last one)
        qtbot.mouseClick(app_with_sound.action_btn, Qt.MouseButton.LeftButton)
        # Each click adds 1 call. So after i clicks, total calls = 2 + (i+1) = i + 3
        assert mock_qsound_effect.return_value.play.call_count == i + 3


@patch('src.prayer.focus_steps.SOUND_PATH', "") # Directly patch the global SOUND_PATH
def test_play_sound_disabled(app, qtbot, monkeypatch):
    """Test that sound is not played if the file does not exist."""
    mock_play = MagicMock()
    monkeypatch.setattr(app.sound_effect, 'play', mock_play)
    monkeypatch.setattr(app.sound_effect, 'isLoaded', MagicMock(return_value=True))

    # Manually call go_to_next_step
    app.go_to_next_step()
    mock_play.assert_not_called()

    # Clicking next should also not play sound
    qtbot.mouseClick(app.action_btn, Qt.MouseButton.LeftButton)
    mock_play.assert_not_called()