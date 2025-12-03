"""
JWT Token Utilities

Handles JWT token creation and verification.
Configuration loaded from config.py (AppConfig.JWT)
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt

# Import configuration from project config
from config import AppConfig


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data to encode (e.g., {"sub": user_id})
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=AppConfig.JWT.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, AppConfig.JWT.SECRET, algorithm=AppConfig.JWT.ALGORITHM)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Payload data to encode (e.g., {"sub": user_id})
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=AppConfig.JWT.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, AppConfig.JWT.SECRET, algorithm=AppConfig.JWT.ALGORITHM)


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string to verify
        token_type: Expected token type ("access" or "refresh")

    Returns:
        Decoded payload dict if valid, None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            AppConfig.JWT.SECRET,
            algorithms=[AppConfig.JWT.ALGORITHM]
        )

        # Verify token type
        if payload.get("type") != token_type:
            return None

        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
