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

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.prayer.focus_steps import StepWindow, STEPS

# ------------------------------------------------------------------
# ❶ Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def app(qtbot, monkeypatch):
    """Create a StepWindow instance for testing."""
    monkeypatch.setattr(StepWindow, 'next_step', lambda self: None)
    window = StepWindow()
    qtbot.addWidget(window)
    return window

# ------------------------------------------------------------------
# ❷ Tests
# ------------------------------------------------------------------

def test_initial_state(app):
    """Test the initial state of the window."""
    app.next_step() # Manually call next_step to load the first step
    assert app.windowTitle() == "تهيئة الخشوع"
    # The first step is loaded on initialization
    first_step_title, first_step_desc = STEPS[0]
    assert app.title_lbl.text() == f"<div dir='rtl' align='center'>{first_step_title}</div>"
    assert app.desc_lbl.text() == f"<div dir='rtl' align='right'>{first_step_desc}</div>"
    assert app.btn.text() == "تم"

def test_step_progression(app, qtbot):
    """Test that clicking the button progresses through the steps."""
    app.next_step() # Load first step
    for i, (title, desc) in enumerate(STEPS[1:]):
        qtbot.mouseClick(app.btn, Qt.MouseButton.LeftButton)
        assert app.title_lbl.text() == f"<div dir='rtl' align='center'>{title}</div>"
        assert app.desc_lbl.text() == f"<div dir='rtl' align='right'>{desc}</div>"
        assert app.btn.text() == "تم"

def test_final_step(app, qtbot):
    """Test the final step and window closing."""
    app.next_step() # Load first step
    # Go through all the steps
    for _ in STEPS:
        qtbot.mouseClick(app.btn, Qt.MouseButton.LeftButton)

    # After the last step, the final message is shown
    assert "انتهيت؛ تقبّل الله طاعتك" in app.title_lbl.text()
    assert app.btn.text() == "إغلاق"

    # Clicking the button again should close the window
    qtbot.mouseClick(app.btn, Qt.MouseButton.LeftButton)
    assert app.isHidden()

def test_play_sound(app, qtbot, monkeypatch):
    """Test that the sound is played on each step."""
    mock_play = MagicMock()
    monkeypatch.setattr(app.sound_effect, 'play', mock_play)

    # Manually call next_step to simulate the first step
    app.next_step()
    mock_play.assert_called_once()

    # Click through the rest of the steps
    for i in range(len(STEPS)):
        qtbot.mouseClick(app.btn, Qt.MouseButton.LeftButton)
        # +1 for init, +1 for each click
        assert mock_play.call_count == i + 2


@patch('os.path.exists', return_value=False)
def test_play_sound_disabled(mock_exists, qtbot, monkeypatch):
    """Test that sound is not played if the file does not exist."""
    # Re-create the app with the mocked os.path.exists
    window = StepWindow()
    qtbot.addWidget(window)

    mock_play = MagicMock()
    monkeypatch.setattr(window.sound_effect, 'play', mock_play)

    # Manually call next_step
    window.next_step()
    mock_play.assert_not_called()

    # Clicking next should also not play sound
    qtbot.mouseClick(window.btn, Qt.MouseButton.LeftButton)
    mock_play.assert_not_called()
