import os
import subprocess
import sys
import json
import venv

# Global variables to store paths to the virtual environment's python and pip
PYTHON_EXECUTABLE = sys.executable
PIP_EXECUTABLE = os.path.join(os.path.dirname(sys.executable), "pip")

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

def check_dependencies_linux():
    """Checks for Python, pip, tkinter, and ffmpeg."""
    print("--- Checking system dependencies ---")
    
    # Check for tkinter
    try:
        import tkinter
        print("tkinter is installed.")
    except ImportError:
        print("tkinter is not installed. Attempting to install python3-tk...")
        run_command(["sudo", "apt-get", "update"], "Updating apt-get")
        run_command(["sudo", "apt-get", "install", "-y", "python3-tk"], "Installing python3-tk")
        try:
            import tkinter
            print("tkinter installed successfully.")
        except ImportError:
            print("Failed to install tkinter. Please install it manually using 'sudo apt-get install python3-tk' and try again.")
            sys.exit(1)

    # Check for ffmpeg (ffplay)
    try:
        run_command(["ffplay", "-version"], "Checking for ffplay (ffmpeg)", check=False)
        print("ffplay (ffmpeg) is installed.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ffplay (from ffmpeg) is not installed. Attempting to install ffmpeg...")
        run_command(["sudo", "apt-get", "update"], "Updating apt-get")
        run_command(["sudo", "apt-get", "install", "-y", "ffmpeg"], "Installing ffmpeg")
        try:
            run_command(["ffplay", "-version"], "Verifying ffplay (ffmpeg) installation", check=False)
            print("ffmpeg installed successfully.")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Failed to install ffmpeg. Please install it manually using 'sudo apt-get install ffmpeg' and try again.")
            sys.exit(1)

    # Check for python3-gi (for GObject Introspection, used by some GUI components)
    try:
        import gi
        print("python3-gi is installed.")
    except ImportError:
        print("python3-gi is not installed. Attempting to install python3-gi...")
        run_command(["sudo", "apt-get", "update"], "Updating apt-get")
        run_command(["sudo", "apt-get", "install", "-y", "python3-gi"], "Installing python3-gi")
        try:
            import gi
            print("python3-gi installed successfully.")
        except ImportError:
            print("Failed to install python3-gi. Please install it manually using 'sudo apt-get install python3-gi' and try again.")
            sys.exit(1)

def setup_virtual_environment():
    """Creates and activates a virtual environment."""
    global PYTHON_EXECUTABLE, PIP_EXECUTABLE
    env_dir = "myenv"
    project_root = os.getcwd()
    
    if not os.path.exists(env_dir):
        print(f"--- Creating virtual environment in {env_dir} ---")
        venv.create(env_dir, with_pip=True)
        print("Virtual environment created.")
    else:
        print(f"--- Virtual environment '{env_dir}' already exists. Skipping creation. ---")

    # Set paths to the virtual environment's python and pip
    PYTHON_EXECUTABLE = os.path.join(project_root, env_dir, "bin", "python3")
    PIP_EXECUTABLE = os.path.join(project_root, env_dir, "bin", "pip")
    
    # Verify the executables exist
    if not os.path.exists(PYTHON_EXECUTABLE):
        print(f"Error: Python executable not found in virtual environment: {PYTHON_EXECUTABLE}")
        sys.exit(1)
    if not os.path.exists(PIP_EXECUTABLE):
        print(f"Error: Pip executable not found in virtual environment: {PIP_EXECUTABLE}")
        sys.exit(1)

    print("Virtual environment path set for subsequent commands.")

