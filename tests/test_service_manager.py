import unittest
from unittest.mock import patch, mock_open
import os
import sys

from src.platform.service import ServiceManager

class TestServiceManager(unittest.TestCase):

    def setUp(self):
        self.service_name = "test-prayer-player"
        self.display_name = "Test Prayer Player"
        self.description = "A test service"

    @patch('platform.system', return_value='Linux')
    @patch('os.path.exists', return_value=True)
    @patch('os.path.expanduser')
    def test_is_enabled_linux_true(self, mock_expanduser, mock_exists, mock_system):
        self.manager = ServiceManager(self.service_name, self.display_name, self.description)
        mock_expanduser.return_value = f"~/.config/autostart/{self.service_name}.desktop"
        self.assertTrue(self.manager.is_enabled())
        mock_expanduser.assert_called_with(f"~/.config/autostart/{self.service_name}.desktop")

    @patch('platform.system', return_value='Linux')
    @patch('os.path.exists', return_value=False)
    @patch('os.path.expanduser')
    def test_is_enabled_linux_false(self, mock_expanduser, mock_exists, mock_system):
        self.manager = ServiceManager(self.service_name, self.display_name, self.description)
        mock_expanduser.return_value = f"~/.config/autostart/{self.service_name}.desktop"
        self.assertFalse(self.manager.is_enabled())
        mock_expanduser.assert_called_with(f"~/.config/autostart/{self.service_name}.desktop")

    @patch('platform.system', return_value='Darwin')
    @patch('os.path.exists', return_value=True)
    @patch('os.path.expanduser')
    def test_is_enabled_macos_true(self, mock_expanduser, mock_exists, mock_system):
        self.manager = ServiceManager(self.service_name, self.display_name, self.description)
        mock_expanduser.return_value = f"~/Library/LaunchAgents/{self.service_name}.plist"
        self.assertTrue(self.manager.is_enabled())
        mock_expanduser.assert_called_with(f"~/Library/LaunchAgents/{self.service_name}.plist")

    @patch('platform.system', return_value='Darwin')
    @patch('os.path.exists', return_value=False)
    @patch('os.path.expanduser')
    def test_is_enabled_macos_false(self, mock_expanduser, mock_exists, mock_system):
        self.manager = ServiceManager(self.service_name, self.display_name, self.description)
        mock_expanduser.return_value = f"~/Library/LaunchAgents/{self.service_name}.plist"
        self.assertFalse(self.manager.is_enabled())
        mock_expanduser.assert_called_with(f"~/Library/LaunchAgents/{self.service_name}.plist")

    @patch('platform.system', return_value='Windows')
    @patch('os.path.exists', return_value=True)
    @patch.dict(os.environ, {'APPDATA': '/mock/appdata'})
    def test_is_enabled_windows_true(self, mock_exists, mock_system):
        self.manager = ServiceManager(self.service_name, self.display_name, self.description)
        mock_exists.return_value = True
        self.assertTrue(self.manager.is_enabled())
        mock_exists.assert_called_with(os.path.join('/mock/appdata', 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup', f'{self.display_name}.lnk'))

    @patch('platform.system', return_value='Windows')
    @patch('os.path.exists', return_value=False)
    @patch.dict(os.environ, {'APPDATA': '/mock/appdata'})
    def test_is_enabled_windows_false(self, mock_exists, mock_system):
        self.manager = ServiceManager(self.service_name, self.display_name, self.description)
        mock_exists.return_value = False
        self.assertFalse(self.manager.is_enabled())
        mock_exists.assert_called_with(os.path.join('/mock/appdata', 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup', f'{self.display_name}.lnk'))

    @patch('platform.system', return_value='UnsupportedOS')
    def test_is_enabled_unsupported_os(self, mock_system):
        self.manager = ServiceManager(self.service_name, self.display_name, self.description)
        self.assertFalse(self.manager.is_enabled())

    @patch('platform.system', return_value='Linux')
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    @patch('subprocess.run')
    @patch('sys.executable', new='/usr/bin/python3')
    def test_install_linux(self, mock_run, mock_open_file, mock_makedirs, mock_system):
        self.manager = ServiceManager(self.service_name, self.display_name, self.description)
        self.manager.install()
        mock_makedirs.assert_called_once_with(os.path.expanduser("~/.config/systemd/user"), exist_ok=True)
        mock_open_file.assert_called_once_with(os.path.expanduser(f"~/.config/systemd/user/{self.service_name}.service"), "w")
        mock_open_file().write.assert_called_once()
        mock_run.assert_called_once_with(["systemctl", "--user", "daemon-reload"], check=True)

    @patch('platform.system', return_value='Linux')
    @patch('os.path.exists', return_value=True)
    @patch('os.remove')
    def test_uninstall_linux(self, mock_remove, mock_exists, mock_system):
        self.manager = ServiceManager(self.service_name, self.display_name, self.description)
        self.manager.uninstall()
        mock_remove.assert_called_once_with(os.path.expanduser(f"~/.config/autostart/{self.service_name}.desktop"))

    @patch('platform.system', return_value='Linux')
    @patch('os.path.exists', return_value=False)
    @patch('os.remove')
    def test_uninstall_linux_not_exists(self, mock_remove, mock_exists, mock_system):
        self.manager = ServiceManager(self.service_name, self.display_name, self.description)
        self.manager.uninstall()
        mock_remove.assert_not_called()

    @patch('platform.system', return_value='Darwin')
    @patch('builtins.open', new_callable=mock_open)
    @patch('subprocess.run')
    @patch('os.path.expanduser')
    @patch('sys.executable', new='/usr/bin/python3')
    def test_install_macos(self, mock_expanduser, mock_run, mock_open_file, mock_system):
        self.manager = ServiceManager(self.service_name, self.display_name, self.description)
        mock_expanduser.return_value = f"~/Library/LaunchAgents/{self.service_name}.plist"
        self.manager.install()
        mock_open_file.assert_called_once_with(f"~/Library/LaunchAgents/{self.service_name}.plist", "w")
        mock_open_file().write.assert_called_once()
        mock_run.assert_called_once_with(["launchctl", "load", f"~/Library/LaunchAgents/{self.service_name}.plist"], check=True)

    @patch('platform.system', return_value='Darwin')
    @patch('os.path.exists', return_value=True)
    @patch('os.remove')
    @patch.object(ServiceManager, 'stop')
    @patch('subprocess.run')
    @patch('os.path.expanduser')
    def test_uninstall_macos(self, mock_expanduser, mock_run, mock_stop, mock_remove, mock_exists, mock_system):
        self.manager = ServiceManager(self.service_name, self.display_name, self.description)
        mock_expanduser.return_value = f"~/Library/LaunchAgents/{self.service_name}.plist"
        self.manager.uninstall()
        mock_stop.assert_called_once()
        mock_run.assert_called_once_with(["launchctl", "unload", f"~/Library/LaunchAgents/{self.service_name}.plist"], check=True)
        mock_remove.assert_called_once_with(f"~/Library/LaunchAgents/{self.service_name}.plist")

    @patch('platform.system', return_value='Darwin')
    @patch('os.path.exists', return_value=False)
    @patch('os.remove')
    @patch.object(ServiceManager, 'stop')
    @patch('subprocess.run')
    @patch('os.path.expanduser')
    def test_uninstall_macos_not_exists(self, mock_expanduser, mock_run, mock_stop, mock_remove, mock_exists, mock_system):
        self.manager = ServiceManager(self.service_name, self.display_name, self.description)
        mock_expanduser.return_value = f"~/Library/LaunchAgents/{self.service_name}.plist"
        self.manager.uninstall()
        mock_stop.assert_not_called()
        mock_run.assert_not_called()
        mock_remove.assert_not_called()

    @patch('platform.system', return_value='Windows')
    @patch('subprocess.run')
    @patch.dict(os.environ, {'APPDATA': '/mock/appdata'})
    def test_install_windows(self, mock_run, mock_system):
        self.manager = ServiceManager(self.service_name, self.display_name, self.description)
        self.manager.install()
        expected_shortcut_path = os.path.join('/mock/appdata', 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup', f'{self.display_name}.lnk')
        expected_target_path = sys.executable
        expected_program_args = ' '.join(self.manager._get_program_arguments())
        powershell_command = f"""
        $shell = New-Object -ComObject WScript.Shell
        $shortcut = $shell.CreateShortcut('{expected_shortcut_path}')
        $shortcut.TargetPath = '{expected_target_path}'
        $shortcut.Arguments = '{expected_program_args}'
        $shortcut.Save()
        """
        mock_run.assert_called_once_with(["powershell.exe", "-Command", powershell_command], check=True)

    @patch('platform.system', return_value='Windows')
    @patch('os.path.exists', return_value=True)
    @patch('os.remove')
    @patch.dict(os.environ, {'APPDATA': '/mock/appdata'})
    def test_uninstall_windows(self, mock_remove, mock_exists, mock_system):
        self.manager = ServiceManager(self.service_name, self.display_name, self.description)
        self.manager.uninstall()
        expected_shortcut_path = os.path.join('/mock/appdata', 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup', f'{self.display_name}.lnk')
        mock_remove.assert_called_once_with(expected_shortcut_path)

    @patch('platform.system', return_value='Windows')
    @patch('os.path.exists', return_value=False)
    @patch('os.remove')
    @patch.dict(os.environ, {'APPDATA': '/mock/appdata'})
    def test_uninstall_windows_not_exists(self, mock_remove, mock_exists, mock_system):
        self.manager = ServiceManager(self.service_name, self.display_name, self.description)
        self.manager.uninstall()
        mock_remove.assert_not_called()

if __name__ == '__main__':
    unittest.main()