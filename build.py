
import os
import sys
import subprocess
import shutil
import argparse
from PIL import Image

from src.__version__ import __version__ as VERSION

# --- Configuration ---
APP_NAME = "PrayerPlayer"
PACKAGE_NAME = "prayer-player"
ENTRY_POINT = "src/__main__.py"
ICON_PATH_PNG = "src/assets/mosque.png"
ICON_PATH_ICO = "src/assets/mosque.ico" # New ICO path
DEB_STAGING_DIR = f"{PACKAGE_NAME}-deb-staging"

def clean():
    """Remove previous build artifacts."""
    print("--- Cleaning up previous build artifacts ---")
    shutil.rmtree("build", ignore_errors=True)
    shutil.rmtree("dist", ignore_errors=True)
    shutil.rmtree(DEB_STAGING_DIR, ignore_errors=True)
    if os.path.exists(f"{APP_NAME}.spec"):
        os.remove(f"{APP_NAME}.spec")
    for root, dirs, files in os.walk("."):
        if "__pycache__" in dirs:
            shutil.rmtree(os.path.join(root, "__pycache__"))
    print("Cleanup complete.")

def install_dependencies():
    """Install Python dependencies."""
    print("--- Installing Python dependencies ---")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "--verbose"], check=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--verbose"], check=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements-dev.txt", "--verbose"], check=True)
    print("Dependencies installed.")

def create_google_config(google_client_config_json_content=None):
    """Create the Google client config file from provided content or environment variable."""
    print("--- Creating Google Client Config ---")
    config_content = google_client_config_json_content or os.getenv("GOOGLE_CLIENT_CONFIG_JSON")
    if config_content:
        config_path = "src/config/security"
        os.makedirs(config_path, exist_ok=True)
        with open(os.path.join(config_path, "google_client_config.json"), "w") as f:
            f.write(config_content)
        print("Google client config file created.")
    else:
        print("No Google client config content provided. Skipping creation.")

def build_executable():
    """Build the application executable with PyInstaller."""
    print(f"--- Building application executable for {sys.platform} ---")

    pyinstaller_command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
    ]

    if sys.platform == "darwin":
        pyinstaller_command.append("PrayerPlayer-mac.spec")
    else:
        if sys.platform == "win32":
            convert_png_to_ico(ICON_PATH_PNG, ICON_PATH_ICO)
            icon_to_use = ICON_PATH_ICO
        else: # Linux
            icon_to_use = ICON_PATH_PNG

        pyinstaller_command.extend([
            "--name", APP_NAME,
            "--icon", icon_to_use,
            "--add-data", "src/assets:assets",
            "--add-data", "src/config:config",
            "--hidden-import", "src.auth",
            "--hidden-import", "src.calendar_api",
            "--hidden-import", "src.config",
            "--hidden-import", "src.platform",
            "--hidden-import", "src.gui",
            "--hidden-import", "src.state",
            "--hidden-import", "src.tray_icon",
        ])
        if sys.platform == "win32":
            pyinstaller_command.extend(["--windowed"])
        else: # Linux
            pyinstaller_command.extend(["--onefile", "--windowed"])
        pyinstaller_command.append(ENTRY_POINT)


    subprocess.run(pyinstaller_command, check=True)
    print("PyInstaller build complete.")

def convert_png_to_ico(png_path, ico_path):
    """Converts a PNG image to an ICO format."""
    print(f"--- Converting {png_path} to {ico_path} ---")
    try:
        img = Image.open(png_path)
        # ICO files typically support multiple sizes. We'll save a common size.
        # Inno Setup can use a single ICO file with multiple resolutions.
        img.save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
        print("Conversion successful.")
    except Exception as e:
        print(f"Error converting PNG to ICO: {e}")
        sys.exit(1)

def package_application():
    """Package the application for the current operating system."""
    print(f"--- Packaging application for {sys.platform} ---")
    if sys.platform == "linux":
        package_deb()
    elif sys.platform == "darwin":
        package_dmg()
    elif sys.platform == "win32":
        package_iss()
    else:
        print(f"Packaging not implemented for {sys.platform}")

