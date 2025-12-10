"""
Security utilities for CLI commands

Provides secure subprocess execution and input validation
to prevent command injection vulnerabilities.
"""

import logging
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Union

# Security logger for security events
from .logging_config import log_security_event


class SecureSubprocessError(Exception):
    """Raised when secure subprocess execution fails"""
    pass


class SecurityValidationError(Exception):
    """Raised when security validation fails"""
    pass


def get_command_path(command_name: str) -> str:
    """
    Get absolute path to command to prevent PATH manipulation attacks.

    Args:
        command_name: Name of the command to find

    Returns:
        Absolute path to the command executable

    Raises:
        SecurityValidationError: If command is not found or is insecure
    """
    try:
        # Use shutil.which alternative for better security
        command_path = shlex.which(command_name)
        if not command_path:
            raise SecurityValidationError(
                f"Command '{command_name}' not found in PATH",
                "SEC001"
            )

        # Ensure the path is absolute
        command_path = os.path.abspath(command_path)

        # Additional validation: ensure command exists and is executable
        if not os.path.exists(command_path):
            raise SecurityValidationError(
                f"Command '{command_path}' does not exist",
                "SEC002"
            )

        if not os.access(command_path, os.X_OK):
            raise SecurityValidationError(
                f"Command '{command_path}' is not executable",
                "SEC003"
            )

        # Log the command resolution for security auditing
        security_logger.info(f"Command resolved: {command_name} -> {command_path}")

        return command_path

    except Exception as e:
        if isinstance(e, SecurityValidationError):
            raise
        raise SecurityValidationError(
            f"Failed to resolve command '{command_name}': {str(e)}",
            "SEC004"
        )


def validate_positive_integer(value: Union[str, int],
                            max_value: Optional[int] = None,
                            field_name: str = "value") -> int:
    """
    Validate that input is a positive integer within allowed range.

    Args:
        value: Value to validate
        max_value: Maximum allowed value (optional)
        field_name: Name of the field for error messages

    Returns:
        Validated integer value

    Raises:
        SecurityValidationError: If validation fails
    """
    try:
        # Convert to integer if string
        if isinstance(value, str):
            value = value.strip()
            if not value.isdigit():
                raise SecurityValidationError(
                    f"{field_name} must contain only digits",
                    "SEC005"
                )
            int_value = int(value)
        else:
            int_value = int(value)

        # Validate positivity
        if int_value < 1:
            raise SecurityValidationError(
                f"{field_name} must be a positive integer (>= 1)",
                "SEC006"
            )

        # Validate maximum if specified
        if max_value is not None and int_value > max_value:
            raise SecurityValidationError(
                f"{field_name} cannot exceed {max_value} for safety",
                "SEC007"
            )

        return int_value

    except ValueError:
        raise SecurityValidationError(
            f"Invalid {field_name} format: '{value}'. Must be a positive integer.",
            "SEC008"
        )
    except SecurityValidationError:
        raise
    except Exception as e:
        raise SecurityValidationError(
            f"Unexpected error validating {field_name}: {str(e)}",
            "SEC009"
        )


def validate_filename(filename: str) -> str:
    """
    Validate filename to prevent path traversal and injection attacks.

    Args:
        filename: Filename to validate

    Returns:
        Sanitized filename

    Raises:
        SecurityValidationError: If filename is invalid
    """
    if not filename:
        raise SecurityValidationError(
            "Filename cannot be empty",
            "SEC010"
        )

    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        raise SecurityValidationError(
            "Path traversal detected in filename",
            "SEC011"
        )

    # Check for dangerous characters
    dangerous_chars = ['<', '>', '|', '&', ';', '"', "'", '`', '$', '(', ')', '{', '}']
    if any(char in filename for char in dangerous_chars):
        raise SecurityValidationError(
            "Dangerous characters detected in filename",
            "SEC012"
        )

    # Ensure filename doesn't start with dot (hidden files)
    if filename.startswith('.'):
        raise SecurityValidationError(
            "Hidden filenames not allowed",
            "SEC013"
        )

    return filename


