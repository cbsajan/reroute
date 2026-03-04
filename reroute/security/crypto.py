"""
Cryptographic Utilities for REROUTE

Provides secure password hashing, JWT token management, and
cryptographically secure random token generation.
"""

from __future__ import annotations  # Enable postponed evaluation of annotations

from typing import Optional, Dict, Any, List, TYPE_CHECKING
from dataclasses import dataclass
import secrets
import time
import hashlib

if TYPE_CHECKING:
    from argon2 import PasswordHasher

# Optional dependencies - will be imported when needed
try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, Argon2Error
    ARGON2_AVAILABLE = True
except ImportError:
    ARGON2_AVAILABLE = False

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False


@dataclass
class Argon2Config:
    """Argon2 password hashing configuration.

    Attributes:
        time_cost: Number of iterations (increases security and time)
        memory_cost: Memory cost in KiB (64 MB = 65536)
        parallelism: Number of parallel threads
        hash_len: Length of the hash in bytes
        salt_len: Length of the salt in bytes
    """
    time_cost: int = 3
    memory_cost: int = 65536  # 64 MB
    parallelism: int = 4
    hash_len: int = 32
    salt_len: int = 16


def _get_password_hasher(config: Argon2Config = None) -> PasswordHasher:
    """Get configured PasswordHasher instance.

    Args:
        config: Argon2 configuration

    Returns:
        PasswordHasher instance

    Raises:
        ImportError: If argon2-cffi is not installed
    """
    if not ARGON2_AVAILABLE:
        raise ImportError(
            "argon2-cffi is required for password hashing. "
            "Install it with: pip install reroute[security]"
        )

    if config is None:
        config = Argon2Config()

    return PasswordHasher(
        time_cost=config.time_cost,
        memory_cost=config.memory_cost,
        parallelism=config.parallelism,
        hash_len=config.hash_len,
        salt_len=config.salt_len,
    )


def hash_password(
    password: str,
    config: Argon2Config = None,
    pepper: str = None
) -> str:
    """Hash password using Argon2id.

    Argon2id is a memory-hard key derivation function that provides
    excellent protection against GPU/ASIC attacks. It's the winner of
    the Password Hashing Competition (2015).

    Args:
        password: Plain-text password to hash
        config: Argon2 configuration (uses defaults if None)
        pepper: Optional secret pepper (application-wide secret added to password)
                NOTE: Pepper must be stored securely, not in code!

    Returns:
        Argon2 hash string (includes algorithm, version, and parameters)

    Raises:
        ImportError: If argon2-cffi is not installed
        ValueError: If password is empty

    Example:
        >>> hash = hash_password("my_secure_password")
        >>> print(hash)
        $argon2id$v=19$m=65536,t=3,p=4$...

    Security Note:
        - Use a pepper for additional security (stored separately from database)
        - Pepper should be at least 32 bytes of cryptographically random data
        - Never log passwords or hashes
        - Use HTTPS to prevent password interception
    """
    if not password:
        raise ValueError("Password cannot be empty")

    if pepper:
        password = password + pepper

    hasher = _get_password_hasher(config)
    return hasher.hash(password)


def verify_password(
    password: str,
    hashed: str,
    pepper: str = None
) -> bool:
    """Verify password against Argon2 hash.

    This function provides timing-attack resistant password verification
    by using constant-time comparison from argon2-cffi.

    Args:
        password: Plain-text password to verify
        hashed: Argon2 hash string (from hash_password)
        pepper: Optional secret pepper (must match pepper used in hash_password)

    Returns:
        True if password matches hash, False otherwise

    Raises:
        ImportError: If argon2-cffi is not installed

    Example:
        >>> hash = hash_password("my_secure_password")
        >>> verify_password("my_secure_password", hash)
        True
        >>> verify_password("wrong_password", hash)
        False

    Security Note:
        - This function is timing-attack resistant
        - Failed verifications should still return quickly to prevent timing attacks
        - Consider implementing rate limiting for login attempts
        - Log failed attempts for security monitoring
    """
    if not ARGON2_AVAILABLE:
        raise ImportError(
            "argon2-cffi is required for password hashing. "
            "Install it with: pip install reroute[security]"
        )

    try:
        if pepper:
            password = password + pepper

        hasher = _get_password_hasher()
        hasher.verify(hashed, password)
        return True
    except (VerifyMismatchError, Argon2Error):
        return False


