"""
REROUTE Security Utilities

Provides cryptographic and validation utilities for secure application development.
This module offers secure password hashing, JWT token management, input validation,
and sanitization helpers.
"""

from .crypto import (
    hash_password,
    verify_password,
    generate_jwt_token,
    verify_jwt_token,
    decode_jwt_token,
    generate_secret_key,
    generate_reset_token,
    generate_api_key,
    generate_session_id,
    Argon2Config,
)

from .validation import (
    validate_email,
    validate_url,
    sanitize_html,
    sanitize_filename,
    check_password_strength,
    ValidationResult,
    PasswordStrength,
)

__all__ = [
    # Crypto
    "hash_password",
    "verify_password",
    "generate_jwt_token",
    "verify_jwt_token",
    "decode_jwt_token",
    "generate_secret_key",
    "generate_reset_token",
    "generate_api_key",
    "generate_session_id",
    "Argon2Config",
    # Validation
    "validate_email",
    "validate_url",
    "sanitize_html",
    "sanitize_filename",
    "check_password_strength",
    "ValidationResult",
    "PasswordStrength",
]
