"""
REROUTE Logging Utilities

Simple logging setup using Python's standard logging library.
Provides sensible defaults while allowing full customization.

Usage:
    from reroute.logging import get_logger

    logger = get_logger(__name__)
    logger.info("Application started")
    logger.error("Something went wrong")
"""

import logging
import sys
from typing import Optional


def get_logger(name: str = "reroute", level: str = "INFO") -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__ or module name)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logging.Logger instance

    Usage:
        logger = get_logger(__name__)
        logger.info("Hello world")
        logger.debug("Debug information")
        logger.error("An error occurred")
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)-8s | %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, level.upper()))

    return logger


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    date_format: Optional[str] = None
):
    """
    Configure logging globally for the entire application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom log format
        date_format: Custom date format

    Usage:
        # Simple setup
        setup_logging(level="DEBUG")

        # Custom format
        setup_logging(
            level="INFO",
            format_string="%(asctime)s | %(levelname)s | %(message)s"
        )
    """
    if format_string is None:
        format_string = '[%(asctime)s] %(levelname)-8s | %(name)s - %(message)s'

    if date_format is None:
        date_format = '%Y-%m-%d %H:%M:%S'

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        datefmt=date_format,
        stream=sys.stdout,
        force=True  # Reset any existing configuration
    )


# Default REROUTE logger
reroute_logger = get_logger("reroute")


__all__ = [
    'get_logger',
    'setup_logging',
    'reroute_logger'
]