def log_security_event(event_type: str, details: str, severity: str = "WARNING"):
    """
    Log security events for monitoring and incident response.

    Args:
        event_type: Type of security event
        details: Event details
        severity: Event severity (INFO, WARNING, ERROR, CRITICAL)
    """
    message = f"[SECURITY] {event_type}: {details}"

    if severity == "CRITICAL":
        security_logger.critical(message)
    elif severity == "ERROR":
        security_logger.error(message)
    elif severity == "WARNING":
        security_logger.warning(message)
    else:
        security_logger.info(message)


def run_secure_command(command_args: List[str],
                      cwd: Optional[str] = None,
                      timeout: Optional[int] = 300,
                      capture_output: bool = True,
                      text: bool = True) -> subprocess.CompletedProcess:
    """
    Execute command securely with comprehensive protections.

    Args:
        command_args: List of command arguments (first should be absolute path)
        cwd: Working directory for command execution
        timeout: Command timeout in seconds
        capture_output: Whether to capture stdout/stderr
        text: Whether to decode output as text

    Returns:
        CompletedProcess object

    Raises:
        SecurityValidationError: If security validation fails
        SecureSubprocessError: If command execution fails
    """
    if not command_args:
        raise SecurityValidationError(
            "Command arguments cannot be empty",
            "SEC014"
        )

    # Validate command path
    command_path = command_args[0]
    if not os.path.isabs(command_path):
        raise SecurityValidationError(
            f"Command must use absolute path: {command_path}",
            "SEC015"
        )

    # Validate all arguments for injection patterns
    injection_patterns = [
        ';', '&&', '||', '|', '&', '`', '$(', '${', '$',
        '<', '>', '>>', '<<', '"', "'", '\\'
    ]

    for i, arg in enumerate(command_args[1:], 1):
        for pattern in injection_patterns:
            if pattern in arg:
                log_security_event(
                    "COMMAND_INJECTION_ATTEMPT",
                    f"Blocked argument with injection pattern: arg[{i}]='{arg}', pattern='{pattern}'",
                    "CRITICAL"
                )
                raise SecurityValidationError(
                    f"Command argument contains dangerous pattern: {pattern}",
                    "SEC016"
                )

    # Set default working directory if not specified
    if cwd is None:
        cwd = os.getcwd()

    # Validate working directory
    if not os.path.exists(cwd):
        raise SecurityValidationError(
            f"Working directory does not exist: {cwd}",
            "SEC017"
        )

    try:
        # Log command execution for security auditing
        command_str = ' '.join(shlex.quote(arg) for arg in command_args)
        log_security_event(
            "COMMAND_EXECUTION",
            f"Executing command: {command_str} in {cwd}",
            "INFO"
        )

        # Execute command with security controls
        result = subprocess.run(
            command_args,
            cwd=cwd,
            timeout=timeout,
            capture_output=capture_output,
            text=text,
            check=False  # We'll handle return codes ourselves
        )

        # Log command completion
        log_security_event(
            "COMMAND_COMPLETED",
            f"Command completed with return code: {result.returncode}",
            "INFO"
        )

        return result

    except subprocess.TimeoutExpired:
        log_security_event(
            "COMMAND_TIMEOUT",
            f"Command timed out after {timeout} seconds: {command_str}",
            "ERROR"
        )
        raise SecureSubprocessError(
            f"Command timed out after {timeout} seconds",
            "SEC018"
        )
    except Exception as e:
        log_security_event(
            "COMMAND_EXECUTION_ERROR",
            f"Command execution failed: {str(e)} - {command_str}",
            "ERROR"
        )
        raise SecureSubprocessError(
            f"Command execution failed: {str(e)}",
            "SEC019"
        )


def run_alembic_command(args: List[str],
                       cwd: Optional[str] = None,
                       timeout: int = 300) -> subprocess.CompletedProcess:
    """
    Execute alembic commands securely.

    Args:
        args: Alembic command arguments (without 'alembic')
        cwd: Working directory for command execution
        timeout: Command timeout in seconds

    Returns:
        CompletedProcess object
    """
    # Get secure alembic path
    alembic_path = get_command_path('alembic')

    # Construct secure command
    command_args = [alembic_path] + args

    # Execute with security controls
    return run_secure_command(command_args, cwd=cwd, timeout=timeout)