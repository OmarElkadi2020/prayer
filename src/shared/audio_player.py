# src/shared/audio_player.py
from __future__ import annotations
import os
import subprocess
import sys
import tempfile
from importlib import resources
import logging
import threading

LOG = logging.getLogger(__name__)

_current_playback_process: subprocess.Popen | None = None
_playback_thread: threading.Thread | None = None

def _play_with_playsound(audio_path: str):
    """Plays audio using the playsound library as a fallback."""
    try:
        from playsound import playsound
        LOG.info(f"📢 Attempting to play audio using 'playsound': {audio_path}")
        playsound(audio_path) # playsound is blocking
        LOG.info("Playback finished successfully via 'playsound'.")
    except Exception as e:
        LOG.error(f"An unexpected error occurred during playsound execution: {e}")

def play(audio_path: str) -> None:
    """
    Plays the given audio file using a suitable method for the current platform.
    This is a non-blocking call.
    """
    global _current_playback_process, _playback_thread

    effective_audio_path = audio_path

    # If running in a PyInstaller bundle and the audio_path doesn't exist,
    # it might be a bundled resource that needs to be extracted to a temporary file.
    if getattr(sys, 'frozen', False) and not os.path.exists(audio_path):
        try:
            # Read the binary content of the default adhan.wav from the package
            audio_content = resources.read_binary('assets', 'adhan.wav')
            
            # Create a temporary file and write the content to it
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
                temp_audio_file.write(audio_content)
                effective_audio_path = temp_audio_file.name
            
            LOG.info(f"Extracted bundled adhan.wav to temporary file: {effective_audio_path}")
        except Exception as e:
            LOG.error(f"Error extracting bundled adhan.wav: {e}")
            effective_audio_path = None # Indicate failure to get a valid path

    if not effective_audio_path or not os.path.exists(effective_audio_path):
        LOG.error(f"Audio file not found: {audio_path} (effective: {effective_audio_path})")
        return

    def _playback_target():
        global _current_playback_process
        if sys.platform.startswith('linux'):
            LOG.info(f"📢 Attempting to play audio using 'aplay': {effective_audio_path}")
            try:
                _current_playback_process = subprocess.Popen(['aplay', effective_audio_path])
                _current_playback_process.wait(timeout=180) # Wait for process to finish
                LOG.info("Playback finished successfully via 'aplay'.")
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
                LOG.error(f"aplay failed with error: {e}. Falling back to playsound.")
                _play_with_playsound(effective_audio_path)
            except Exception as e:
                LOG.error(f"An unexpected error occurred during aplay execution: {e}. Falling back to playsound.")
                _play_with_playsound(effective_audio_path)
        else:
            # For other platforms, use playsound directly
            _play_with_playsound(effective_audio_path)

        # Clean up the temporary file if it was created after playback finishes
        if effective_audio_path != audio_path and os.path.exists(effective_audio_path):
            try:
                os.remove(effective_audio_path)
                LOG.info(f"Cleaned up temporary audio file: {effective_audio_path}")
            except Exception as e:
                LOG.warning(f"Could not remove temporary audio file {effective_audio_path}: {e}")
        _current_playback_process = None # Clear the process after it finishes

    _playback_thread = threading.Thread(target=_playback_target)
    _playback_thread.start()

def stop_playback():
    """Stops any currently active audio playback."""
    global _current_playback_process
    if _current_playback_process and _current_playback_process.poll() is None:
        LOG.info("Attempting to stop audio playback.")
        _current_playback_process.terminate()
        try:
            _current_playback_process.wait(timeout=5) # Give it a moment to terminate
            LOG.info("Audio playback stopped.")
        except subprocess.TimeoutExpired:
            LOG.warning("Audio playback process did not terminate in time, killing it.")
            _current_playback_process.kill()
    _current_playback_process = None # Ensure it's cleared after attempt to stop
