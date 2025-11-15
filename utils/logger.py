"""
Logging configuration and utilities.
"""
import logging
import sys
from pythonjsonlogger import json as jsonlogger
from config.settings import settings


def setup_logging():
    """Configure application logging."""

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Remove existing handlers
    logger.handlers = []

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)

    # Configure formatter
    if settings.log_format == "json":
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s',
            rename_fields={"levelname": "level", "asctime": "timestamp"}
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
