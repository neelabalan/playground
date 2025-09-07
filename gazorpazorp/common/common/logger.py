import logging
import os
from logging.handlers import RotatingFileHandler

DEFAULT_LOG_FILE = os.path.join(os.path.dirname(__file__), 'app.log')

def get_logger(name, log_file=DEFAULT_LOG_FILE, level=logging.INFO):
    """Get a logger with the specified name, log file, and level. Uses a default log file if not provided."""

    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

    # Create handlers
    handler = RotatingFileHandler(log_file, maxBytes=10000, backupCount=1)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
