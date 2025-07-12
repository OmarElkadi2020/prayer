import os
import subprocess
import sys
import json

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
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: Command not found. Please ensure '{command[0]}' is installed and in your PATH.")
        sys.exit(1)

def main_linux_uninstall():
    print("Prayer Player Uninstallation for Linux")

    # --- 1. Stop and disable the systemd service ---
    service_file = os.path.expanduser("~/.config/systemd/user/prayer-player.service")

    if os.path.exists(service_file):
        print("Stopping and disabling systemd user service...")
        run_command(["systemctl", "--user", "stop", "prayer-player.service"], "Stopping service", check=False)
        run_command(["systemctl", "--user", "disable", "prayer-player.service"], "Disabling service", check=False)
        
        print("Removing service file...")
        os.remove(service_file)
        
        print("Reloading systemd daemon...")
        run_command(["systemctl", "--user", "daemon-reload"], "Reloading systemd daemon")
        
        print("Service removed successfully.")
    else:
        print("Systemd service file not found. Skipping service removal.")

    # --- 2. Remove project files ---
    print("The following items will be removed:")
    print(" - Virtual environment (myenv/)")
    print(" - Configuration files (src/prayer/config/config.json)")
    print(" - Google Calendar token (src/prayer/auth/token.json)")
    print(" - Log files (/tmp/prayer-player.*.log)")

    confirm = input("Are you sure you want to permanently delete these files? (y/N): ")
    if confirm.lower() != 'y':
        print("Uninstallation cancelled.")
        sys.exit(0)

    project_root = os.getcwd()

    print("Removing virtual environment...")
    venv_path = os.path.join(project_root, "myenv")
    if os.path.exists(venv_path):
        subprocess.run(f"rm -rf {venv_path}", shell=True, check=True)
        print("Virtual environment removed.")
    else:
        print("Virtual environment not found. Skipping removal.")

    print("Removing configuration files...")
    config_file = os.path.join(project_root, "src", "prayer", "config", "config.json")
    token_file = os.path.join(project_root, "src", "prayer", "auth", "token.json")
    if os.path.exists(config_file):
        os.remove(config_file)
        print(f"Removed {config_file}")
    else:
        print(f"{config_file} not found. Skipping removal.")
    if os.path.exists(token_file):
        os.remove(token_file)
        print(f"Removed {token_file}")
    else:
        print(f"{token_file} not found. Skipping removal.")

    print("Removing log files...")
    log_file_stdout = "/tmp/prayer-player.stdout.log"
    log_file_stderr = "/tmp/prayer-player.stderr.log"
    if os.path.exists(log_file_stdout):
        os.remove(log_file_stdout)
        print(f"Removed {log_file_stdout}")
    else:
        print(f"{log_file_stdout} not found. Skipping removal.")
    if os.path.exists(log_file_stderr):
        os.remove(log_file_stderr)
        print(f"Removed {log_file_stderr}")
    else:
        print(f"{log_file_stderr} not found. Skipping removal.")

    print("Uninstallation complete.")
    print(f"The project directory '{project_root}' has not been removed. You can delete it manually if you wish.")

