from __future__ import annotations

import os
import platform
import subprocess
import sys


class ServiceManager:
    def __init__(self, service_name: str, service_display_name: str, service_description: str):
        self.service_name = service_name
        self.service_display_name = service_display_name
        self.service_description = service_description
        self.system = platform.system()

    def _get_executable_path(self) -> str:
        if getattr(sys, 'frozen', False):
            # Running in a PyInstaller bundle
            return sys.executable
        else:
            # Running from source
            return sys.executable

    def _get_program_arguments(self) -> list[str]:
        if getattr(sys, 'frozen', False):
            # Running in a PyInstaller bundle
            return []
        else:
            # Running from source
            return ["-m", "src.prayer"]

    def _run_command(self, command: list[str], as_root: bool = False):
        if as_root and os.geteuid() != 0:
            command.insert(0, "sudo")
        subprocess.run(command, check=True)

    def install(self):
        if self.system == "Linux":
            self._install_linux()
        elif self.system == "Darwin":
            self._install_macos()
        elif self.system == "Windows":
            self._install_windows()
        else:
            raise NotImplementedError(f"Unsupported operating system: {self.system}")

    def uninstall(self):
        if self.system == "Linux":
            self._uninstall_linux()
        elif self.system == "Darwin":
            self._uninstall_macos()
        elif self.system == "Windows":
            self._uninstall_windows()
        else:
            raise NotImplementedError(f"Unsupported operating system: {self.system}")

    def enable(self):
        if self.system == "Linux":
            self._run_command(["systemctl", "--user", "enable", self.service_name])
        elif self.system == "Darwin":
            self._run_command(["launchctl", "enable", f"gui/{os.getuid()}/{self.service_name}"])
        elif self.system == "Windows":
            self._run_command(["sc", "config", self.service_name, "start=", "auto"])

    def disable(self):
        if self.system == "Linux":
            self.uninstall() # Uninstalling the .desktop file effectively disables it
        elif self.system == "Darwin":
            plist_path = os.path.expanduser(f"~/Library/LaunchAgents/{self.service_name}.plist")
            if os.path.exists(plist_path):
                self._run_command(["launchctl", "unload", plist_path])
            self.uninstall() # Uninstall if present
        elif self.system == "Windows":
            self.uninstall() # Uninstalling the shortcut effectively disables it

    def start(self):
        if self.system == "Linux":
            self._run_command(["systemctl", "--user", "start", self.service_name])
        elif self.system == "Darwin":
            self._run_command(["launchctl", "start", self.service_name])
        elif self.system == "Windows":
            self._run_command(["sc", "start", self.service_name])

    def stop(self):
        if self.system == "Linux":
            self._run_command(["systemctl", "--user", "stop", self.service_name])
        elif self.system == "Darwin":
            self._run_command(["launchctl", "stop", self.service_name])
        elif self.system == "Windows":
            self._run_command(["sc", "stop", self.service_name])

    def is_enabled(self) -> bool:
        if self.system == "Linux":
            desktop_entry_path = os.path.expanduser(f"~/.config/autostart/{self.service_name}.desktop")
            return os.path.exists(desktop_entry_path)
        elif self.system == "Darwin":
            plist_path = os.path.expanduser(f"~/Library/LaunchAgents/{self.service_name}.plist")
            return os.path.exists(plist_path)
        elif self.system == "Windows":
            startup_folder = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
            shortcut_path = os.path.join(startup_folder, f"{self.service_display_name}.lnk")
            return os.path.exists(shortcut_path)
        return False

    def _install_linux(self):
        service_file_path = os.path.expanduser(f"~/.config/systemd/user/{self.service_name}.service")
        os.makedirs(os.path.dirname(service_file_path), exist_ok=True)
        with open(service_file_path, "w") as f:
            f.write(f"""[Unit]
Description={self.service_description}
After=network.target

[Service]
ExecStart={self._get_executable_path()} {' '.join(self._get_program_arguments())}
Restart=always
User=%i

[Install]
WantedBy=default.target
""")
        self._run_command(["systemctl", "--user", "daemon-reload"])

    def _uninstall_linux(self):
        desktop_entry_path = os.path.expanduser(f"~/.config/autostart/{self.service_name}.desktop")
        if os.path.exists(desktop_entry_path):
            os.remove(desktop_entry_path)

    def _install_macos(self):
        plist_path = os.path.expanduser(f"~/Library/LaunchAgents/{self.service_name}.plist")
        with open(plist_path, "w") as f:
            f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{self.service_name}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{self._get_executable_path()}</string>
        {''.join([f'<string>{arg}</string>' for arg in self._get_program_arguments()])}
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
""")
        self._run_command(["launchctl", "load", plist_path])

    def _uninstall_macos(self):
        plist_path = os.path.expanduser(f"~/Library/LaunchAgents/{self.service_name}.plist")
        if os.path.exists(plist_path):
            self.stop()
            self._run_command(["launchctl", "unload", plist_path])
            os.remove(plist_path)

    def _install_windows(self):
        startup_folder = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
        shortcut_path = os.path.join(startup_folder, f"{self.service_display_name}.lnk")
        target_path = self._get_executable_path()
        program_args = ' '.join(self._get_program_arguments())

        # PowerShell command to create a shortcut
        powershell_command = f"""
        $shell = New-Object -ComObject WScript.Shell
        $shortcut = $shell.CreateShortcut('{shortcut_path}')
        $shortcut.TargetPath = '{target_path}'
        $shortcut.Arguments = '{program_args}'
        $shortcut.Save()
        """
        self._run_command(["powershell.exe", "-Command", powershell_command])

    def _uninstall_windows(self):
        startup_folder = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
        shortcut_path = os.path.join(startup_folder, f"{self.service_display_name}.lnk")
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)

if __name__ == '__main__':
    # Example usage:
    manager = ServiceManager(
        service_name="prayer-player",
        service_display_name="Prayer Player",
        service_description="A service to play prayer times."
    )
    # To install: manager.install()
    # To uninstall: manager.uninstall()
    # To enable: manager.enable()
    # To disable: manager.disable()
    # To start: manager.start()
    # To stop: manager.stop()