def generate_jwt_token(
    payload: Dict[str, Any],
    secret: str,
    expiry_seconds: int = 3600,
    algorithm: str = "HS256",
    additional_claims: Dict[str, Any] = None
) -> str:
    """Generate JWT (JSON Web Token) for authentication.

    JWTs are used for stateless authentication. The token contains encoded
    claims that can be verified without database access.

    Args:
        payload: Custom claims to include in token (e.g., user_id, email)
                 Reserved claims: 'exp', 'iat', 'nbf', 'iss', 'sub', 'aud'
        secret: Secret key for signing (keep secure!)
        expiry_seconds: Token lifetime in seconds (default: 1 hour)
        algorithm: Signing algorithm (HS256=HMAC-SHA256, RS256=RSA-SHA256)
        additional_claims: Additional standard JWT claims (e.g., iss, aud)

    Returns:
        Encoded JWT token string

    Raises:
        ImportError: If pyjwt is not installed
        ValueError: If secret is empty

    Example:
        >>> token = generate_jwt_token(
        ...     {"user_id": 123, "email": "user@example.com"},
        ...     secret="your-secret-key",
        ...     expiry_seconds=3600
        ... )
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

    Security Note:
        - Keep secret key secure and at least 32 bytes
        - Use RS256 (asymmetric) for distributed systems
        - Set appropriate expiry (shorter is more secure)
        - Include 'sub' (subject) and 'iss' (issuer) claims
        - Never include sensitive data in JWT (can be decoded)
        - Use HTTPS to prevent token interception
    """
    if not JWT_AVAILABLE:
        raise ImportError(
            "PyJWT is required for JWT token generation. "
            "Install it with: pip install reroute[security]"
        )

    if not secret:
        raise ValueError("Secret key cannot be empty")

    # Prepare the payload
    token_payload = payload.copy()

    # Add expiry time
    token_payload['exp'] = int(time.time()) + expiry_seconds
    token_payload['iat'] = int(time.time())

    # Add additional standard claims
    if additional_claims:
        token_payload.update(additional_claims)

    # Generate token
    token = jwt.encode(token_payload, secret, algorithm=algorithm)

    # PyJWT 2.x returns bytes in some cases
    if isinstance(token, bytes):
        token = token.decode('utf-8')

    return token


def verify_jwt_token(
    token: str,
    secret: str,
    algorithms: List[str] = None,
    issuer: str = None,
    audience: str = None
) -> Dict[str, Any]:
    """Verify and decode JWT token.

    Args:
        token: JWT token string to verify
        secret: Secret key for verification (must match generation secret)
        algorithms: Allowed signing algorithms (default: ["HS256"])
                   IMPORTANT: Always specify this to prevent algorithm confusion attacks
        issuer: Expected issuer claim (optional validation)
        audience: Expected audience claim (optional validation)

    Returns:
        Decoded token payload as dictionary

    Raises:
        ImportError: If pyjwt is not installed
        jwt.InvalidTokenError: If token is invalid, expired, or signature mismatch

    Example:
        >>> token = generate_jwt_token({"user_id": 123}, "secret")
        >>> payload = verify_jwt_token(token, "secret")
        >>> print(payload['user_id'])
        123

    Security Note:
        - ALWAYS specify algorithms parameter to prevent algorithm confusion attacks
        - Check token expiry (exp claim) - this is automatic
        - Validate issuer and audience when applicable
        - Use constant-time comparison for secret keys
        - Reject tokens with invalid algorithms
    """
    if not JWT_AVAILABLE:
        raise ImportError(
            "PyJWT is required for JWT token verification. "
            "Install it with: pip install reroute[security]"
        )

    if algorithms is None:
        algorithms = ["HS256"]

    # Decode and verify token
    payload = jwt.decode(
        token,
        secret,
        algorithms=algorithms,
        issuer=issuer,
        audience=audience,
    )

    return payload