def main_macos_uninstall():
    print("Prayer Player Uninstallation for macOS")

    # --- 1. Unload and remove the launchd agent ---
    plist_file = os.path.expanduser("~/Library/LaunchAgents/com.prayerplayer.scheduler.plist")

    if os.path.exists(plist_file):
        print("Unloading launchd agent...")
        run_command(["launchctl", "unload", plist_file], "Unloading launchd agent", check=False)
        
        print("Removing .plist file...")
        os.remove(plist_file)
        
        print("Launchd agent removed successfully.")
    else:
        print("Launchd .plist file not found. Skipping agent removal.")

    # --- 2. Remove project files ---
    print("The following items will be removed:")
    print(" - Virtual environment (myenv/)")
    print(" - Configuration files (src/prayer/config/config.json)")
    print(" - Google Calendar token (src/prayer/auth/token.json)")
    print(" - Log files (/tmp/prayer-player.*.log)")

    confirm = input("Are you sure you want to permanently delete these files? (y/N): ")
    if confirm.lower() != 'y':
        print("Uninstallation cancelled.")
        sys.exit(0)

    project_root = os.getcwd()

    print("Removing virtual environment...")
    venv_path = os.path.join(project_root, "myenv")
    if os.path.exists(venv_path):
        subprocess.run(f"rm -rf {venv_path}", shell=True, check=True)
        print("Virtual environment removed.")
    else:
        print("Virtual environment not found. Skipping removal.")

    print("Removing configuration files...")
    config_file = os.path.join(project_root, "src", "prayer", "config", "config.json")
    token_file = os.path.join(project_root, "src", "prayer", "auth", "token.json")
    if os.path.exists(config_file):
        os.remove(config_file)
        print(f"Removed {config_file}")
    else:
        print(f"{config_file} not found. Skipping removal.")
    if os.path.exists(token_file):
        os.remove(token_file)
        print(f"Removed {token_file}")
    else:
        print(f"{token_file} not found. Skipping removal.")

    print("Removing log files...")
    log_file_stdout = "/tmp/prayer-player.stdout.log"
    log_file_stderr = "/tmp/prayer-player.stderr.log"
    if os.path.exists(log_file_stdout):
        os.remove(log_file_stdout)
        print(f"Removed {log_file_stdout}")
    else:
        print(f"{log_file_stdout} not found. Skipping removal.")
    if os.path.exists(log_file_stderr):
        os.remove(log_file_stderr)
        print(f"Removed {log_file_stderr}")
    else:
        print(f"{log_file_stderr} not found. Skipping removal.")

    print("Uninstallation complete.")
    print(f"The project directory '{project_root}' has not been removed. You can delete it manually if you wish.")

def main_windows_uninstall():
    print("Prayer Player Uninstallation for Windows")

    # --- 1. Stop and remove the Scheduled Task ---
    task_name = "PrayerPlayerScheduler"
    print(f"Attempting to unregister scheduled task '{task_name}'...")
    # PowerShell command to unregister the scheduled task
    powershell_command = f"Unregister-ScheduledTask -TaskName '{task_name}' -Confirm:$false -ErrorAction SilentlyContinue"
    run_command(["powershell.exe", "-ExecutionPolicy", "Bypass", "-Command", powershell_command],
                "Unregistering scheduled task", check=False)
    print(f"Scheduled task '{task_name}' removal attempted. Check Task Scheduler for confirmation.")

    # --- 2. Remove project files ---
    print("The following items will be removed:")
    print(" - Virtual environment (myenv/)")
    print(" - Configuration files (src/prayer/config/config.json)")
    print(" - Google Calendar token (src/prayer/auth/token.json)")

    confirm = input("Are you sure you want to permanently delete these files? (y/N): ")
    if confirm.lower() != 'y':
        print("Uninstallation cancelled.")
        sys.exit(0)

    project_root = os.getcwd()

    print("Removing virtual environment...")
    venv_path = os.path.join(project_root, "myenv")
    if os.path.exists(venv_path):
        # Use rmdir /s /q for Windows to remove directory non-interactively
        subprocess.run(["rmdir", "/s", "/q", venv_path], shell=True, check=False)
        print("Virtual environment removed.")
    else:
        print("Virtual environment not found. Skipping removal.")

    print("Removing configuration files...")
    config_file = os.path.join(project_root, "src", "prayer", "config", "config.json")
    token_file = os.path.join(project_root, "src", "prayer", "auth", "token.json")
    if os.path.exists(config_file):
        os.remove(config_file)
        print(f"Removed {config_file}")
    else:
        print(f"{config_file} not found. Skipping removal.")
    if os.path.exists(token_file):
        os.remove(token_file)
        print(f"Removed {token_file}")
    else:
        print(f"{token_file} not found. Skipping removal.")

    print("Uninstallation complete.")
    print(f"The project directory '{project_root}' has not been removed. You can delete it manually if you wish.")

if __name__ == "__main__":
    if sys.platform.startswith('linux'):
        main_linux_uninstall()
    elif sys.platform == 'darwin':
        main_macos_uninstall()
    elif sys.platform == 'win32':
        main_windows_uninstall()
    else:
        print(f"Unsupported operating system: {sys.platform}")