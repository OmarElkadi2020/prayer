import unittest
from unittest.mock import Mock, patch

from src.gui.notification_service import NotificationService
from src.domain.notification_messages import AudioPlaybackRequestedEvent, FocusModeRequestedEvent

class TestNotificationService(unittest.TestCase):

    def setUp(self):
        self.mock_event_bus = Mock()
        self.notification_service = NotificationService(event_bus=self.mock_event_bus)

    @patch('src.gui.notification_service.play')
    def test_handle_audio_playback_request(self, mock_play):
        mock_audio_path = "/path/to/audio.wav"
        event = AudioPlaybackRequestedEvent(audio_path=mock_audio_path)

        self.notification_service.handle_audio_playback_requested(event)

        mock_play.assert_called_once_with(mock_audio_path)

    @patch('PySide6.QtCore.QTimer.singleShot', side_effect=lambda *args, **kwargs: args[1]() if len(args) > 1 else None)
    @patch('src.gui.notification_service.NotificationService._run_focus_steps')
    def test_handle_focus_mode_request(self, mock_run_focus_steps, mock_single_shot):
        event = FocusModeRequestedEvent()

        self.notification_service.handle_focus_mode_requested(event)

        mock_run_focus_steps.assert_called_once_with(is_modal=True)

if __name__ == '__main__':
    unittest.main()
