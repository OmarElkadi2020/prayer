
from PySide6.QtCore import QTimer
import logging

LOG = logging.getLogger(__name__)

def run_in_qt_thread(target_func):
    """
    Decorator to ensure a function runs in the Qt GUI thread.

    This decorator is crucial for maintaining thread safety in a Qt application.
    Any function that directly or indirectly modifies the GUI (e.g., updating
    widgets, showing windows) should be decorated with this to ensure that
    the operation is queued to be executed on the main Qt event loop.

    Usage:
        @run_in_qt_thread
        def my_gui_update_function():
            my_label.setText("Updated from another thread!")
    """
    def wrapper(*args, **kwargs):
        LOG.debug(f"Scheduling {target_func.__name__} on Qt thread.")
        QTimer.singleShot(0, lambda: target_func(*args, **kwargs))
    return wrapper
