# src/domain/config_messages.py
from __future__ import annotations
from dataclasses import dataclass

from src.shared.commands import Command
from src.shared.events import Event
from src.config.schema import Config

@dataclass
class SaveConfigurationCommand(Command):
    """Command to save the application configuration."""
    config: Config

@dataclass
class ConfigurationChangedEvent(Event):
    """Event published when the application configuration has changed."""
    config: Config
