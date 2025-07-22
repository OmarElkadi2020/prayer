import unittest
from unittest.mock import Mock, patch

from src.services.config_service import ConfigService
from src.domain.config_messages import SaveConfigurationCommand, ConfigurationChangedEvent
from src.config.schema import Config

class TestConfigService(unittest.TestCase):

    def setUp(self):
        self.mock_event_bus = Mock()
        self.config_service = ConfigService(event_bus=self.mock_event_bus)

    @patch('src.services.config_service.save_config', autospec=True)
    def test_handle_save_command(self, mock_save_config):
        mock_config = Mock(spec=Config)
        command = SaveConfigurationCommand(config=mock_config)

        self.config_service.handle_save_command(command)

        mock_save_config.assert_called_once_with(command.config)
        self.mock_event_bus.publish.assert_called_once_with(ConfigurationChangedEvent(config=command.config))

if __name__ == '__main__':
    unittest.main()
