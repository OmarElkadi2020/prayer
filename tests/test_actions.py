from __future__ import annotations

import pytest
from prayer import actions
from prayer.config import TZ
from datetime import datetime



def test_focus_mode(mocker):
    """Test the focus_mode action."""
    mock_run_focus_steps_window = mocker.patch("prayer.actions.run_focus_steps_window")
    mock_log_info = mocker.patch("prayer.actions.LOG.info")

    actions.focus_mode()

    mock_run_focus_steps_window.assert_called_once()
    mock_log_info.assert_any_call("🕌 Focus‑mode ON.")
