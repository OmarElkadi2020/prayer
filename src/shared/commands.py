# src/shared/commands.py
from __future__ import annotations
from dataclasses import dataclass

class Command:
    """A base class for commands in the system."""
    pass

@dataclass(frozen=True)
class SimulatePrayerCommand(Command):
    """Command to simulate a single prayer sequence."""
    prayer_name: str