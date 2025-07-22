# src/shared/event_bus.py
from __future__ import annotations
import logging
from collections import defaultdict
from typing import Callable, Dict, List, Type

from src.shared.events import Event
from src.shared.commands import Command

LOG = logging.getLogger(__name__)

class EventBus:
    def __init__(self):
        self._event_subscribers: Dict[Type[Event], List[Callable]] = defaultdict(list)
        self._command_handlers: Dict[Type[Command], Callable] = {}

    def register(self, message_type: Type[Event] | Type[Command], handler: Callable):
        """
        Registers a handler for a specific message type (Event or Command).
        - Events can have multiple handlers (subscribers).
        - Commands should have only one handler.
        """
        if issubclass(message_type, Event):
            self._event_subscribers[message_type].append(handler)
            LOG.debug(f"Registered event subscriber {handler.__name__} for {message_type.__name__}")
        elif issubclass(message_type, Command):
            if message_type in self._command_handlers:
                raise ValueError(f"Command {message_type.__name__} already has a registered handler.")
            self._command_handlers[message_type] = handler
            LOG.debug(f"Registered command handler {handler.__name__} for {message_type.__name__}")
        else:
            raise TypeError("Handler must be for an Event or Command.")

    def publish(self, event: Event):
        """Publishes an event to all its registered subscribers."""
        event_type = type(event)
        LOG.info(f"Publishing event: {event_type.__name__}")
        for handler in self._event_subscribers[event_type]:
            try:
                handler(event)
            except Exception:
                LOG.exception(f"Error in event handler {handler.__name__} for {event_type.__name__}")

    def dispatch(self, command: Command):
        """Dispatches a command to its registered handler."""
        command_type = type(command)
        LOG.info(f"Dispatching command: {command_type.__name__}")
        handler = self._command_handlers.get(command_type)
        if handler:
            try:
                handler(command)
            except Exception:
                LOG.exception(f"Error in command handler {handler.__name__} for {command_type.__name__}")
        else:
            LOG.warning(f"No handler registered for command: {command_type.__name__}")
