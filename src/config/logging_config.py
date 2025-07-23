import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(log_file_path: str, level=logging.INFO):
    """
    Sets up centralized logging for the application.

    Args:
        log_file_path: The absolute path to the log file.
        level: The minimum logging level to capture (e.g., logging.INFO, logging.DEBUG).
    """
    # Ensure the log directory exists
    log_dir = os.path.dirname(log_file_path)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear existing handlers to prevent duplicate logs in case of re-configuration
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File Handler (Rotating)
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=1024 * 1024 * 5,  # 5 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Suppress googleapiclient's INFO logs if not in DEBUG mode
    if level > logging.DEBUG:
        logging.getLogger('googleapiclient.discovery').setLevel(logging.WARNING)
        logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.WARNING)

# You can also define a global logger instance if preferred, but it's often better
# to get a logger by name in each module: logging.getLogger(__name__)
# For simplicity, we'll just use the root logger for now.
