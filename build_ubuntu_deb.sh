#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- Starting local Ubuntu .deb build process ---"

# Define project root (assuming script is run from project root)
PROJECT_ROOT=$(pwd)

# Step 0: Clean up previous builds and PyInstaller cache
echo "--- Cleaning up previous builds and PyInstaller cache ---"
rm -rf build dist *.spec __pycache__


# Step 1: Set up Python and install dependencies
echo "--- Setting up Python and installing dependencies ---"
python3.10 -m pip install --upgrade pip setuptools wheel
python3.10 -m pip install -r requirements.txt
python3.10 -m pip install -r requirements-dev.txt

# Step 2: Install PyInstaller
echo "--- Installing PyInstaller ---"
python3.10 -m pip install pyinstaller

# Step 3: Build the application executable using PyInstaller
echo "--- Building application executable with PyInstaller ---"
# Ensure the dist directory exists
mkdir -p dist

pyinstaller --noconfirm --onefile --windowed --collect-all PySide6 --collect-submodules PySide6.Qt.plugins.platforms --collect-submodules PySide6.Qt.plugins.xcbglintegrations \
  --name "PrayerPlayer" \
  --icon "src/assets/mosque.png" \
  --add-data "src/assets:src/assets" \
  --add-data "src/config:src/config" \
  --hidden-import "src.auth" \
  --hidden-import "src.calendar_api" \
  --hidden-import "src.config" \
  --hidden-import "src.platform" \
  --hidden-import "src.gui" \
  --hidden-import "src.state" \
  --hidden-import "src.tray_icon" \
  src/__main__.py

echo "PyInstaller build complete. Executable is in dist/PrayerPlayer"

# NEW STEP: Test application startup (dry run)
echo "--- Testing application startup (dry run) ---"
./dist/PrayerPlayer --dry-run

# Step 4: Build and package the Ubuntu .deb file
echo "--- Building and packaging Ubuntu .deb file ---"

# Define package details
DEB_DIR="prayer-player-deb"
VERSION="1.0.0" # IMPORTANT: Update this if your project version changes!

# Clean up previous build directory if it exists
if [ -d "${DEB_DIR}" ]; then
    echo "Removing existing ${DEB_DIR} directory..."
    rm -rf "${DEB_DIR}"
fi

# Create the Debian package structure
mkdir -p "${DEB_DIR}/DEBIAN"
mkdir -p "${DEB_DIR}/usr/local/bin"
mkdir -p "${DEB_DIR}/usr/share/applications"
mkdir -p "${DEB_DIR}/usr/share/icons/hicolor/256x256/apps"

# Create the control file
cat <<EOF > "${DEB_DIR}/DEBIAN/control"
Package: prayer-player
Version: ${VERSION}
Architecture: amd64
Maintainer: Omar <dev@omar.com>
Description: Prayer times application that plays the Adhan.
EOF

# Create the desktop entry file
cat <<EOF > "${DEB_DIR}/usr/share/applications/prayer-player.desktop"
[Desktop Entry]
Name=Prayer Player
Exec=bash -c "/usr/local/bin/PrayerPlayer"
Icon=prayer-player
Type=Application
Categories=Utility;
EOF

# Copy the application executable and icon into the package structure.
cp dist/PrayerPlayer "${DEB_DIR}/usr/local/bin/"
cp src/assets/mosque.png "${DEB_DIR}/usr/share/icons/hicolor/256x256/apps/prayer-player.png"

# Set correct permissions for the package directory.
chmod -R 755 "${DEB_DIR}"

# Build the final .deb package.
dpkg-deb --build "${DEB_DIR}"

# Move the created package to the dist folder.
mv "${DEB_DIR}.deb" "dist/prayer-player-${VERSION}-amd64.deb"

echo "--- Final .deb artifact ---"
ls -l dist/

echo "--- Ubuntu .deb build process complete ---"
echo "You can now install the .deb package using: sudo dpkg -i dist/prayer-player-${VERSION}-amd64.deb"
