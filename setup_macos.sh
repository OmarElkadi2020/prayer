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

# --- 4. Get user configuration ---
read -p "Enter your city (e.g., Deggendorf): " CITY
read -p "Enter your country (e.g., Germany): " COUNTRY

# --- 5. Choose run mode ---
echo "\nHow would you like to run Prayer Player?"
echo "1) Run in background (as a launchd agent - recommended)"
echo "2) Run in foreground (for testing or temporary use)"
read -p "Enter your choice (1 or 2): " RUN_CHOICE

if [ "$RUN_CHOICE" == "1" ]; then
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
        <string>--city</string>
        <string>$CITY</string>
        <string>--country</string>
        <string>$COUNTRY</string>
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

elif [ "$RUN_CHOICE" == "2" ]; then
    echo "Running Prayer Player in the foreground..."
    echo "Press Ctrl+C to stop the application."
    "$PROJECT_ROOT"/"$ENV_DIR"/bin/prayer-player --city "$CITY" --country "$COUNTRY"
else
    echo "Invalid choice. Please run the script again and choose 1 or 2."
    exit 1
fi

deactivate
echo "Setup script finished."
