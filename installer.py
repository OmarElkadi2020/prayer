import os
import subprocess
import sys
import venv
import shutil

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
    if sys.platform.startswith('linux') or sys.platform == 'darwin':
        PYTHON_EXECUTABLE = os.path.join(project_root, env_dir, "bin", "python3")
        PIP_EXECUTABLE = os.path.join(project_root, env_dir, "bin", "pip")
    elif sys.platform == 'win32':
        PYTHON_EXECUTABLE = os.path.join(project_root, env_dir, "Scripts", "python.exe")
        PIP_EXECUTABLE = os.path.join(project_root, env_dir, "Scripts", "pip.exe")

    # Verify the executables exist
    if not os.path.exists(PYTHON_EXECUTABLE):
        # Fallback for Windows if python3 is not the name
        if sys.platform == 'win32':
             PYTHON_EXECUTABLE = os.path.join(project_root, env_dir, "Scripts", "python.exe")
        if not os.path.exists(PYTHON_EXECUTABLE):
            print(f"Error: Python executable not found in virtual environment: {PYTHON_EXECUTABLE}")
            sys.exit(1)

    if not os.path.exists(PIP_EXECUTABLE):
        print(f"Error: Pip executable not found in virtual environment: {PIP_EXECUTABLE}")
        sys.exit(1)

    print("Virtual environment path set for subsequent commands.")

def install_project_dependencies_linux():
    """Installs project dependencies for Linux."""
    print("--- Installing project dependencies for Linux ---")
    run_command([PIP_EXECUTABLE, "install", "--upgrade", "pip"], "Upgrading pip")

    run_command([PIP_EXECUTABLE, "install", "-r", "requirements.txt"], "Installing requirements.txt")

def install_project_dependencies_macos():
    """Installs project dependencies for macOS."""
    print("--- Installing project dependencies for macOS ---")
    run_command([PIP_EXECUTABLE, "install", "--upgrade", "pip"], "Upgrading pip")

    run_command([PIP_EXECUTABLE, "install", "-r", "requirements.txt"], "Installing requirements.txt")

def install_project_dependencies_windows():
    """Installs project dependencies for Windows."""
    print("--- Installing project dependencies for Windows ---")
    run_command([PIP_EXECUTABLE, "install", "--upgrade", "pip"], "Upgrading pip")

    run_command([PIP_EXECUTABLE, "install", "-r", "requirements.txt"], "Installing requirements.txt")

def run_tests():
    """Runs project tests."""
    print("--- Running tests to verify installation ---")
    # run_command([PIP_EXECUTABLE, "install", "pytest", "pytest-mock", "pytest-qt"], "Installing pytest and its plugins")
    run_command([PYTHON_EXECUTABLE, "-m", "pytest"], "Running pytest")

def copy_credentials_file(app_name, app_author, user_data_dir_func):
    """Copies credentials.json from project root to user data directory if it exists."""
    project_root_credentials = os.path.join(os.getcwd(), 'credentials.json')
    user_data_credentials_dir = user_data_dir_func(app_name, app_author)
    user_data_credentials_path = os.path.join(user_data_credentials_dir, 'credentials.json')

    if os.path.exists(project_root_credentials):
        print(f"--- Copying credentials.json to {user_data_credentials_dir} ---")
        os.makedirs(user_data_credentials_dir, exist_ok=True)
        shutil.copy(project_root_credentials, user_data_credentials_path)
        print("credentials.json copied successfully.")
    else:
        print("--- No credentials.json found in project root. Skipping copy. ---")
        print(f"Please place your Google API credentials file at: {user_data_credentials_path}")

def show_completion_message():
    """Shows a message with instructions on how to run the application."""
    print("\n--- Installation Complete ---")
    print("To run the application, execute the appropriate command for your OS from the project root:")
    
    env_dir = "myenv"
    
    if sys.platform.startswith('linux') or sys.platform == 'darwin':
        executable_path = os.path.join(env_dir, "bin", "prayer-player")
        print(f"\nFor Linux/macOS:\n./{executable_path}\n")
    elif sys.platform == 'win32':
        executable_path = os.path.join(env_dir, "Scripts", "prayer-player.exe")
        print(f"\nFor Windows:\n{executable_path}\n")

    print("The application will start with a system tray icon.")
    print("Right-click the icon to access Settings and configure your location.")

def main_linux():
    print("Prayer Player Setup for Linux (Python Installer)")
    setup_virtual_environment()
    install_project_dependencies_linux()
    from appdirs import user_data_dir
    APP_NAME = "PrayerPlayer"
    APP_AUTHOR = "Omar"
    copy_credentials_file(APP_NAME, APP_AUTHOR, user_data_dir)
    # run_tests()
    show_completion_message()
    print("Setup script finished.")

def main_macos():
    print("Prayer Player Setup for macOS (Python Installer)")
    setup_virtual_environment()
    install_project_dependencies_macos()
    from appdirs import user_data_dir
    APP_NAME = "PrayerPlayer"
    APP_AUTHOR = "Omar"
    copy_credentials_file(APP_NAME, APP_AUTHOR, user_data_dir)
    run_tests()
    show_completion_message()
    print("Setup script finished.")

def main_windows():
    print("Prayer Player Setup for Windows (Python Installer)")
    setup_virtual_environment()
    install_project_dependencies_windows()
    from appdirs import user_data_dir
    APP_NAME = "PrayerPlayer"
    APP_AUTHOR = "Omar"
    copy_credentials_file(APP_NAME, APP_AUTHOR, user_data_dir)
    run_tests()
    show_completion_message()
    print("Setup script finished.")

VENV_DIR = "myenv"

if __name__ == "__main__":
    # Determine the path to the virtual environment's Python executable
    if sys.platform.startswith('linux') or sys.platform == 'darwin':
        VENV_PYTHON = os.path.join(os.getcwd(), VENV_DIR, "bin", "python3")
    elif sys.platform == 'win32':
        VENV_PYTHON = os.path.join(os.getcwd(), VENV_DIR, "Scripts", "python.exe")
    else:
        print(f"Unsupported operating system: {sys.platform}")
        sys.exit(1)

    # Check if we are already in the virtual environment
    if sys.executable == VENV_PYTHON:
        # We are in the venv, proceed with installation
        if sys.platform.startswith('linux'):
            main_linux()
        elif sys.platform == 'darwin':
            main_macos()
        elif sys.platform == 'win32':
            main_windows()
    else:
        # Not in venv, create it if it doesn't exist and re-execute self
        if not os.path.exists(VENV_DIR):
            print(f"--- Creating virtual environment in {VENV_DIR} ---")
            venv.create(VENV_DIR, with_pip=True)
            print("Virtual environment created.")
        else:
            print(f"--- Virtual environment '{VENV_DIR}' already exists. ---\n")

        print(f"--- Re-executing installer within virtual environment ({VENV_PYTHON}) ---")
        try:
            subprocess.run([VENV_PYTHON, __file__] + sys.argv[1:], check=True)
        except subprocess.CalledProcessError:
            print("Error: Re-execution within virtual environment failed.")
            sys.exit(1)
        sys.exit(0) # Exit the current process after re-execution
