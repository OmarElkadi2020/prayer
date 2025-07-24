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

_active_playback_processes: list[subprocess.Popen] = []
_playback_finished_event = threading.Event()

def _play_with_playsound(audio_path: str):
    """Plays audio using the playsound library as a fallback, via subprocess."""
    global _active_playback_processes
    try:
        command = [sys.executable, "-c", f"from playsound import playsound; playsound('{audio_path}')"]
        LOG.info(f"📢 Attempting to play audio using 'playsound' via subprocess: {audio_path}")
        process = subprocess.Popen(command)
        _active_playback_processes.append(process)
        process.wait(timeout=180)
        LOG.info("Playback finished successfully via 'playsound' subprocess.")
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        LOG.error(f"playsound subprocess failed with error: {e}")
    except Exception as e:
        LOG.error(f"An unexpected error occurred during playsound subprocess execution: {e}")
    finally:
        if process in _active_playback_processes:
            _active_playback_processes.remove(process)

def play(audio_path: str) -> None:
    """
    Plays the given audio file using a suitable method for the current platform.
    This is a non-blocking call.
    """
    global _active_playback_processes

    _playback_finished_event.clear()

    effective_audio_path = audio_path

    if getattr(sys, 'frozen', False) and not os.path.exists(audio_path):
        try:
            audio_content = resources.read_binary('assets', 'adhan.wav')
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
                temp_audio_file.write(audio_content)
                effective_audio_path = temp_audio_file.name
            LOG.info(f"Extracted bundled adhan.wav to temporary file: {effective_audio_path}")
        except Exception as e:
            LOG.error(f"Error extracting bundled adhan.wav: {e}")
            effective_audio_path = None

    if not effective_audio_path or not os.path.exists(effective_audio_path):
        LOG.error(f"Audio file not found: {audio_path} (effective: {effective_audio_path})")
        _playback_finished_event.set()
        return

    def _playback_target():
        global _active_playback_processes
        process = None
        try:
            if sys.platform.startswith('linux'):
                LOG.info(f"📢 Attempting to play audio using 'aplay': {effective_audio_path}")
                process = subprocess.Popen(['aplay', effective_audio_path])
                _active_playback_processes.append(process)
                process.wait(timeout=180)
                LOG.info("Playback finished successfully via 'aplay'.")
            else:
                _play_with_playsound(effective_audio_path)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            LOG.error(f"aplay failed with error: {e}. Falling back to playsound.")
            _play_with_playsound(effective_audio_path)
        except Exception as e:
            LOG.error(f"An unexpected error occurred during aplay execution: {e}. Falling back to playsound.")
            _play_with_playsound(effective_audio_path)
        finally:
            if process and process in _active_playback_processes:
                _active_playback_processes.remove(process)
            # Clean up the temporary file if it was created after playback finishes
            if effective_audio_path != audio_path and os.path.exists(effective_audio_path):
                try:
                    os.remove(effective_audio_path)
                    LOG.info(f"Cleaned up temporary audio file: {effective_audio_path}")
                except Exception as e:
                    LOG.warning(f"Could not remove temporary audio file {effective_audio_path}: {e}")
            if not _active_playback_processes: # Only set event if all playback is done
                _playback_finished_event.set()

    threading.Thread(target=_playback_target).start()

def wait_for_playback_to_finish():
    """Waits for all active audio playbacks to finish."""
    LOG.info("Waiting for audio playback to finish...")
    _playback_finished_event.wait()
    LOG.info("Audio playback finished.")

def stop_playback():
    """Stops any currently active audio playback."""
    global _active_playback_processes
    for process in list(_active_playback_processes): # Iterate over a copy as list will be modified
        if process.poll() is None: # Process is still running
            LOG.info(f"Attempting to stop audio playback process {process.pid}.")
            process.terminate()
            try:
                process.wait(timeout=5)
                LOG.info(f"Audio playback process {process.pid} stopped.")
            except subprocess.TimeoutExpired:
                LOG.warning(f"Audio playback process {process.pid} did not terminate in time, killing it.")
                process.kill()
        if process in _active_playback_processes:
            _active_playback_processes.remove(process)
    _playback_finished_event.set() # Set the event to unblock any waiting threads
