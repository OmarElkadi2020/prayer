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
echo "1) Run in background (as a systemd user service - recommended)"
echo "2) Run in foreground (for testing or temporary use)"
read -p "Enter your choice (1 or 2): " RUN_CHOICE

if [ "$RUN_CHOICE" == "1" ]; then
    echo "Setting up Prayer Player as a systemd user service..."

    # Create systemd user directory if it doesn't exist
    mkdir -p ~/.config/systemd/user/

    SERVICE_FILE="~/.config/systemd/user/prayer-player.service"
    EXECUTABLE="$PROJECT_ROOT/$ENV_DIR/bin/prayer-player"

    # Create the service file content
    cat << EOF > "$SERVICE_FILE"
[Unit]
Description=Prayer Player Scheduler
After=network.target

[Service]
Type=simple
ExecStart=$EXECUTABLE --city "$CITY" --country "$COUNTRY"
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
