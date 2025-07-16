
from PySide6.QtCore import QTimer
import logging

LOG = logging.getLogger(__name__)

def run_in_qt_thread(target_func):
    """Decorator to ensure a function runs in the Qt GUI thread."""
    def wrapper(*args, **kwargs):
        LOG.debug(f"Scheduling {target_func.__name__} on Qt thread.")
        QTimer.singleShot(0, lambda: target_func(*args, **kwargs))
    return wrapper
