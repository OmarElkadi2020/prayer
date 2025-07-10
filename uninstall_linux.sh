#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

PROJECT_ROOT="$(dirname "$(realpath "$0")")"
cd "$PROJECT_ROOT"

echo "Prayer Player Uninstallation for Linux"

# --- 1. Stop and disable the systemd service ---
SERVICE_FILE="$HOME/.config/systemd/user/prayer-player.service"

if [ -f "$SERVICE_FILE" ]; then
    echo "Stopping and disabling systemd user service..."
    systemctl --user stop prayer-player.service || true 
    systemctl --user disable prayer-player.service || true
    
    echo "Removing service file..."
    rm -f "$SERVICE_FILE"
    
    echo "Reloading systemd daemon..."
    systemctl --user daemon-reload
    
    echo "Service removed successfully."
else
    echo "Systemd service file not found. Skipping service removal."
fi

# --- 2. Deactivate virtual environment if active ---
# Note: This is best-effort, as the script runs in its own shell.
if [ -n "$VIRTUAL_ENV" ]; then
    if command -v deactivate &> /dev/null; then
        echo "Deactivating virtual environment..."
        deactivate
    fi
fi

# --- 3. Remove project files ---
echo "The following items will be removed:"
echo " - Virtual environment (myenv/)"
echo " - Configuration files (src/prayer/config/config.json)"
echo " - Google Calendar token (src/prayer/auth/token.json)"
echo " - Log files (/tmp/prayer-player.*.log)"

read -p "Are you sure you want to permanently delete these files? (y/N): " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

echo "Removing virtual environment..."
rm -rf "$PROJECT_ROOT/myenv"

echo "Removing configuration files..."
rm -f "$PROJECT_ROOT/src/prayer/config/config.json"
rm -f "$PROJECT_ROOT/src/prayer/auth/token.json"

echo "Removing log files..."
rm -f /tmp/prayer-player.stdout.log
rm -f /tmp/prayer-player.stderr.log

echo "Uninstallation complete."
echo "The project directory '$PROJECT_ROOT' has not been removed. You can delete it manually if you wish."
