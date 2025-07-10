#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

PROJECT_ROOT="$(dirname "$(realpath "$0")")"
cd "$PROJECT_ROOT"

echo "Prayer Player Setup for macOS"

# --- 1. Check for Python and pip ---
if ! command -v python3 &> /dev/null
then
    echo "Python 3 is not installed. Please install Python 3 to proceed."
    exit 1
fi

if ! command -v pip3 &> /dev/null
then
    echo "pip3 is not installed. Please install pip3 to proceed."
    exit 1
fi

# --- 1.5. Check for Tkinter (for GUI) and FFmpeg (for audio) ---
echo "Checking for tkinter..."
if ! python3 -c "import tkinter" &> /dev/null;
then
    echo "tkinter module not found. This is required for the setup GUI."
    echo "Please ensure you have a full Python 3 installation that includes tkinter."
    echo "If you installed Python via Homebrew, you might need to install 'python-tk': brew install python-tk"
    echo "Otherwise, consider reinstalling Python from python.org."
    exit 1
fi

echo "Checking for ffmpeg (for audio playback)..."
if ! command -v ffplay &> /dev/null
then
    echo "ffplay (from ffmpeg) is not installed. Attempting to install ffmpeg using Homebrew..."
    if ! command -v brew &> /dev/null
    then
        echo "Homebrew is not installed. Please install Homebrew (https://brew.sh/) to install ffmpeg, or install ffmpeg manually."
        exit 1
    fi
    brew install ffmpeg
    if ! command -v ffplay &> /dev/null
    then
        echo "Failed to install ffmpeg. Please install it manually using 'brew install ffmpeg' and try again."
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
    echo "Setting up Prayer Player as a launchd agent..."

    # Create LaunchAgents directory if it doesn't exist
    mkdir -p "$HOME/Library/LaunchAgents/"

    PLIST_FILE="$HOME/Library/LaunchAgents/com.prayerplayer.scheduler.plist"
    PYTHON_EXECUTABLE="$(realpath "$ENV_DIR/bin/python3")"
    MAIN_SCRIPT="$(realpath "src/prayer/__main__.py")"

    # Create the .plist file content dynamically
    cat << EOF > "$PLIST_FILE"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.prayerplayer.scheduler</string>

    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_EXECUTABLE</string>
        <string>$MAIN_SCRIPT</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/tmp/prayer-player.stdout.log</n>

    <key>StandardErrorPath</key>
    <string>/tmp/prayer-player.stderr.log</string>

    <key>WorkingDirectory</key>
    <string>$PROJECT_ROOT</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONPATH</key>
        <string>$PROJECT_ROOT/src</string>
    </dict>

</dict>
</plist>
EOF

    echo "launchd .plist file created at $PLIST_FILE"

    # Load the agent
    echo "Loading launchd agent..."
    launchctl load "$PLIST_FILE"

    echo "Service setup complete. Prayer Player is now running in the background."
    echo "To check status: launchctl list | grep com.prayerplayer.scheduler"
    echo "To unload (stop): launchctl unload \"$PLIST_FILE\""
    echo "To load (start): launchctl load \"$PLIST_FILE\""

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
