import os
import sys
from datetime import datetime, timedelta

# Add the project root to the Python path to allow imports from src
script_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(script_dir, "."))
sys.path.insert(0, project_root)

from src.prayer.config import adhan_path, TZ
from src.prayer.scheduler import PrayerScheduler

def dry_run_adhan_with_scheduler():
    """
    Performs a dry run of the Adhan, Duaa, and Focus Mode using the scheduler.
    - Adhan and Focus Mode start in 4 seconds.
    - Duaa starts after the Adhan is finished (approximated at 2m 53s).
    """
    print("Performing scheduled adhan dry run...")
    
    # --- Setup ---
    audio_path = adhan_path()
    scheduler = PrayerScheduler(audio_path=audio_path)
    
    # --- Scheduling ---
    now = datetime.now(TZ)
    start_time = now + timedelta(seconds=4)
    
    # Adhan duration is approximated based on the original scheduler's logic
    adhan_duration = timedelta(minutes=2, seconds=53)
    duaa_time = start_time + adhan_duration

    print(f"Scheduling Adhan and Focus Mode at: {start_time.strftime('%H:%M:%S')}")
    print(f"Scheduling Duaa at: {duaa_time.strftime('%H:%M:%S')}")

    # 1. Schedule Adhan
    scheduler.scheduler.add_job(
        scheduler.play_adhan, "date", run_date=start_time,
        id="dry-run-adhan", args=[audio_command]
    )

    # 2. Schedule Focus Mode
    scheduler.scheduler.add_job(
        scheduler.trigger_focus_mode, "date", run_date=start_time,
        id="dry-run-focus"
    )

    # 3. Schedule Duaa
    scheduler.scheduler.add_job(
        scheduler.play_duaa, "date", run_date=duaa_time,
        id="dry-run-duaa"
    )

    # --- Execution ---
    print("\nScheduler started. Waiting for jobs to trigger...")
    try:
        scheduler.run()
    except (KeyboardInterrupt, SystemExit):
        print("\nScheduler stopped by user.")

if __name__ == "__main__":
    dry_run_adhan_with_scheduler()
