# src/services/config_service.py
from __future__ import annotations
import logging

from src.config.security import save_config
from src.domain.config_messages import SaveConfigurationCommand, ConfigurationChangedEvent
from src.shared.event_bus import EventBus

LOG = logging.getLogger(__name__)

class ConfigService:
    def __init__(self, event_bus: EventBus):
        self._event_bus = event_bus

    def handle_save_command(self, command: SaveConfigurationCommand):
        """Handles the command to save the configuration."""
        LOG.info("Handling SaveConfigurationCommand.")
        try:
            save_config(command.config)
            self._event_bus.publish(ConfigurationChangedEvent(config=command.config))
        except Exception:
            LOG.exception("Failed to save configuration")