def package_deb():
    """Create a .deb package for Ubuntu/Debian."""
    print("--- Creating .deb package ---")
    arch = subprocess.check_output(["dpkg", "--print-architecture"]).strip().decode()
    
    # Create package structure
    os.makedirs(os.path.join(DEB_STAGING_DIR, "DEBIAN"), exist_ok=True)
    install_dir = os.path.join(DEB_STAGING_DIR, "usr", "local", "bin")
    os.makedirs(install_dir, exist_ok=True)
    desktop_dir = os.path.join(DEB_STAGING_DIR, "usr", "share", "applications")
    os.makedirs(desktop_dir, exist_ok=True)
    icon_dir = os.path.join(DEB_STAGING_DIR, "usr", "share", "icons", "hicolor", "256x256", "apps")
    os.makedirs(icon_dir, exist_ok=True)

    # Create control file
    with open(os.path.join(DEB_STAGING_DIR, "DEBIAN", "control"), "w") as f:
        f.write(f"""Package: {PACKAGE_NAME}
Version: {VERSION}
Architecture: {arch}
Maintainer: Omar <dev@omar.com>
Description: Prayer times application that plays the Adhan.
Depends: libc6, libqt6gui6, libqt6widgets6, libxcb-xinerama0
""")

    # Create post-installation script
    with open(os.path.join(DEB_STAGING_DIR, "DEBIAN", "postinst"), "w") as f:
        f.write("""#!/bin/sh
set -e
echo "Updating icon cache..."
gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
echo "Updating desktop database..."
update-desktop-database -q || true
exit 0
""")
    os.chmod(os.path.join(DEB_STAGING_DIR, "DEBIAN", "postinst"), 0o755)

    # Create desktop entry
    with open(os.path.join(desktop_dir, f"{PACKAGE_NAME}.desktop"), "w") as f:
        f.write(f"""[Desktop Entry]
Name={APP_NAME}
Exec=/usr/local/bin/{APP_NAME}
Icon={PACKAGE_NAME}
Type=Application
Categories=Utility;
""")

    # Copy application files
    shutil.copy(os.path.join("dist", APP_NAME), install_dir)
    shutil.copy(ICON_PATH_PNG, os.path.join(icon_dir, f"{PACKAGE_NAME}.png"))
    shutil.copy(ICON_PATH_ICO, os.path.join(icon_dir, f"{PACKAGE_NAME}.ico"))

    # Copy Google client config to system-wide config directory
    system_config_dir = os.path.join(DEB_STAGING_DIR, "usr", "share", PACKAGE_NAME, "config", "security")
    os.makedirs(system_config_dir, exist_ok=True)
    shutil.copy(os.path.join("src", "config", "security", "google_client_config.json"), system_config_dir)

    # Build the package
    subprocess.run(["dpkg-deb", "--build", DEB_STAGING_DIR], check=True)
    os.rename(f"{DEB_STAGING_DIR}.deb", os.path.join("dist", f"{PACKAGE_NAME}_{VERSION}_{arch}.deb"))
    print(".deb package created.")

def package_dmg():
    """Create a .dmg package for macOS."""
    print("--- Creating .dmg package ---")
    subprocess.run(["brew", "install", "create-dmg"], check=True)
    subprocess.run([
        "create-dmg",
        "--volname", f"{APP_NAME} Installer",
        "--window-pos", "200", "120",
        "--window-size", "800", "400",
        "--icon-size", "100",
        "--icon", f"{APP_NAME}.app", "200", "190",
        "--hide-extension", f"{APP_NAME}.app",
        "--app-drop-link", "600", "185",
        os.path.join("dist", f"{APP_NAME}.dmg"),
        os.path.join("dist", f"{APP_NAME}.app"),
    ], check=True)
    print(".dmg package created.")

def package_iss():
    """Create a .exe installer using Inno Setup."""
    print("--- Creating Windows installer ---")
    subprocess.run(["choco", "install", "innosetup", "--no-progress"], check=True)
    result = subprocess.run(["iscc", "deployment/windows/setup.iss"], capture_output=True, text=True)
    print("Inno Setup STDOUT:")
    print(result.stdout)
    print("Inno Setup STDERR:")
    print(result.stderr)
    result.check_returncode() # This will raise an exception if the command failed
    print("Windows installer created.")


def main():
    parser = argparse.ArgumentParser(description="Build script for PrayerPlayer.")
    parser.add_argument("command", nargs="?", choices=["clean", "deps", "build", "package", "all"], help="The command to execute.")
    parser.add_argument("--release", action="store_true", help="Perform a full release build (all steps).")

    parser.add_argument("--google-client-config", help="Content of google_client_config.json for direct injection.")

    args = parser.parse_args()

    if args.release:
        clean()
        install_dependencies()
        create_google_config(args.google_client_config)
        build_executable()
        package_application()
    elif args.command:
        if args.command == "clean":
            clean()
        elif args.command == "deps":
            install_dependencies()
        elif args.command == "build":
            create_google_config(args.google_client_config)
            build_executable()
        elif args.command == "package":
            package_application()
        elif args.command == "all":
            clean()
            install_dependencies()
            create_google_config(args.google_client_config)
            build_executable()
            package_application()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
