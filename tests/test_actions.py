from __future__ import annotations

import pytest
from prayer import actions
from prayer.config import TZ
from datetime import datetime

@pytest.fixture
def mock_popen(mocker):
    return mocker.patch("subprocess.Popen")

@pytest.fixture
def mock_call(mocker):
    return mocker.patch("subprocess.call")

@pytest.fixture
def mock_check_output(mocker):
    return mocker.patch("subprocess.check_output")

def test_play(mock_popen):
    """Test that the play action calls subprocess.Popen with the correct command."""
    test_command = "ffplay my_sound.mp3"
    actions.play(test_command)
    mock_popen.assert_called_once_with(test_command, shell=True)

def test_focus_mode(mock_popen, mock_call, mock_check_output, mocker):
    """Test the focus_mode action."""
    # Mock the scheduler to prevent it from actually blocking
    mock_scheduler = mocker.MagicMock()
    mocker.patch("prayer.actions.BlockingScheduler", return_value=mock_scheduler)

    actions.focus_mode()

    # Verify that the network is turned off
    mock_call.assert_any_call(actions.NET_OFF_CMD, shell=True)

    # Verify that the focus steps script is started
    mock_popen.assert_called()
    
    # Verify that the network is scheduled to be turned back on
    mock_scheduler.add_job.assert_called_once()
    mock_scheduler.start.assert_called_once()
