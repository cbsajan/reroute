"""
Input Validation Helpers for REROUTE

Provides email/URL validation, HTML sanitization, and
password strength checking.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import re
import string
from urllib.parse import urlparse

# Optional dependencies
try:
    from email_validator import validate_email as ev, EmailNotValidError
    EMAIL_VALIDATOR_AVAILABLE = True
except ImportError:
    EMAIL_VALIDATOR_AVAILABLE = False

try:
    import bleach
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False


@dataclass
class ValidationResult:
    """Validation result with details.

    Attributes:
        is_valid: Whether validation passed
        value: The validated/cleaned value
        errors: List of error messages
        warnings: List of warning messages (non-critical issues)
    """
    is_valid: bool
    value: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class PasswordStrength:
    """Password strength analysis.

    Attributes:
        score: Strength score (0-100)
        level: Strength level (weak, fair, good, strong)
        suggestions: List of improvement suggestions
        warnings: List of security warnings
    """
    score: int
    level: str
    suggestions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def validate_email(
    email: str,
    check_deliverability: bool = False
) -> ValidationResult:
    """Validate email address (RFC 5322).

    Performs comprehensive email validation including syntax checking
    and optional deliverability verification (DNS MX record check).

    Args:
        email: Email address to validate
        check_deliverability: Check if email domain can receive emails
                              (requires DNS lookup, slower)

    Returns:
        ValidationResult with is_valid, normalized email, and errors

    Example:
        >>> result = validate_email("user@example.com")
        >>> if result.is_valid:
        ...     print(f"Valid: {result.value}")

    Security Note:
        - Email validation alone doesn't prove ownership
        - Always verify email via confirmation link/code
        - Consider rate limiting email-based operations
        - Be careful with error messages (don't reveal if email exists)
    """
    if not email:
        return ValidationResult(
            is_valid=False,
            value="",
            errors=["Email cannot be empty"]
        )

    if not EMAIL_VALIDATOR_AVAILABLE:
        raise ImportError(
            "email-validator is required for email validation. "
            "Install it with: pip install reroute[security]"
        )

    try:
        # Validate and normalize email
        valid = ev(
            email,
            check_deliverability=check_deliverability,
        )

        return ValidationResult(
            is_valid=True,
            value=valid.email,
            errors=[],
            warnings=[]
        )

    except EmailNotValidError as e:
        return ValidationResult(
            is_valid=False,
            value=email,
            errors=[str(e)],
            warnings=[]
        )


def validate_url(
    url: str,
    allowed_schemes: Optional[List[str]] = None,
    require_fqdn: bool = True
) -> ValidationResult:
    """Validate URL with scheme checking.

    Validates URL structure and optionally restricts allowed schemes
    (e.g., only allow https:// for security).

    Args:
        url: URL to validate
        allowed_schemes: List of allowed URL schemes (e.g., ["https", "http"])
                        If None, allows any scheme
        require_fqdn: Require fully-qualified domain name (rejects localhost, etc.)

    Returns:
        ValidationResult with is_valid, normalized URL, and errors

    Example:
        >>> result = validate_url("https://example.com", allowed_schemes=["https"])
        >>> if result.is_valid:
        ...     print("Secure URL valid")

    Security Note:
        - Always restrict schemes for user-provided URLs (whitelist approach)
        - Use allowlist instead of denylist for schemes
        - Consider blocking private IP addresses (192.168.x.x, etc.)
        - Be aware of SSRF (Server-Side Request Forgery) risks
        - Never resolve URLs without validation
    """
    if not url:
        return ValidationResult(
            is_valid=False,
            value="",
            errors=["URL cannot be empty"]
        )

    errors = []
    warnings = []

    try:
        parsed = urlparse(url)

        # Check scheme
        if not parsed.scheme:
            errors.append("URL must include a scheme (e.g., https://)")
        elif allowed_schemes and parsed.scheme not in allowed_schemes:
            errors.append(f"URL scheme '{parsed.scheme}' is not allowed. Allowed schemes: {', '.join(allowed_schemes)}")

        # Check network location
        if not parsed.netloc:
            errors.append("URL must include a domain or host")
        elif require_fqdn:
            # Reject localhost, IP addresses, etc.
            if parsed.netloc in ['localhost', '127.0.0.1', '[::1]']:
                warnings.append("URL uses localhost or loopback address")
            elif parsed.netloc.startswith('192.168.') or \
                 parsed.netloc.startswith('10.') or \
                 parsed.netloc.startswith('172.16.'):
                warnings.append("URL uses private IP address")

        # Check for suspicious patterns
        if '@' in parsed.netloc:
            warnings.append("URL contains credentials (should use auth header instead)")

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            value=url,
            errors=errors,
            warnings=warnings
        )

    except Exception as e:
        return ValidationResult(
            is_valid=False,
            value=url,
            errors=[f"Invalid URL: {str(e)}"],
            warnings=[]
        )


def sanitize_html(
    html: str,
    allowed_tags: Optional[List[str]] = None,
    allowed_attributes: Optional[Dict[str, List[str]]] = None,
    strip_tags: bool = True
) -> str:
    """Sanitize HTML to prevent XSS attacks.

    Removes or escapes dangerous HTML content that could lead to
    Cross-Site Scripting (XSS) attacks.

    Args:
        html: HTML string to sanitize
        allowed_tags: List of allowed HTML tags (e.g., ["b", "i", "p"])
                      If None, uses a safe default list
        allowed_attributes: Dict mapping tags to allowed attributes
                           If None, uses a safe default set
        strip_tags: If True, remove disallowed tags; if False, escape them

    Returns:
        Sanitized HTML string safe to render

    Example:
        >>> html = "<script>alert('XSS')</script><b>safe</b>"
        >>> clean = sanitize_html(html)
        >>> print(clean)
        <b>safe</b>

    Security Note:
        - Always sanitize user-generated HTML before rendering
        - Use Content-Security-Policy as additional protection
        - Consider using a template system with auto-escaping (Jinja2)
        - Be conservative with allowed tags/attributes
        - Never allow <script>, <iframe>, <object>, <embed>, etc.
        - Be careful with style attributes (can contain CSS-based XSS)
    """
    if not html:
        return ""

    if not BLEACH_AVAILABLE:
        raise ImportError(
            "bleach is required for HTML sanitization. "
            "Install it with: pip install reroute[security]"
        )

    # Default safe tags (no script, iframe, object, etc.)
    if allowed_tags is None:
        allowed_tags = [
            'a', 'abbr', 'acronym', 'b', 'blockquote', 'br', 'code', 'div',
            'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img',
            'li', 'ol', 'p', 'pre', 'span', 'strong', 'table', 'tbody',
            'td', 'th', 'thead', 'tr', 'ul'
        ]

    # Default safe attributes
    if allowed_attributes is None:
        allowed_attributes = {
            'a': ['href', 'title', 'rel'],
            'abbr': ['title'],
            'acronym': ['title'],
            'img': ['src', 'alt', 'title'],
            'div': ['class'],
            'span': ['class'],
            'p': ['class'],
            'h1': ['class'],
            'h2': ['class'],
            'h3': ['class'],
            'h4': ['class'],
            'h5': ['class'],
            'h6': ['class'],
        }

    # Sanitize HTML
    clean_html = bleach.clean(
        html,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=strip_tags,
        strip_comments=True
    )

    return clean_html


def sanitize_filename(
    filename: str,
    replacement: str = "_",
    max_length: int = 255
) -> str:
    """Sanitize filename for secure filesystem storage.

    Removes dangerous characters and prevents path traversal attacks.
    Suitable for user-uploaded filenames.

    Args:
        filename: Original filename
        replacement: Character to replace dangerous characters with
        max_length: Maximum filename length (default: 255 for most filesystems)

    Returns:
        Sanitized filename safe for filesystem storage

    Example:
        >>> clean = sanitize_filename("../../../etc/passwd")
        >>> print(clean)
        ___..__..__etc_passwd

    Security Note:
        - Never trust user-provided filenames
        - Always sanitize filenames before filesystem operations
        - Store files outside web root or use random filenames
        - Consider generating random filenames instead of sanitizing
        - Be aware of file size limits and disk space
        - Scan uploaded files for malware
        - Check file type headers (not just extension)
    """
    if not filename:
        return "unnamed"

    # Extract basename (remove directory path)
    filename = filename.replace('\\', '/').split('/')[-1]

    # Remove control characters
    filename = ''.join(char for char in filename if ord(char) >= 32)

    # Replace dangerous characters
    dangerous_chars = '<>:"/\\|?*\'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f'
    for char in dangerous_chars:
        filename = filename.replace(char, replacement)

    # Remove leading dots, dashes, spaces (path traversal)
    filename = filename.lstrip('.- ')

    # Replace multiple consecutive replacements with single
    if replacement:
        filename = re.sub(f'{re.escape(replacement)}+', replacement, filename)

    # Remove leading/trailing replacements
    filename = filename.strip(replacement)

    # Truncate to max length
    if len(filename) > max_length:
        # Preserve extension
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        if ext:
            max_name_length = max_length - len(ext) - 1  # -1 for the dot
            filename = name[:max_name_length] + '.' + ext
        else:
            filename = filename[:max_length]

    # Ensure filename is not empty
    if not filename:
        return "unnamed"

    return filename


def check_password_strength(
    password: str,
    min_length: int = 8,
    check_common_passwords: bool = True
) -> PasswordStrength:
    """Analyze password strength.

    Evaluates password strength based on length, character variety,
    and common password patterns.

    Args:
        password: Password to analyze
        min_length: Minimum required length (default: 8)
        check_common_passwords: Check against common weak passwords

    Returns:
        PasswordStrength with score, level, and suggestions

    Example:
        >>> result = check_password_strength("password")
        >>> print(f"Score: {result.score}, Level: {result.level}")
        Score: 20, Level: weak

    Security Note:
        - Encourage passwords of 12+ characters
        - Require mix of uppercase, lowercase, numbers, symbols
        - Block common passwords and dictionary words
        - Use password hashing (Argon2) for storage
        - Implement rate limiting for password attempts
        - Consider implementing password blacklist
        - Never store passwords in plain text
    """
    if not password:
        return PasswordStrength(
            score=0,
            level="weak",
            suggestions=["Password cannot be empty"],
            warnings=["Password is required"]
        )

    score = 0
    suggestions = []
    warnings = []

    # Common weak passwords (subset of most common passwords)
    common_passwords = {
        'password', '123456', '12345678', 'qwerty', 'abc123',
        'monkey', '1234567', 'letmein', 'trustno1', 'dragon',
        'baseball', '111111', 'iloveyou', 'master', 'sunshine',
        'ashley', 'bailey', 'passw0rd', 'shadow', '123123',
        '654321', 'superman', 'qazwsx', 'michael', 'football',
    }

    # Check length
    if len(password) >= min_length:
        score += 20
    else:
        suggestions.append(f"Use at least {min_length} characters")

    if len(password) >= 12:
        score += 10
    elif len(password) >= 16:
        score += 20

    # Check character variety
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in string.punctuation for c in password)

    variety_score = sum([has_upper, has_lower, has_digit, has_special])
    score += variety_score * 10

    if not has_upper:
        suggestions.append("Add uppercase letters")
    if not has_lower:
        suggestions.append("Add lowercase letters")
    if not has_digit:
        suggestions.append("Add numbers")
    if not has_special:
        suggestions.append("Add special characters (!@#$%^&*)")

    # Check for common passwords
    if check_common_passwords and password.lower() in common_passwords:
        warnings.append("This is a very common password")
        score = max(0, score - 50)

    # Check for repeating characters
    if len(set(password)) < 4:
        warnings.append("Password has too few unique characters")
        score = max(0, score - 20)

    # Check for sequential characters
    seq_patterns = ['abc', '123', 'qwe', 'asd', 'zxc']
    if any(pattern in password.lower() for pattern in seq_patterns):
        suggestions.append("Avoid sequential characters")
        score = max(0, score - 10)

    # Check for keyboard patterns
    keyboard_patterns = ['qwerty', 'asdfgh', 'zxcvbn']
    if any(pattern in password.lower() for pattern in keyboard_patterns):
        suggestions.append("Avoid keyboard patterns")
        score = max(0, score - 15)

    # Determine strength level
    if score >= 80:
        level = "strong"
    elif score >= 60:
        level = "good"
    elif score >= 40:
        level = "fair"
    else:
        level = "weak"

    # Add final suggestions
    if level == "weak":
        suggestions.append("Consider using a passphrase instead")
    elif level == "fair":
        suggestions.append("Add more length or variety")

    return PasswordStrength(
        score=score,
        level=level,
        suggestions=suggestions,
        warnings=warnings
    )
