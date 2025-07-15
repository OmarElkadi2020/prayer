import unittest
from unittest.mock import patch
import os

from src.actions import play, focus_mode
from src.config.security import get_asset_path

class TestActions(unittest.TestCase):

    @patch('src.actions.pydub_play')
    def test_play_real_wav_audio(self, mock_pydub_play):
        """
        Tests the play function with a real WAV audio file, mocking the actual playback.
        """
        try:
            # Assuming get_asset_path correctly finds the asset path
            audio_path = get_asset_path('complete_sound.wav')
        except FileNotFoundError:
            # Fallback for different execution context
            audio_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'assets', 'complete_sound.wav')

        self.assertTrue(os.path.exists(audio_path), f"Test audio file not found at {audio_path}")

        try:
            play(audio_path)
            mock_pydub_play.assert_called_once() # Assert that pydub_play was called
        except Exception as e:
            self.fail(f"play() raised an exception unexpectedly: {e}")

    @patch('src.actions.run_focus_steps_window')
    def test_focus_mode(self, mock_run_focus_steps):
        """
        Tests that focus_mode calls the run_focus_steps_window function.
        """
        focus_mode()
        mock_run_focus_steps.assert_called_once()

    def test_play_file_not_found(self):
        """
        Tests that the play function handles a non-existent file gracefully.
        """
        non_existent_file = "non_existent_file.wav"
        with patch('src.actions.LOG') as mock_log:
            play(non_existent_file)
            mock_log.error.assert_called_with(f"Audio file not found: {non_existent_file}")

if __name__ == '__main__':
    unittest.main()