def install_project_dependencies_windows():
    """Installs project dependencies for Windows, including building a wheel."""
    print("--- Installing project dependencies for Windows ---")
    run_command([PIP_EXECUTABLE, "install", "--upgrade", "pip"], "Upgrading pip")

    # Ensure the 'build' package is installed
    run_command([PIP_EXECUTABLE, "install", "build"], "'build' package not found, installing...")

    # Build the wheel package
    print("--- Building the Prayer Player wheel package ---")
    run_command([PYTHON_EXECUTABLE, "-m", "build"], "Building wheel package")

    # Install the wheel package
    print("--- Installing the Prayer Player from the built wheel ---")
    dist_dir = os.path.join(os.getcwd(), "dist")
    wheel_files = [f for f in os.listdir(dist_dir) if f.endswith(".whl")]
    if not wheel_files:
        print("Error: No wheel file found in 'dist/' directory.")
        sys.exit(1)
    wheel_path = os.path.join(dist_dir, wheel_files[0])
    run_command([PIP_EXECUTABLE, "install", wheel_path], "Installing from built wheel")

    # Install requirements.txt explicitly (PowerShell script does this after wheel)
    run_command([PIP_EXECUTABLE, "install", "-r", "requirements.txt"], "Installing requirements.txt")

def check_dependencies_windows():
    """Checks for Python, pip, tkinter, and ffmpeg on Windows."""
    print("--- Checking system dependencies for Windows ---")

    # Python and pip are assumed to be present as this is a Python installer.
    # The PowerShell script checks for them, but our Python script implies their presence.

    # Check for tkinter
    try:
        import tkinter
        print("tkinter is installed.")
    except ImportError:
        print("tkinter module not found. This is required for the setup GUI.")
        print("Please ensure you have a full Python 3 installation that includes tkinter.")
        print("Consider reinstalling Python from python.org, ensuring Tkinter is selected during installation.")
        sys.exit(1)

    # Check for ffmpeg (ffplay)
    # On Windows, ffplay.exe might not be in PATH. We'll just warn.
    try:
        # Use 'where' command on Windows to find executables in PATH
        subprocess.run(["where", "ffplay.exe"], check=True, capture_output=True, text=True)
        print("ffmpeg (ffplay) is found in PATH.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: ffplay (from ffmpeg) is not found in your system's PATH.")
        print("Please install ffmpeg to enable audio playback. You can install it via Chocolatey (recommended) or manually:")
        print("  1. Install Chocolatey: Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))")
        print("  2. Then install ffmpeg: choco install ffmpeg")
        print("  Alternatively, download ffmpeg binaries from ffmpeg.org and add them to your system PATH.")
        # Do not exit, allow script to continue, but audio playback will not work without ffplay

def setup_scheduled_task():
    """Sets up the Windows Scheduled Task."""
    print("--- Setting up Prayer Player as a Scheduled Task ---")

    task_name = "PrayerPlayerScheduler"
    task_description = "Runs the Prayer Player application in the background."
    project_root = os.getcwd()
    env_dir = "myenv"

    # Determine the correct executable path within the venv for Windows
    # It could be .exe or just the script
    player_executable_base = os.path.join(project_root, env_dir, "Scripts", "prayer-player")
    player_executable = f"{player_executable_base}.exe" if os.path.exists(f"{player_executable_base}.exe") else player_executable_base

    if not os.path.exists(player_executable):
        print(f"Error: Prayer Player executable not found at {player_executable}. Cannot create scheduled task.")
        sys.exit(1)

    # PowerShell commands to create a scheduled task
    # We need to escape paths for PowerShell
    ps_player_executable = player_executable.replace("'", "''") # Escape single quotes
    ps_project_root = project_root.replace("'", "''")

    # Using PowerShell cmdlets requires admin privileges.
    # The original script assumes it might be run with admin privileges.
    # We will construct the PowerShell command and run it.
    # Note: This will likely prompt for UAC if not already running as admin.
    powershell_command = f"""
$action = New-ScheduledTaskAction -Execute '{ps_player_executable}' -WorkingDirectory '{ps_project_root}'
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:UserName
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfOnBatteries -ExecutionTimeLimit 0 -StartWhenAvailable
Register-ScheduledTask -TaskName '{task_name}' -Description '{task_description}' -Action $action -Trigger $trigger -Settings $settings -Force
"""
    # Run PowerShell command. Need to use -Command and -EncodedCommand for complex scripts.
    # For simplicity, let's try direct execution first, if it fails, we can encode.
    # It's crucial to run PowerShell with -ExecutionPolicy Bypass for scripts.
    run_command(["powershell.exe", "-ExecutionPolicy", "Bypass", "-Command", powershell_command],
                "Registering scheduled task", shell=False)

    print("Scheduled task setup complete. Prayer Player will run in the background after you log in.")
    print("To manage the task, open 'Task Scheduler' (taskschd.msc).")

