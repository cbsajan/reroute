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


# =============================================================================
# Security Logging (OWASP A09: Security Logging and Monitoring)
# =============================================================================

import json
from datetime import datetime
from enum import Enum
from typing import Dict, Any


class SecurityEventType(Enum):
    """Security event types for structured logging."""
    # Authentication events
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    AUTH_LOGOUT = "auth_logout"

    # Authorization events
    AUTHZ_SUCCESS = "authz_success"
    AUTHZ_FAILURE = "authz_failure"
    AUTHZ_ROLE_DENIED = "authz_role_denied"

    # Rate limiting events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    RATE_LIMIT_WARNING = "rate_limit_warning"

    # Validation events
    VALIDATION_FAILURE = "validation_failure"
    INPUT_SANITIZED = "input_sanitized"

    # Security events
    PATH_TRAVERSAL_ATTEMPT = "path_traversal_attempt"
    INJECTION_ATTEMPT = "injection_attempt"
    SUSPICIOUS_REQUEST = "suspicious_request"

    # System events
    CONFIG_CHANGE = "config_change"
    SECURITY_ERROR = "security_error"


# Sensitive field names to redact from logs
SENSITIVE_FIELDS = {
    'password', 'passwd', 'pwd', 'secret', 'token', 'api_key', 'apikey',
    'access_token', 'refresh_token', 'authorization', 'auth', 'credential',
    'credit_card', 'card_number', 'cvv', 'ssn', 'social_security',
    'private_key', 'secret_key', 'connection_string', 'database_url'
}


def _sanitize_data(data: Any, depth: int = 0) -> Any:
    """
    Recursively sanitize sensitive data from logs.

    Args:
        data: Data to sanitize
        depth: Current recursion depth (max 10)

    Returns:
        Sanitized data with sensitive fields redacted
    """
    if depth > 10:
        return "[MAX_DEPTH]"

    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            key_lower = key.lower().replace('-', '_').replace(' ', '_')
            if any(sensitive in key_lower for sensitive in SENSITIVE_FIELDS):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = _sanitize_data(value, depth + 1)
        return sanitized
    elif isinstance(data, (list, tuple)):
        return [_sanitize_data(item, depth + 1) for item in data]
    elif isinstance(data, str):
        # Check if string looks like a credential
        if len(data) > 20 and any(c in data for c in ['=', '://']):
            # Might be a connection string or token
            for sensitive in ['password=', 'pwd=', 'secret=', 'token=', 'key=']:
                if sensitive in data.lower():
                    return "[REDACTED_STRING]"
        return data
    else:
        return data


