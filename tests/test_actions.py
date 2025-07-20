import unittest
from unittest.mock import patch
import os

from src.actions import play, run_focus_steps
from src.config.security import get_asset_path
import types
import sys

class TestActions(unittest.TestCase):

    @patch('subprocess.run')
    def test_play_real_wav_audio(self, mock_subprocess_run):
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
            mock_subprocess_run.assert_called_once_with(
                ['aplay', audio_path],
                check=True,
            )
        except Exception as e:
            self.fail(f"play() raised an exception unexpectedly: {e}")

    def test_focus_mode(self):
        """
        Tests that focus_mode calls the run_focus_steps function.
        """
        dummy_mod = types.SimpleNamespace(run=unittest.mock.Mock())
        with patch.dict(sys.modules, {'src.focus_steps_view': dummy_mod}):
            run_focus_steps(is_modal=True)
            dummy_mod.run.assert_called_once_with(is_modal=True)

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
