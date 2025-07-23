#!/bin/bash

# This script automates the process of building a Python application with
# PyInstaller and packaging it as a .deb file for Ubuntu/Debian-based systems.
#
# It includes cleanup, dependency installation, building the executable,
# testing the executable, and creating a well-formed Debian package.

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
# Define configuration variables here for easy management.

# The Python executable to use. Using a variable makes it easy to switch versions.
PYTHON_EXEC="python3.10"

# The user-facing name of your application.
APP_NAME="PrayerPlayer"

# The official package name. Must be lowercase, no spaces.
# Using the original 'prayer-player' name to ensure upgrades work correctly.
PACKAGE_NAME="prayer-player"

# The application version.
# IMPORTANT: Avoid hardcoding the version. It's best practice to source this
# from a single place, like a version.txt file or a git tag.
# Example using a file: VERSION=$(cat version.txt)
# Example using git: VERSION=$(git describe --tags --abbrev=0)
VERSION="1.0.1"

# Automatically detect the system architecture instead of hardcoding it.
ARCH=$(dpkg --print-architecture)

# Path to your application's main entry point script.
ENTRY_POINT="src/__main__.py"

# Path to the application icon.
ICON_PATH="src/assets/mosque.png"

# Name of the temporary directory for building the .deb structure.
DEB_STAGING_DIR="${PACKAGE_NAME}-deb-staging"

echo "--- Starting build for $APP_NAME v$VERSION ($ARCH) ---"


# --- Step 1: Clean Up Previous Builds ---
echo "--- Cleaning up previous build artifacts ---"
rm -rf build/ dist/ "$DEB_STAGING_DIR" "${APP_NAME}.spec"
# More robustly find and remove all __pycache__ directories.
find . -type d -name "__pycache__" -exec rm -r {} +
echo "Cleanup complete."


# --- Step 2: Install Dependencies ---
echo "--- Installing Python dependencies ---"
# It's good practice to ensure pip itself is up to date.
"$PYTHON_EXEC" -m pip install --upgrade pip
# Install dependencies from your requirements files.
# It's recommended to include 'pyinstaller' in your requirements-dev.txt
"$PYTHON_EXEC" -m pip install -r requirements.txt
"$PYTHON_EXEC" -m pip install -r requirements-dev.txt
echo "Dependencies installed."


# --- Step 3: Build Executable with PyInstaller ---
echo "--- Building application executable with PyInstaller ---"
# Note on --add-data: The path "src/assets:assets" copies the 'src/assets'
# directory into the bundle's top-level as a folder named 'assets'.
# Your Python code should be adjusted to look for resources in 'assets/'
# instead of 'src/assets/' at runtime.
#
# Note on --hidden-import: This flag is for modules that PyInstaller's
# static analysis might miss.
"$PYTHON_EXEC" -m PyInstaller --noconfirm --onefile --windowed \
  --name "$APP_NAME" \
  --icon "$ICON_PATH" \
  --collect-all PySide6 \
  --add-data "src/assets:assets" \
  --add-data "src/config:config" \
  --hidden-import "src.auth" \
  --hidden-import "src.calendar_api" \
  --hidden-import "src.config" \
  --hidden-import "src.platform" \
  --hidden-import "src.gui" \
  --hidden-import "src.state" \
  --hidden-import "src.tray_icon" \
  "$ENTRY_POINT"

echo "PyInstaller build complete. Executable is in: dist/$APP_NAME"


# --- Step 4: Test Application Startup (Optional but Recommended) ---
echo "--- Performing a quick startup test of the executable ---"
# This assumes your application has a '--dry-run' flag that performs a quick
# check and then exits cleanly. If not, you can adapt or remove this step.
dist/"$APP_NAME" --dry-run
echo "Startup test passed."


