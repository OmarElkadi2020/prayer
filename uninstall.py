import os
import subprocess
import sys
import shutil
from appdirs import user_config_dir, user_data_dir

APP_NAME = "PrayerPlayer"
APP_AUTHOR = "Omar"

def run_command(command, description, check=True, shell=False):
    """Helper to run shell commands and provide feedback."""
    print(f"--- {description} ---")
    try:
        result = subprocess.run(command, check=check, shell=shell, capture_output=True, text=True)
        if result.stdout:
            print(f"Stdout: {result.stdout}")
        if result.stderr:
            print(f"Stderr: {result.stderr}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error: Command failed with exit code {e.returncode}.")
        if e.stdout:
            print(f"Stdout: {e.stdout}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        # Do not exit here, allow cleanup to continue if possible
        return None
    except FileNotFoundError:
        print(f"Error: Command not found. Please ensure '{command[0]}' is installed and in your PATH.")
        return None

def get_app_data_paths():
    """Returns paths for user-specific config and data directories."""
    config_dir = user_config_dir(APP_NAME, APP_AUTHOR)
    data_dir = user_data_dir(APP_NAME, APP_AUTHOR)
    
    config_file = os.path.join(config_dir, 'config.json')
    token_file = os.path.join(data_dir, 'token.json') # Token is data, not config
    
    return config_dir, data_dir, config_file, token_file

def remove_path(path, description):
    """Removes a file or directory and prints status."""
    if os.path.exists(path):
        print(f"Removing {description} at: {path}")
        try:
            if os.path.isfile(path):
                os.remove(path)
            else: # Assume it's a directory
                shutil.rmtree(path)
            print(f"Successfully removed {description}.")
        except OSError as e:
            print(f"Error removing {description} at {path}: {e}")
    else:
        print(f"{description} not found at: {path}. Skipping removal.")

def remove_user_data():
    print("\n--- Removing User Data and Logs ---")
    config_dir, data_dir, config_file, token_file = get_app_data_paths()

    remove_path(config_file, "configuration file")
    remove_path(token_file, "Google Calendar token file")
    
    # Attempt to remove the directories if they are empty or only contain what we just removed
    # This is a best-effort cleanup.
    if os.path.exists(config_dir) and not os.listdir(config_dir):
        remove_path(config_dir, "configuration directory")
    if os.path.exists(data_dir) and not os.listdir(data_dir):
        remove_path(data_dir, "data directory")

    # Remove log files from /tmp
    log_file_stdout = "/tmp/prayer-player.stdout.log"
    log_file_stderr = "/tmp/prayer-player.stderr.log"
    remove_path(log_file_stdout, "stdout log file")
    remove_path(log_file_stderr, "stderr log file")

def remove_venv():
    print("\n--- Removing Development Virtual Environment ---")
    project_root = os.getcwd()
    venv_path = os.path.join(project_root, "myenv")
    remove_path(venv_path, "virtual environment")

def main_linux_uninstall():
    print("Prayer Player Uninstallation for Linux")
    print("--------------------------------------")

    # --- 1. Application Removal ---
    print("\n--- Removing Application Files ---")
    # Check if installed via .deb
    dpkg_check = run_command(["dpkg", "-s", "prayer-player"], "Checking for .deb package installation", check=False)
    if dpkg_check and dpkg_check.returncode == 0:
        print("Prayer Player was detected as a .deb package installation.")
        print("Please run the following command to uninstall the application:")
        print("  sudo dpkg -r prayer-player")
    else:
        print("Prayer Player was not detected as a .deb package installation.")
        print("Attempting to remove manually installed files (if any):")
        remove_path("/usr/local/bin/PrayerPlayer", "executable")
        remove_path("/usr/share/applications/prayer-player.desktop", "desktop entry")
        remove_path("/usr/share/icons/hicolor/256x256/apps/prayer-player.png", "application icon")

    # --- 2. Stop and disable the systemd service ---
    print("\n--- Removing System Service ---")
    service_file = os.path.expanduser("~/.config/systemd/user/prayer-player.service")
    if os.path.exists(service_file):
        print("Stopping and disabling systemd user service...")
        run_command(["systemctl", "--user", "stop", "prayer-player.service"], "Stopping service", check=False)
        run_command(["systemctl", "--user", "disable", "prayer-player.service"], "Disabling service", check=False)
        remove_path(service_file, "systemd service file")
        run_command(["systemctl", "--user", "daemon-reload"], "Reloading systemd daemon")
        print("Service removed successfully.")
    else:
        print("Systemd service file not found. Skipping service removal.")

    # --- 3. Remove User Data and Logs ---
    remove_user_data()

    # --- 4. Remove Development Virtual Environment ---
    remove_venv()

    print("\nUninstallation complete. If you ran this script from the project directory, you can now delete the directory manually.")

def main_macos_uninstall():
    print("Prayer Player Uninstallation for macOS")
    print("--------------------------------------")

    # --- 1. Application Removal ---
    print("\n--- Removing Application Files ---")
    app_paths = [
        "/Applications/PrayerPlayer.app",
        os.path.expanduser("~/Applications/PrayerPlayer.app")
    ]
    app_removed = False
    for app_path in app_paths:
        if os.path.exists(app_path):
            remove_path(app_path, "PrayerPlayer.app")
            app_removed = True
            break
    if not app_removed:
        print("PrayerPlayer.app not found in common application directories. Skipping application removal.")

    # --- 2. Unload and remove the launchd agent ---
    print("\n--- Removing System Service ---")
    plist_file = os.path.expanduser("~/Library/LaunchAgents/com.prayerplayer.scheduler.plist")
    if os.path.exists(plist_file):
        print("Unloading launchd agent...")
        run_command(["launchctl", "unload", plist_file], "Unloading launchd agent", check=False)
        remove_path(plist_file, ".plist file")
        print("Launchd agent removed successfully.")
    else:
        print("Launchd .plist file not found. Skipping agent removal.")

    # --- 3. Remove User Data and Logs ---
    remove_user_data()

    # --- 4. Remove Development Virtual Environment ---
    remove_venv()

    print("\nUninstallation complete. If you ran this script from the project directory, you can now delete the directory manually.")

def main_windows_uninstall():
    print("Prayer Player Uninstallation for Windows")
    print("----------------------------------------")

    # --- 1. Application Removal ---
    print("\n--- Removing Application Files ---")
    print("Prayer Player was likely installed via an executable installer.")
    print("To uninstall the main application, please go to:")
    print("  Control Panel -> Programs -> Programs and Features (or 'Add or Remove Programs')")
    print("  and uninstall 'Prayer Player' from there.")

    # --- 2. Remove User Data and Logs ---
    remove_user_data()

    # --- 3. Remove Development Virtual Environment ---
    remove_venv()

    print("\nUninstallation complete. If you ran this script from the project directory, you can now delete the directory manually.")

if __name__ == "__main__":
    # Ask for confirmation once at the beginning for all removals
    print("This script will attempt to remove Prayer Player application files,")
    print("user configuration/data, and development-related files.")
    confirm = input("Are you sure you want to proceed with uninstallation? (y/N): ")
    if confirm.lower() != 'y':
        print("Uninstallation cancelled.")
        sys.exit(0)

    if sys.platform.startswith('linux'):
        main_linux_uninstall()
    elif sys.platform == 'darwin':
        main_macos_uninstall()
    elif sys.platform == 'win32':
        main_windows_uninstall()
    else:
        print(f"Unsupported operating system: {sys.platform}")