def decode_jwt_token(
    token: str,
    verify: bool = False
) -> Dict[str, Any]:
    """Decode JWT token without verification (for debugging).

    WARNING: This function does NOT verify the token signature.
    Only use for debugging purposes, never for authentication decisions.

    Args:
        token: JWT token string to decode
        verify: If True, verify signature (requires secret, not implemented here)

    Returns:
        Decoded token payload as dictionary

    Raises:
        ImportError: If pyjwt is not installed
        jwt.DecodeError: If token format is invalid

    Example:
        >>> token = generate_jwt_token({"user_id": 123}, "secret")
        >>> payload = decode_jwt_token(token)
        >>> print(payload['user_id'])
        123

    Security Note:
        - This does NOT verify the signature!
        - Never use decoded data for authentication or authorization
        - Only use for debugging/logging purposes
        - For authentication, ALWAYS use verify_jwt_token()
    """
    if not JWT_AVAILABLE:
        raise ImportError(
            "PyJWT is required for JWT token decoding. "
            "Install it with: pip install reroute[security]"
        )

    # Decode without verification
    payload = jwt.decode(token, options={"verify_signature": False})
    return payload


def generate_secret_key(length: int = 32) -> str:
    """Generate cryptographically secure secret key.

    Uses secrets module (CSPRNG) to generate random bytes suitable
    for cryptographic use (secret keys, API keys, etc.).

    Args:
        length: Length in bytes (default: 32 bytes = 256 bits)

    Returns:
        Hex-encoded secret key string

    Raises:
        ValueError: If length is less than 16 bytes

    Example:
        >>> key = generate_secret_key()
        >>> print(key)
        a1b2c3d4e5f6...

    Security Note:
        - Store secret keys securely (environment variables, vault)
        - Never commit secret keys to version control
        - Use at least 32 bytes for production applications
        - Rotate keys periodically (if possible)
        - Use different keys for different environments
    """
    if length < 16:
        raise ValueError("Secret key length must be at least 16 bytes")

    return secrets.token_hex(length)


def generate_reset_token(length: int = 32) -> str:
    """Generate secure password reset token.

    Generates a cryptographically secure random token suitable for
    password reset, email verification, etc.

    Args:
        length: Length in bytes (default: 32 bytes)

    Returns:
        URL-safe base64-encoded token string

    Example:
        >>> token = generate_reset_token()
        >>> print(token)
        Xb5Gh8Km3Pq...

    Security Note:
        - Tokens should be single-use and expire after short time
        - Store hash of token, not the token itself
        - Use HTTPS to prevent token interception
        - Invalidate token after use
        - Send token via secure channel (email)
        - Consider rate limiting for reset requests
    """
    return secrets.token_urlsafe(length)


def generate_api_key(prefix: str = "ruk") -> str:
    """Generate API key with prefix for identification.

    API keys are used to authenticate API requests instead of user credentials.
    The prefix helps identify the key type and makes keys easier to manage.

    Args:
        prefix: Key prefix for identification (default: "ruk" for REROUTE Key)
                Use different prefixes for different environments (e.g., "ruk_dev", "ruk_prod")

    Returns:
        API key string in format: prefix_randomkey

    Example:
        >>> key = generate_api_key()
        >>> print(key)
        ruk_Xb5Gh8Km3Pq...

    Security Note:
        - Store API keys hashed (like passwords) in database
        - Use HTTPS to prevent key interception
        - Implement key rotation mechanism
        - Include key metadata (created, expiry, scopes)
        - Consider adding IP whitelisting for API keys
        - Log API key usage for audit trails
        - Never include API keys in error messages
    """
    # Generate 32 random bytes, encode as URL-safe base64
    random_part = secrets.token_urlsafe(32)

    # Remove any padding characters
    random_part = random_part.rstrip('=')

    return f"{prefix}_{random_part}"


def generate_session_id() -> str:
    """Generate cryptographically secure session ID.

    Session IDs are used to identify user sessions. They must be
    unpredictable to prevent session hijacking attacks.

    Args:
        None

    Returns:
        URL-safe session ID string

    Example:
        >>> session_id = generate_session_id()
        >>> print(session_id)
        Xb5Gh8Km3Pq...

    Security Note:
        - Use HTTPS exclusively (cookies can be intercepted over HTTP)
        - Set 'Secure' and 'HttpOnly' flags on session cookies
        - Set 'SameSite' cookie attribute to prevent CSRF
        - Regenerate session ID after login
        - Invalidate old session IDs after privilege escalation
        - Implement session timeout (e.g., 30 minutes of inactivity)
        - Store server-side session data securely
        - Consider binding session to IP address (optional)
        - Never expose session IDs in URLs or logs
    """
    # Generate 32 random bytes for session ID
    return secrets.token_urlsafe(32)
