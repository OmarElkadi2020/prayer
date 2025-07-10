import os
import sys

# Add the project root to the Python path to allow imports from src
script_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(script_dir, ".")) # Current directory is project root
sys.path.insert(0, project_root)

from src.prayer.config import adhan_path
from src.prayer.actions import play, focus_mode

def dry_run_adhan():
    print("Performing adhan dry run...")
    adhan_audio_path = adhan_path()
    print(f"Playing adhan from: {adhan_audio_path}")
    play(f"ffplay -nodisp -autoexit -loglevel quiet '{adhan_audio_path}'")
    print("Adhan played. Now activating focus mode...")
    focus_mode()
    print("Focus mode activated. Check your network and any opened windows.")

if __name__ == "__main__":
    dry_run_adhan()