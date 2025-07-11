from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, mock_open
from prayer.scheduler import PrayerScheduler, duaa_path
from prayer.config import TZ
from datetime import datetime

@patch('prayer.scheduler.BlockingScheduler')
def test_scheduler_initialization(mock_scheduler_class):
    """Test that the PrayerScheduler initializes correctly."""
    mock_scheduler_instance = MagicMock()
    mock_scheduler_class.return_value = mock_scheduler_instance
    
    with patch('prayer.scheduler.duaa_path', return_value="path/to/duaa.wav") as mock_duaa:
        scheduler = PrayerScheduler("my_audio_cmd")
        
        assert scheduler.audio_path == "my_audio_cmd"
        mock_scheduler_class.assert_called_once_with(timezone=TZ)
        assert scheduler.scheduler == mock_scheduler_instance
        mock_duaa.assert_called_once()
        assert scheduler._duaa_audio_path == "path/to/duaa.wav"

def test_duaa_path_success(mocker):
    """Test that duaa_path returns the correct path when the file exists."""
    mock_path = MagicMock()
    mock_path.__enter__.return_value = "/fake/path/to/duaa_after_adhan.wav"
    mocker.patch('importlib.resources.path', return_value=mock_path)
    
    path = duaa_path()
    
    assert path == "/fake/path/to/duaa_after_adhan.wav"

def test_duaa_path_failure(mocker):
    """Test that duaa_path returns an empty string if the file is not found."""
    mocker.patch('importlib.resources.path', side_effect=FileNotFoundError)
    mock_log = mocker.patch('prayer.scheduler.LOG.error')
    
    path = duaa_path()
    
    assert path == ""
    mock_log.assert_called_once_with("Duaa audio file not found.")

@patch('prayer.scheduler.play')
def test_play_adhan_wrapper(mock_play):
    """Test the play_adhan action wrapper."""
    scheduler = PrayerScheduler("test_cmd")
    scheduler.play_adhan("specific_command")
    mock_play.assert_called_once_with("specific_command")

@patch('prayer.scheduler.play')
def test_play_duaa_wrapper(mock_play, mocker):
    """Test the play_duaa action wrapper."""
    mocker.patch('prayer.scheduler.duaa_path', return_value="path/to/duaa.wav")
    scheduler = PrayerScheduler("test_cmd")
    scheduler.play_duaa()
    expected_cmd = "path/to/duaa.wav"
    mock_play.assert_called_once_with(expected_cmd)

@patch('prayer.scheduler.focus_mode')
def test_trigger_focus_mode_wrapper(mock_focus_mode):
    """Test the trigger_focus_mode action wrapper."""
    scheduler = PrayerScheduler("test_cmd")
    scheduler.trigger_focus_mode()
    mock_focus_mode.assert_called_once()

@patch('prayer.scheduler.BlockingScheduler')
def test_run_starts_scheduler(mock_scheduler_class):
    """Test that the run method starts the scheduler."""
    mock_scheduler_instance = MagicMock()
    mock_scheduler_class.return_value = mock_scheduler_instance
    
    scheduler = PrayerScheduler("test_cmd")
    scheduler.run()
    
    mock_scheduler_instance.start.assert_called_once()