class SecurityLogger:
    """
    Security-focused logger for OWASP A09 compliance.

    Provides structured logging of security events with:
    - Automatic sensitive data redaction
    - JSON-formatted events for SIEM integration
    - Consistent event structure
    - Severity levels aligned with security impact

    Usage:
        from reroute.logging import security_logger

        # Log authentication failure
        security_logger.log_auth_failure(
            user="john@example.com",
            reason="Invalid password",
            ip_address="192.168.1.1"
        )

        # Log rate limit exceeded
        security_logger.log_rate_limit(
            endpoint="/api/login",
            ip_address="10.0.0.1",
            limit="5/min"
        )

        # Log suspicious activity
        security_logger.log_suspicious(
            description="SQL injection attempt",
            payload="'; DROP TABLE users; --",
            ip_address="evil.attacker.com"
        )
    """

    def __init__(self, name: str = "reroute.security"):
        self._logger = logging.getLogger(name)
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '[%(asctime)s] SECURITY | %(levelname)-8s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)

    def _create_event(
        self,
        event_type: SecurityEventType,
        severity: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a structured security event."""
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type.value,
            "severity": severity,
            "message": message,
            "details": _sanitize_data(details or {})
        }
        return event

    def _log_event(
        self,
        event_type: SecurityEventType,
        severity: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a security event."""
        event = self._create_event(event_type, severity, message, details)
        event_json = json.dumps(event, default=str)

        if severity == "CRITICAL":
            self._logger.critical(event_json)
        elif severity == "HIGH":
            self._logger.error(event_json)
        elif severity == "MEDIUM":
            self._logger.warning(event_json)
        else:
            self._logger.info(event_json)

    # Authentication events
    def log_auth_success(self, user: str, ip_address: str = None, **extra) -> None:
        """Log successful authentication."""
        self._log_event(
            SecurityEventType.AUTH_SUCCESS,
            "INFO",
            f"Authentication successful for user: {user}",
            {"user": user, "ip_address": ip_address, **extra}
        )

    def log_auth_failure(self, user: str = None, reason: str = None, ip_address: str = None, **extra) -> None:
        """Log failed authentication attempt."""
        self._log_event(
            SecurityEventType.AUTH_FAILURE,
            "MEDIUM",
            f"Authentication failed: {reason or 'Unknown reason'}",
            {"user": user, "reason": reason, "ip_address": ip_address, **extra}
        )

    # Authorization events
    def log_authz_failure(self, user: str = None, resource: str = None, required_roles: list = None, ip_address: str = None, **extra) -> None:
        """Log authorization failure."""
        self._log_event(
            SecurityEventType.AUTHZ_FAILURE,
            "MEDIUM",
            f"Authorization denied for resource: {resource}",
            {"user": user, "resource": resource, "required_roles": required_roles, "ip_address": ip_address, **extra}
        )

    # Rate limiting events
    def log_rate_limit(self, endpoint: str, ip_address: str = None, limit: str = None, **extra) -> None:
        """Log rate limit exceeded."""
        self._log_event(
            SecurityEventType.RATE_LIMIT_EXCEEDED,
            "MEDIUM",
            f"Rate limit exceeded for endpoint: {endpoint}",
            {"endpoint": endpoint, "ip_address": ip_address, "limit": limit, **extra}
        )

    # Validation events
    def log_validation_failure(self, endpoint: str = None, errors: list = None, ip_address: str = None, **extra) -> None:
        """Log validation failure."""
        self._log_event(
            SecurityEventType.VALIDATION_FAILURE,
            "LOW",
            f"Validation failed for endpoint: {endpoint}",
            {"endpoint": endpoint, "errors": errors, "ip_address": ip_address, **extra}
        )

    # Security events
    def log_path_traversal(self, path: str, ip_address: str = None, **extra) -> None:
        """Log path traversal attempt."""
        self._log_event(
            SecurityEventType.PATH_TRAVERSAL_ATTEMPT,
            "HIGH",
            f"Path traversal attempt detected: {path}",
            {"attempted_path": path, "ip_address": ip_address, **extra}
        )

    def log_injection_attempt(self, injection_type: str, payload: str = None, ip_address: str = None, **extra) -> None:
        """Log injection attempt (SQL, command, etc.)."""
        self._log_event(
            SecurityEventType.INJECTION_ATTEMPT,
            "CRITICAL",
            f"Potential {injection_type} injection attempt detected",
            {"injection_type": injection_type, "payload": _sanitize_data(payload), "ip_address": ip_address, **extra}
        )

    def log_suspicious(self, description: str, ip_address: str = None, **extra) -> None:
        """Log suspicious activity."""
        self._log_event(
            SecurityEventType.SUSPICIOUS_REQUEST,
            "HIGH",
            f"Suspicious activity: {description}",
            {"description": description, "ip_address": ip_address, **extra}
        )

    def log_security_error(self, error: str, context: str = None, **extra) -> None:
        """Log security-related error."""
        self._log_event(
            SecurityEventType.SECURITY_ERROR,
            "HIGH",
            f"Security error: {error}",
            {"error": error, "context": context, **extra}
        )


# Default security logger instance
security_logger = SecurityLogger()


__all__ = [
    'get_logger',
    'setup_logging',
    'reroute_logger',
    # Security logging (OWASP A09)
    'SecurityLogger',
    'SecurityEventType',
    'security_logger',
    'SENSITIVE_FIELDS',
]
