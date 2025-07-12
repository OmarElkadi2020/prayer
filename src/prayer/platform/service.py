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
            self._run_command(["systemctl", "--user", "disable", self.service_name])
        elif self.system == "Darwin":
            self._run_command(["launchctl", "disable", f"gui/{os.getuid()}/{self.service_name}"])
        elif self.system == "Windows":
            self._run_command(["sc", "config", self.service_name, "start=", "disabled"])

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
        service_file_path = os.path.expanduser(f"~/.config/systemd/user/{self.service_name}.service")
        if os.path.exists(service_file_path):
            self.stop()
            self.disable()
            os.remove(service_file_path)
            self._run_command(["systemctl", "--user", "daemon-reload"])

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
        # This is a simplified version. A real implementation might need to use pywin32 or similar libraries.
        executable_path = self._get_executable_path()
        program_args = ' '.join(self._get_program_arguments())
        command = [
            "sc", "create", self.service_name,
            "binPath=", f'"{executable_path}" {program_args}',
            "DisplayName=", self.service_display_name,
            "start=", "auto"
        ]
        self._run_command(command, as_root=True)

    def _uninstall_windows(self):
        self.stop()
        self._run_command(["sc", "delete", self.service_name], as_root=True)

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
