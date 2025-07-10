#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

PROJECT_ROOT="$(dirname "$(realpath "$0")")"
cd "$PROJECT_ROOT"

echo "Prayer Player Setup for Linux"

# --- 1. Check for Python and pip ---
if ! command -v python3 &> /dev/null
then
    echo "Python 3 is not installed. Please install Python 3 to proceed."
    exit 1
fi

if ! command -v pip3 &> /dev/null
then
    echo "pip3 is not installed. Please install pip3 (usually python3-pip package) to proceed."
    exit 1
fi

# --- 1.5. Check for Tkinter (for GUI) and FFmpeg (for audio) ---
echo "Checking for tkinter..."
if ! python3 -c "import tkinter" &> /dev/null;
then
    echo "tkinter is not installed. Attempting to install python3-tk..."
    sudo apt-get update
    sudo apt-get install -y python3-tk
    if ! python3 -c "import tkinter" &> /dev/null;
    then
        echo "Failed to install tkinter. Please install it manually using 'sudo apt-get install python3-tk' and try again."
        exit 1
    fi
    echo "tkinter installed successfully."
fi

echo "Checking for ffmpeg (for audio playback)..."
if ! command -v ffplay &> /dev/null
then
    echo "ffplay (from ffmpeg) is not installed. Attempting to install ffmpeg..."
    sudo apt-get update
    sudo apt-get install -y ffmpeg
    if ! command -v ffplay &> /dev/null
    then
        echo "Failed to install ffmpeg. Please install it manually using 'sudo apt-get install ffmpeg' and try again."
        exit 1
    fi
    echo "ffmpeg installed successfully."
fi

# --- 2. Create and activate virtual environment ---
ENV_DIR="myenv"
if [ ! -d "$ENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$ENV_DIR"
fi

source "$ENV_DIR"/bin/activate
echo "Virtual environment activated."

# --- 3. Install project dependencies ---
echo "Installing project dependencies..."
pip install --upgrade pip
pip install -e .
pip install -r requirements.txt

# --- 4. User Configuration via GUI ---
echo "Launching the Prayer Player Setup GUI for configuration..."
echo "Please enter your City and Country in the GUI and click 'Save Configuration'."
echo "Also, click 'Authenticate Google Calendar' in the GUI to set up calendar integration."
echo "After saving and authenticating, close the GUI to continue with the setup."

# Launch the GUI and wait for it to close
python3 "$PROJECT_ROOT"/setup_gui.py

echo "Configuration GUI closed. Continuing with service setup..."

# --- 5. Apply run mode based on GUI configuration ---

# Load the configuration saved by the GUI
CONFIG_FILE="$PROJECT_ROOT/src/prayer/config/config.json"
if [ -f "$CONFIG_FILE" ]; then
    RUN_CHOICE=$(python3 -c "import json; f=open('$CONFIG_FILE'); config=json.load(f); f.close(); print(config.get('run_mode', 'background'))")
else
    echo "Warning: config.json not found. Defaulting to background service."
    RUN_CHOICE="background"
fi

if [ "$RUN_CHOICE" == "background" ]; then
    echo "Setting up Prayer Player as a systemd user service..."

    # Create systemd user directory if it doesn't exist
    mkdir -p ~/.config/systemd/user/

    SERVICE_FILE="$HOME/.config/systemd/user/prayer-player.service"
    EXECUTABLE="$PROJECT_ROOT/$ENV_DIR/bin/prayer-player"

    # Create the service file content
    cat << EOF > "$SERVICE_FILE"
[Unit]
Description=Prayer Player Scheduler
After=network.target

[Service]
Type=simple
ExecStart=$EXECUTABLE
Restart=always
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

    echo "Service file created at $SERVICE_FILE"

    # Enable and start the service
    echo "Reloading systemd daemon and enabling service..."
    systemctl --user daemon-reload
    systemctl --user enable --now prayer-player.service

    echo "Service setup complete. Prayer Player is now running in the background."
    echo "To check status: systemctl --user status prayer-player.service"
    echo "To view logs: journalctl --user -u prayer-player.service -f"
    echo "To enable running after logout: loginctl enable-linger $USER"

elif [ "$RUN_CHOICE" == "foreground" ]; then
    echo "Running Prayer Player in the foreground..."
    echo "Press Ctrl+C to stop the application."
    "$PROJECT_ROOT"/"$ENV_DIR"/bin/prayer-player
else
    echo "Invalid run mode specified in config.json. Defaulting to foreground run."
    echo "Running Prayer Player in the foreground..."
    echo "Press Ctrl+C to stop the application."
    "$PROJECT_ROOT"/"$ENV_DIR"/bin/prayer-player
fi

deactivate
echo "Setup script finished."