def main_windows():
    print("Prayer Player Setup for Windows (Python Installer)")
    check_dependencies_windows()
    setup_virtual_environment()
    install_project_dependencies_windows()
    # Ensure a clean config state for tests
    config_file_path_for_tests = os.path.join(os.getcwd(), "src", "prayer", "config", "config.json")
    if os.path.exists(config_file_path_for_tests):
        print(f"--- Deleting existing config.json at {config_file_path_for_tests} for clean test run ---")
        os.remove(config_file_path_for_tests)
    run_tests()
    run_gui_configuration()

    config_file = os.path.join(os.getcwd(), "src", "prayer", "config", "config.json")
    run_choice = "background" # Default

    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
            run_choice = config.get("run_mode", "background")
        except json.JSONDecodeError:
            print("Warning: config.json is corrupted. Defaulting to background service.")
    else:
        print("Warning: config.json not found. Defaulting to background service.")

    if run_choice == "background":
        setup_scheduled_task()
    elif run_choice == "foreground":
        run_foreground()
    else:
        print("Invalid run mode specified in config.json. Defaulting to foreground run.")
        run_foreground()

    print("Setup script finished.")

def check_dependencies_macos():
    """Checks for Python, pip, tkinter, and ffmpeg on macOS."""
    print("--- Checking system dependencies for macOS ---")

    # Check for tkinter
    try:
        import tkinter
        print("tkinter is installed.")
    except ImportError:
        print("tkinter module not found. This is required for the setup GUI.")
        print("Please ensure you have a full Python 3 installation that includes tkinter.")
        print("If you installed Python via Homebrew, you might need to install 'python-tk': brew install python-tk")
        print("Otherwise, consider reinstalling Python from python.org.")
        sys.exit(1)

    # Check for ffmpeg (ffplay)
    try:
        run_command(["ffplay", "-version"], "Checking for ffplay (ffmpeg)", check=False)
        print("ffplay (ffmpeg) is installed.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ffplay (from ffmpeg) is not installed. Attempting to install ffmpeg using Homebrew...")
        try:
            run_command(["brew", "--version"], "Checking for Homebrew", check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Homebrew is not installed. Please install Homebrew (https://brew.sh/) to install ffmpeg, or install ffmpeg manually.")
            sys.exit(1)
        run_command(["brew", "install", "ffmpeg"], "Installing ffmpeg using Homebrew")
        try:
            run_command(["ffplay", "-version"], "Verifying ffplay (ffmpeg) installation", check=False)
            print("ffmpeg installed successfully.")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Failed to install ffmpeg. Please install it manually using 'brew install ffmpeg' and try again.")
            sys.exit(1)

def install_project_dependencies_macos():
    """Installs project dependencies for macOS, including building a wheel."""
    print("--- Installing project dependencies for macOS ---")
    run_command([PIP_EXECUTABLE, "install", "--upgrade", "pip"], "Upgrading pip")

    # Ensure the 'build' package is installed
    run_command([PIP_EXECUTABLE, "install", "build"], "'build' package not found, installing...")

    # Build the wheel package
    print("--- Building the Prayer Player wheel package ---")
    run_command([PYTHON_EXECUTABLE, "-m", "build"], "Building wheel package")

    # Install the wheel package
    print("--- Installing the Prayer Player from the built wheel ---")
    # Find the .whl file in the dist/ directory
    dist_dir = os.path.join(os.getcwd(), "dist")
    wheel_files = [f for f in os.listdir(dist_dir) if f.endswith(".whl")]
    if not wheel_files:
        print("Error: No wheel file found in 'dist/' directory.")
        sys.exit(1)
    # Assuming there's only one wheel file or we take the first one
    wheel_path = os.path.join(dist_dir, wheel_files[0])
    run_command([PIP_EXECUTABLE, "install", wheel_path], "Installing from built wheel")

def setup_launchd_service():
    """Sets up the launchd user agent."""
    print("--- Setting up Prayer Player as a launchd agent ---")

    launch_agents_dir = os.path.expanduser("~/Library/LaunchAgents/")
    os.makedirs(launch_agents_dir, exist_ok=True)

    plist_file_path = os.path.join(launch_agents_dir, "com.prayerplayer.scheduler.plist")
    project_root = os.getcwd()
    env_dir = "myenv"
    python_executable_in_venv = os.path.join(project_root, env_dir, "bin", "python3")
    main_script_path = os.path.join(project_root, "src", "prayer", "__main__.py")

    plist_content = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">
<plist version=\"1.0\">
<dict>
    <key>Label</key>
    <string>com.prayerplayer.scheduler</string>

    <key>ProgramArguments</key>
    <array>
        <string>{python_executable_in_venv}</string>
        <string>{main_script_path}</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/tmp/prayer-player.stdout.log</string>

    <key>StandardErrorPath</key>
    <string>/tmp/prayer-player.stderr.log</string>

    <key>WorkingDirectory</key>
    <string>{project_root}</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONPATH</key>
        <string>{project_root}/src</string>
    </dict>

</dict>
</plist>"""

    print(f"Creating launchd .plist file at {plist_file_path}")
    with open(plist_file_path, "w") as f:
        f.write(plist_content)

    print("Loading launchd agent...")
    run_command(["launchctl", "load", plist_file_path], "Loading launchd agent")

    print("Service setup complete. Prayer Player is now running in the background.")
    print("To check status: launchctl list | grep com.prayerplayer.scheduler")
    print(f"To unload (stop): launchctl unload \"{plist_file_path}\"")
    print(f"To load (start): launchctl load \"{plist_file_path}\"")

def main_macos():
    print("Prayer Player Setup for macOS (Python Installer)")
    check_dependencies_macos()
    setup_virtual_environment()
    install_project_dependencies_macos()
    # Ensure a clean config state for tests
    config_file_path_for_tests = os.path.join(os.getcwd(), "src", "prayer", "config", "config.json")
    if os.path.exists(config_file_path_for_tests):
        print(f"--- Deleting existing config.json at {config_file_path_for_tests} for clean test run ---")
        os.remove(config_file_path_for_tests)
    run_tests()
    run_gui_configuration()

    config_file = os.path.join(os.getcwd(), "src", "prayer", "config", "config.json")
    run_choice = "background" # Default

    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
            run_choice = config.get("run_mode", "background")
        except json.JSONDecodeError:
            print("Warning: config.json is corrupted. Defaulting to background service.")
    else:
        print("Warning: config.json not found. Defaulting to background service.")

    if run_choice == "background":
        setup_launchd_service()
    elif run_choice == "foreground":
        run_foreground()
    else:
        print("Invalid run mode specified in config.json. Defaulting to foreground run.")
        run_foreground()

    print("Setup script finished.")

def run_tests():
    """Runs project tests."""
    print("--- Running tests to verify installation ---")
    # Ensure pytest is installed in the venv
    run_command([PIP_EXECUTABLE, "install", "pytest", "pytest-mock", "pytest-qt"], "Installing pytest and its plugins if not present")
    run_command([PYTHON_EXECUTABLE, "-m", "pytest", "--ignore=test_gi.py"], "Running pytest (ignoring test_gi.py)")

def run_gui_configuration():
    """Launches the GUI for user configuration."""
    print("--- Launching the Prayer Player Setup GUI for configuration ---")
    print("Please enter your City and Country in the GUI and click 'Save Configuration'.")
    print("Also, click 'Authenticate Google Calendar' in the GUI to set up calendar integration.")
    print("After saving and authenticating, close the GUI to continue with the setup.")
    setup_gui_path = os.path.join(os.getcwd(), "setup_gui.py")
    run_command([PYTHON_EXECUTABLE, setup_gui_path], "Running setup GUI")
    print("Configuration GUI closed. Continuing with service setup...")

def setup_systemd_service():
    """Sets up the systemd user service."""
    print("--- Setting up Prayer Player as a systemd user service ---")

    service_dir = os.path.expanduser("~/.config/systemd/user/")
    os.makedirs(service_dir, exist_ok=True)

    service_file_path = os.path.join(service_dir, "prayer-player.service")
    project_root = os.getcwd()
    env_dir = "myenv"
    executable_path = os.path.join(project_root, env_dir, "bin", "prayer-player")

    service_content = f"""[Unit]
Description=Prayer Player Scheduler
After=network.target

[Service]
Type=simple
ExecStart={executable_path}
Restart=always
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
"""
    print(f"Creating service file at {service_file_path}")
    with open(service_file_path, "w") as f:
        f.write(service_content)

    print("Reloading systemd daemon and enabling service...")
    run_command(["systemctl", "--user", "daemon-reload"], "Reloading systemd daemon")
    run_command(["systemctl", "--user", "enable", "--now", "prayer-player.service"], "Enabling and starting service")

    print("Service setup complete. Prayer Player is now running in the background.")
    print("To check status: systemctl --user status prayer-player.service")
    print("To view logs: journalctl --user -u prayer-player.service -f")
    print(f"To enable running after logout: loginctl enable-linger {os.getenv('USER')}")

def run_foreground():
    """Runs the application in the foreground."""
    print("--- Running Prayer Player in the foreground ---")
    print("Press Ctrl+C to stop the application.")
    project_root = os.getcwd()
    env_dir = "myenv"
    executable_path = os.path.join(project_root, env_dir, "bin", "prayer-player")
    run_command([executable_path], "Running prayer-player in foreground", check=False) # Don't check for error as Ctrl+C is expected

def main_linux():
    print("Prayer Player Setup for Linux (Python Installer)")
    check_dependencies_linux()
    setup_virtual_environment()
    install_project_dependencies_linux()
    run_tests()
    # Ensure a clean config state for tests
    config_file_path_for_tests = os.path.join(os.getcwd(), "src", "prayer", "config", "config.json")
    if os.path.exists(config_file_path_for_tests):
        print(f"--- Deleting existing config.json at {config_file_path_for_tests} for clean test run ---")
        os.remove(config_file_path_for_tests)

    run_tests()
    run_gui_configuration()

    config_file = os.path.join(os.getcwd(), "src", "prayer", "config", "config.json")
    run_choice = "background" # Default

    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
            run_choice = config.get("run_mode", "background")
        except json.JSONDecodeError:
            print("Warning: config.json is corrupted. Defaulting to background service.")
    else:
        print("Warning: config.json not found. Defaulting to background service.")

    if run_choice == "background":
        setup_systemd_service()
    elif run_choice == "foreground":
        run_foreground()
    else:
        print("Invalid run mode specified in config.json. Defaulting to foreground run.")
        run_foreground()

    print("Setup script finished.")

if __name__ == "__main__":
    # Determine OS and call appropriate main function
    if sys.platform.startswith('linux'):
        main_linux()
    elif sys.platform == 'darwin':
        main_macos()
    elif sys.platform == 'win32':
        main_windows()
    else:
        print(f"Unsupported operating system: {sys.platform}")
