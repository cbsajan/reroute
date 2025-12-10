"""
Security logging configuration for CLI

Provides centralized security event logging with proper formatting
and destination configuration.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional


class SecurityLoggerSetup:
    """Centralized security logger configuration"""

    def __init__(self):
        self.security_logger = None
        self.setup_complete = False

    def setup_security_logging(self, log_file: Optional[str] = None) -> None:
        """
        Setup security logging with file and console handlers.

        Args:
            log_file: Optional path to security log file
        """
        if self.setup_complete:
            return

        # Create security logger
        self.security_logger = logging.getLogger('reroute.security')
        self.security_logger.setLevel(logging.INFO)

        # Prevent propagation to avoid duplicate logs
        self.security_logger.propagate = False

        # Clear any existing handlers
        self.security_logger.handlers.clear()

        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )

        # Add console handler for security events
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
        console_handler.setFormatter(console_formatter)
        self.security_logger.addHandler(console_handler)

        # Add file handler for all security events
        if log_file is None:
            # Default security log location
            log_dir = Path.home() / '.reroute' / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / 'security.log'

        try:
            # Use rotating file handler to prevent huge log files
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(logging.INFO)  # All security events to file
            file_handler.setFormatter(detailed_formatter)
            self.security_logger.addHandler(file_handler)

        except (OSError, IOError) as e:
            # If we can't create log file, fallback to console only
            self.security_logger.warning(f"Could not create security log file: {e}")

        self.setup_complete = True

    def get_logger(self) -> logging.Logger:
        """Get the configured security logger"""
        if not self.setup_complete:
            self.setup_security_logging()
        return self.security_logger

    def log_security_event(self, event_type: str, details: str, severity: str = "INFO"):
        """
        Log a security event with proper formatting.

        Args:
            event_type: Type of security event
            details: Event details
            severity: Event severity (INFO, WARNING, ERROR, CRITICAL)
        """
        logger = self.get_logger()
        message = f"[{event_type}] {details}"

        if severity == "CRITICAL":
            logger.critical(message)
        elif severity == "ERROR":
            logger.error(message)
        elif severity == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)


# Global instance for security logging
security_logging = SecurityLoggerSetup()


def setup_security_logging(log_file: Optional[str] = None) -> None:
    """
    Setup security logging for the CLI application.

    Args:
        log_file: Optional path to security log file
    """
    security_logging.setup_security_logging(log_file)


def get_security_logger() -> logging.Logger:
    """Get the configured security logger"""
    return security_logging.get_logger()


def log_security_event(event_type: str, details: str, severity: str = "INFO") -> None:
    """
    Log a security event using the centralized security logger.

    Args:
        event_type: Type of security event
        details: Event details
        severity: Event severity (INFO, WARNING, ERROR, CRITICAL)
    """
    security_logging.log_security_event(event_type, details, severity)