# --- Step 5: Prepare Debian Package Structure ---
echo "--- Preparing Debian package structure in '$DEB_STAGING_DIR' ---"
# Define paths for clarity.
INSTALL_DIR="$DEB_STAGING_DIR/usr/local/bin"
DESKTOP_DIR="$DEB_STAGING_DIR/usr/share/applications"
ICON_DIR="$DEB_STAGING_DIR/usr/share/icons/hicolor/256x256/apps"

# Create the required directory structure.
mkdir -p "$DEB_STAGING_DIR/DEBIAN"
mkdir -p "$INSTALL_DIR"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$ICON_DIR"
echo "Package structure created."


# --- Step 6: Create Debian Control File ---
echo "--- Creating DEBIAN/control file ---"
# The control file contains essential metadata for the package manager.
# The 'Depends' field is crucial for system stability. The list below is a
# reasonable starting point for a PySide6 application. To get a more accurate
# list of shared library dependencies, you can run this command on your executable:
# dpkg-shlibdeps -O dist/${APP_NAME}
cat <<EOF > "$DEB_STAGING_DIR/DEBIAN/control"
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Architecture: ${ARCH}
Maintainer: Omar <dev@omar.com>
Description: Prayer times application that plays the Adhan.
Depends: libc6, libqt6gui6, libqt6widgets6, libxcb-xinerama0
EOF
echo "Control file created."


# --- Step 7: Create Desktop Entry File ---
echo "--- Creating .desktop file for application menu ---"
# This file allows the app to be found in the desktop environment's application menu.
# The filename should be the package name with a .desktop extension.
cat <<EOF > "$DESKTOP_DIR/${PACKAGE_NAME}.desktop"
[Desktop Entry]
Name=${APP_NAME}
Comment=Prayer times application that plays the Adhan
# The 'Exec' line should point directly to the executable.
Exec=/usr/local/bin/${APP_NAME}
# The 'Icon' name should match the package name (and the icon filename without extension).
Icon=${PACKAGE_NAME}
Type=Application
Categories=Utility;
EOF
echo ".desktop file created."


# --- Step 8: Create Post-Installation Script ---
echo "--- Creating DEBIAN/postinst script ---"
# A post-install script is good practice for GUI apps to update system caches,
# ensuring the icon and menu entry appear immediately after installation.
cat <<EOF > "$DEB_STAGING_DIR/DEBIAN/postinst"
#!/bin/sh
set -e
echo "Updating icon cache..."
gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
echo "Updating desktop database..."
update-desktop-database -q || true
exit 0
EOF
echo "Post-install script created."


# --- Step 9: Copy Files and Set Permissions ---
echo "--- Copying application files and setting permissions ---"
cp "dist/$APP_NAME" "$INSTALL_DIR/"
# The destination icon filename should be the lowercase package name.
cp "$ICON_PATH" "$ICON_DIR/${PACKAGE_NAME}.png"

# Set permissions correctly and granularly.
# Directories should be 755 (rwxr-xr-x).
find "$DEB_STAGING_DIR" -type d -exec chmod 755 {} \;
# Most files should be 644 (rw-r--r--).
find "$DEB_STAGING_DIR" -type f -exec chmod 644 {} \;
# The main executable and control scripts must be executable (755).
chmod 755 "$DEB_STAGING_DIR/DEBIAN/postinst"
chmod 755 "$INSTALL_DIR/$APP_NAME"
echo "Files copied and permissions set."


# --- Step 10: Build the .deb Package ---
echo "--- Building the final .deb package ---"
dpkg-deb --build "$DEB_STAGING_DIR"

# Create a clean, descriptive name for the final artifact.
FINAL_DEB_NAME="${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
mv "${DEB_STAGING_DIR}.deb" "dist/$FINAL_DEB_NAME"

echo "--- Build process complete! ---"
echo "Final artifact created at:"
ls -l "dist/$FINAL_DEB_NAME"
echo
echo "You can now install the package using: sudo dpkg -i dist/$FINAL_DEB_NAME"
echo "After installation, run it from your application menu or with the command: ${APP_NAME}"
