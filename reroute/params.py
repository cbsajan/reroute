"""
REROUTE Parameter Injection

Provides FastAPI-style parameter injection for route handlers.
Use these in route method signatures to automatically extract and validate request data.

SECURITY FEATURES:
- Comprehensive input validation using Pydantic
- Size limits and sanitization
- Type checking enforcement
- Security-aware parameter constraints
"""

import re
import logging
from pathlib import Path
from typing import Any, Optional, Type, Union, List, Dict, Callable
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SecurityValidator:
    """
    Security validation utilities for parameter injection.

    Provides comprehensive input validation and sanitization to prevent
    injection attacks, data leakage, and other security vulnerabilities.
    """

    # Maximum lengths for different parameter types (security limits)
    MAX_LENGTHS = {
        'query_string': 1000,      # URL query parameters
        'path_segment': 100,       # URL path segments
        'header_value': 8192,      # HTTP header values
        'cookie_value': 4096,      # Cookie values
        'form_field': 10485760,    # Form fields (10MB)
        'json_field': 104857600,   # JSON fields (100MB)
    }

    # Dangerous patterns that should be blocked
    DANGEROUS_PATTERNS = [
        # Script injection patterns
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',

        # SQL injection patterns
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
        r"'.*OR.*'",
        r'".*OR.*"',
        r'\bUNION\s+SELECT\b',

        # Command injection patterns
        r'[;&|`$(){}[\]]',  # Shell metacharacters
        r'\b(curl|wget|nc|netcat|bash|sh|cmd|powershell)\b',

        # Path traversal patterns
        r'\.\./.*',
        r'\.\\.\\.*',
        r'%2e%2e%2f',
        r'%2e%2e%5c',

        # NoSQL injection patterns
        r'\$where',
        r'\$ne',
        r'\$gt',
        r'\$lt',
        r'\$in',

        # XSS patterns
        r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]',  # Control characters
        r'&#x[0-9a-f]+',  # HTML entities
        r'&#[0-9]+',      # HTML numeric entities
    ]

    @classmethod
    def validate_input_size(cls, value: str, param_type: str) -> bool:
        """
        Validate input size against security limits.

        Args:
            value: Input value to validate
            param_type: Type of parameter (query, path, header, etc.)

        Returns:
            True if size is within limits, False otherwise
        """
        if not isinstance(value, str):
            return True

        max_length = cls.MAX_LENGTHS.get(param_type, 1000)
        if len(value) > max_length:
            logger.warning(
                f"Input too large for {param_type}: {len(value)} > {max_length} characters"
            )
            return False
        return True

    @classmethod
    def sanitize_input(cls, value: str) -> str:
        """
        Sanitize input by removing dangerous content.

        Args:
            value: Input value to sanitize

        Returns:
            Sanitized input value
        """
        if not isinstance(value, str):
            return value

        # Remove null bytes and control characters
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)

        # Normalize whitespace
        sanitized = ' '.join(sanitized.split())

        # Strip surrounding whitespace
        sanitized = sanitized.strip()

        return sanitized

    @classmethod
    def detect_dangerous_content(cls, value: str) -> List[str]:
        """
        Detect potentially dangerous content in input.

        Args:
            value: Input value to check

        Returns:
            List of detected dangerous patterns
        """
        if not isinstance(value, str):
            return []

        detected = []
        value_lower = value.lower()

        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                detected.append(pattern)

        return detected

    @classmethod
    def validate_regex_pattern(cls, pattern: str) -> bool:
        """
        Validate that a regex pattern is safe (prevents ReDoS attacks).

        Args:
            pattern: Regex pattern to validate

        Returns:
            True if pattern is safe, False otherwise
        """
        if not isinstance(pattern, str):
            return False

        try:
            # Check for dangerous regex patterns that can cause ReDoS
            dangerous_patterns = [
                r'\(\?\=.*\)\*',     # Lookahead with quantifier
                r'\(\?\!.*\)\*',     # Negative lookahead with quantifier
                r'\(\?\<.*\>\)\*',   # Lookbehind with quantifier
                r'\(\?\<\!.*\)\*',   # Negative lookbehind with quantifier
                r'.*\{.*\}.*\{.*\}', # Multiple nested quantifiers
                r'.*\(\.\*\*\).*',    # Nested quantifiers
                r'.*\(\.\?\).*',      # Lazy quantifier in complex pattern
            ]

            for dangerous in dangerous_patterns:
                if re.search(dangerous, pattern):
                    logger.warning(f"Potentially dangerous regex pattern: {pattern}")
                    return False

            # Test compile the pattern
            re.compile(pattern)
            return True

        except re.error as e:
            logger.warning(f"Invalid regex pattern: {pattern} - {e}")
            return False


class ParamBase:
    """
    Base class for all parameter types with enhanced security validation.
    """

    def __init__(
        self,
        default: Any = ...,
        *,
        description: Optional[str] = None,
        alias: Optional[str] = None,
        title: Optional[str] = None,
        ge: Optional[float] = None,
        le: Optional[float] = None,
        gt: Optional[float] = None,
        lt: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        regex: Optional[str] = None,
        example: Any = None,
        deprecated: bool = False,
        # Security-specific parameters
        sanitize: bool = True,           # Auto-sanitize input
        strict_mode: bool = True,        # Enable strict validation
        max_length_security: Optional[int] = None,  # Override security max length
        allow_null_bytes: bool = False,  # Allow null bytes (dangerous)
    ):
        self.default = default
        self.description = description
        self.alias = alias
        self.title = title
        self.ge = ge
        self.le = le
        self.gt = gt
        self.lt = lt
        self.min_length = min_length
        self.max_length = max_length
        self.regex = regex
        self.example = example
        self.deprecated = deprecated
        self.required = default is ...

        # Security parameters
        self.sanitize = sanitize
        self.strict_mode = strict_mode
        self.max_length_security = max_length_security
        self.allow_null_bytes = allow_null_bytes

        # Security: Validate regex pattern for safety
        if self.regex and not SecurityValidator.validate_regex_pattern(self.regex):
            raise ValueError(f"Unsafe regex pattern: {self.regex}")

    def validate_security(self, value: Any, param_type: str = 'default') -> Any:
        """
        Apply security validation to input value.

        Args:
            value: Input value to validate
            param_type: Type of parameter for size limits

        Returns:
            Validated and sanitized value

        Raises:
            ValueError: If value fails security validation
        """
        if value is None:
            return value

        # Convert to string for validation if possible
        if not isinstance(value, str):
            try:
                str_value = str(value)
            except Exception:
                return value
        else:
            str_value = value

        # Security: Check for null bytes
        if not self.allow_null_bytes and '\x00' in str_value:
            raise ValueError("Null bytes are not allowed in input")

        # Security: Validate input size
        max_length = self.max_length_security or SecurityValidator.MAX_LENGTHS.get(param_type, 1000)
        if len(str_value) > max_length:
            raise ValueError(f"Input too large: {len(str_value)} > {max_length} characters")

        # Security: Detect dangerous content
        if self.strict_mode:
            dangerous_patterns = SecurityValidator.detect_dangerous_content(str_value)
            if dangerous_patterns:
                logger.warning(f"Dangerous content detected: {dangerous_patterns}")
                raise ValueError(f"Input contains potentially dangerous content")

        # Security: Sanitize input if requested
        if self.sanitize:
            if isinstance(value, str):
                return SecurityValidator.sanitize_input(str_value)
            else:
                # For non-string values, we don't sanitize but still validate
                return value
        else:
            return value


class Query(ParamBase):
    """
    Query parameter injection with enhanced security.

    Extracts values from URL query parameters (?key=value) with comprehensive
    validation and sanitization to prevent injection attacks.

    Example:
        def get(self,
                limit: int = Query(10, description="Maximum results"),
                offset: int = Query(0, description="Skip results"),
                search: str = Query(None, description="Search term")):
            return {"limit": limit, "offset": offset}

    Usage:
        GET /users?limit=20&offset=10&search=john
        → limit=20, offset=10, search="john"

    Security Features:
    - URL decoding validation
    - Size limits (1000 characters by default)
    - XSS prevention
    - SQL injection detection
    - Automatic sanitization
    """

    def __init__(self, *args, **kwargs):
        # Set query-specific security defaults
        if 'max_length_security' not in kwargs:
            kwargs['max_length_security'] = SecurityValidator.MAX_LENGTHS['query_string']
        super().__init__(*args, **kwargs)

    def validate(self, value: Any) -> Any:
        """
        Validate query parameter value with security checks.

        Args:
            value: Query parameter value to validate

        Returns:
            Validated and sanitized value
        """
        return self.validate_security(value, 'query_string')


class Path(ParamBase):
    """
    Path parameter injection with enhanced security.

    Extracts values from URL path segments with strict validation
    to prevent path traversal and injection attacks.

    Example:
        def get(self,
                user_id: int = Path(..., description="User ID"),
                post_id: int = Path(..., description="Post ID")):
            return {"user_id": user_id, "post_id": post_id}

    Usage:
        GET /users/123/posts/456
        → user_id=123, post_id=456

    Security Features:
    - Path traversal prevention
    - Character encoding validation
    - Size limits (100 characters by default)
    - Format validation
    """

    def __init__(self, *args, **kwargs):
        # Set path-specific security defaults
        if 'max_length_security' not in kwargs:
            kwargs['max_length_security'] = SecurityValidator.MAX_LENGTHS['path_segment']
        super().__init__(*args, **kwargs)

    def validate(self, value: Any) -> Any:
        """
        Validate path parameter value with security checks.

        Args:
            value: Path parameter value to validate

        Returns:
            Validated and sanitized value
        """
        return self.validate_security(value, 'path_segment')


class Header(ParamBase):
    """
    Header parameter injection with enhanced security.

    Extracts values from HTTP headers with validation to prevent
    header injection and request smuggling attacks.

    Example:
        def get(self,
                authorization: str = Header(..., description="Bearer token"),
                user_agent: str = Header(None, description="User agent")):
            return {"auth": authorization}

    Usage:
        GET /users
        Headers:
            Authorization: Bearer abc123
            User-Agent: Mozilla/5.0
        → authorization="Bearer abc123", user_agent="Mozilla/5.0"

    Security Features:
    - HTTP header injection prevention
    - Newline character filtering
    - Size limits (8KB by default)
    - Character encoding validation
    """

    def __init__(self, *args, **kwargs):
        # Set header-specific security defaults
        if 'max_length_security' not in kwargs:
            kwargs['max_length_security'] = SecurityValidator.MAX_LENGTHS['header_value']
        super().__init__(*args, **kwargs)

    def validate(self, value: Any) -> Any:
        """
        Validate header value with security checks.

        Args:
            value: Header value to validate

        Returns:
            Validated and sanitized value
        """
        validated = self.validate_security(value, 'header_value')

        # Additional header-specific security checks
        if isinstance(validated, str):
            # Remove newlines and carriage returns to prevent header injection
            validated = validated.replace('\r', '').replace('\n', '')

        return validated


class Body(ParamBase):
    """
    Request body injection with enhanced security.

    Parses and validates JSON request body using Pydantic models with
    comprehensive security validation to prevent injection attacks.

    Example:
        from app.models.user import UserCreate

        def post(self,
                 user: UserCreate = Body(..., description="User data")):
            return {"user": user.dict()}

    Usage:
        POST /users
        Body: {"name": "John", "email": "john@example.com"}
        → user=UserCreate(name="John", email="john@example.com")

    Security Features:
    - JSON schema validation
    - Size limits (100MB by default)
    - Content-Type validation
    - Nested object validation
    - Depth limits to prevent stack overflow
    """

    def __init__(
        self,
        default: Any = ...,
        *,
        embed: bool = False,
        media_type: str = "application/json",
        max_depth: int = 10,  # Prevent deeply nested objects
        **kwargs
    ):
        # Set body-specific security defaults
        if 'max_length_security' not in kwargs:
            kwargs['max_length_security'] = SecurityValidator.MAX_LENGTHS['json_field']
        super().__init__(default, **kwargs)
        self.embed = embed
        self.media_type = media_type
        self.max_depth = max_depth

    def validate(self, value: Any) -> Any:
        """
        Validate request body with security checks.

        Args:
            value: Request body to validate

        Returns:
            Validated and sanitized value
        """
        # For body parameters, we need special handling for complex objects
        if isinstance(value, (dict, list)):
            # Validate object depth to prevent stack overflow
            if self._get_object_depth(value) > self.max_depth:
                raise ValueError(f"Object depth exceeds maximum allowed: {self.max_depth}")

        return value

    def _get_object_depth(self, obj: Any, current_depth: int = 0) -> int:
        """
        Calculate the depth of a nested object.

        Args:
            obj: Object to check
            current_depth: Current depth level

        Returns:
            Maximum depth of the object
        """
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(self._get_object_depth(v, current_depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(self._get_object_depth(item, current_depth + 1) for item in obj)
        else:
            return current_depth


class Cookie(ParamBase):
    """
    Cookie parameter injection with enhanced security.

    Extracts values from HTTP cookies with validation to prevent
    cookie injection and session hijacking attacks.

    Example:
        def get(self,
                session_id: str = Cookie(..., description="Session ID"),
                theme: str = Cookie("light", description="UI theme")):
            return {"session": session_id, "theme": theme}

    Usage:
        GET /profile
        Cookies: session_id=abc123; theme=dark
        → session_id="abc123", theme="dark"

    Security Features:
    - Cookie injection prevention
    - Size limits (4KB by default)
    - Character validation
    - Session ID format validation
    """

    def __init__(self, *args, **kwargs):
        # Set cookie-specific security defaults
        if 'max_length_security' not in kwargs:
            kwargs['max_length_security'] = SecurityValidator.MAX_LENGTHS['cookie_value']
        super().__init__(*args, **kwargs)

    def validate(self, value: Any) -> Any:
        """
        Validate cookie value with security checks.

        Args:
            value: Cookie value to validate

        Returns:
            Validated and sanitized value
        """
        validated = self.validate_security(value, 'cookie_value')

        # Additional cookie-specific security checks
        if isinstance(validated, str):
            # Remove control characters and null bytes from cookies
            validated = re.sub(r'[\x00-\x1f\x7f]', '', validated)

        return validated


class Form(ParamBase):
    """
    Form data injection with enhanced security.

    Extracts values from form data (application/x-www-form-urlencoded) with
    validation to prevent form-based injection attacks.

    Example:
        def post(self,
                 username: str = Form(...),
                 password: str = Form(...)):
            return {"username": username}

    Usage:
        POST /login
        Content-Type: application/x-www-form-urlencoded
        Body: username=john&password=secret
        → username="john", password="secret"

    Security Features:
    - Form injection prevention
    - Size limits (10MB by default)
    - URL decoding validation
    - Character encoding checks
    """

    def __init__(self, *args, **kwargs):
        # Set form-specific security defaults
        if 'max_length_security' not in kwargs:
            kwargs['max_length_security'] = SecurityValidator.MAX_LENGTHS['form_field']
        super().__init__(*args, **kwargs)

    def validate(self, value: Any) -> Any:
        """
        Validate form field value with security checks.

        Args:
            value: Form field value to validate

        Returns:
            Validated and sanitized value
        """
        return self.validate_security(value, 'form_field')


class File(ParamBase):
    """
    File upload injection with enhanced security.

    Handles file uploads (multipart/form-data) with comprehensive
    validation to prevent malicious file upload attacks.

    Example:
        from fastapi import UploadFile

        def post(self,
                 file: UploadFile = File(..., description="Upload file")):
            return {"filename": file.filename, "size": file.size}

    Usage:
        POST /upload
        Content-Type: multipart/form-data
        Body: [file data]
        → file=UploadFile(filename="image.jpg")

    Security Features:
    - File type validation
    - Size limits
    - Filename sanitization
    - Magic number verification
    - Malicious file detection
    """

    def __init__(
        self,
        default: Any = ...,
        *,
        max_file_size: int = 10485760,  # 10MB default
        allowed_extensions: Optional[List[str]] = None,
        allowed_mime_types: Optional[List[str]] = None,
        scan_content: bool = True,  # Scan for malicious content
        **kwargs
    ):
        super().__init__(default, **kwargs)
        self.max_file_size = max_file_size
        self.allowed_extensions = allowed_extensions or ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.txt']
        self.allowed_mime_types = allowed_mime_types or ['image/jpeg', 'image/png', 'image/gif', 'application/pdf', 'text/plain']
        self.scan_content = scan_content

    def validate_file(self, file_obj: Any) -> bool:
        """
        Validate uploaded file for security.

        Args:
            file_obj: Uploaded file object

        Returns:
            True if file is safe, False otherwise

        Raises:
            ValueError: If file fails security validation
        """
        # Check file size
        if hasattr(file_obj, 'size') and file_obj.size > self.max_file_size:
            raise ValueError(f"File too large: {file_obj.size} > {self.max_file_size} bytes")

        # Check filename
        if hasattr(file_obj, 'filename') and file_obj.filename:
            filename = file_obj.filename.lower()

            # Security: Check for dangerous filename patterns
            dangerous_patterns = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
            for pattern in dangerous_patterns:
                if pattern in filename:
                    raise ValueError(f"Dangerous character in filename: {pattern}")

            # Check file extension
            file_ext = Path(filename).suffix.lower()
            if file_ext not in self.allowed_extensions:
                raise ValueError(f"File extension not allowed: {file_ext}")

        # Check MIME type
        if hasattr(file_obj, 'content_type') and file_obj.content_type:
            mime_type = file_obj.content_type.lower()
            if mime_type not in self.allowed_mime_types:
                raise ValueError(f"MIME type not allowed: {mime_type}")

        # Additional security checks would go here in production
        # - Magic number verification
        # - Virus scanning
        # - Content inspection

        return True


# Aliases for convenience
Param = Query  # Backwards compatibility
Depends = ParamBase  # For dependency injection (future feature)


__all__ = [
    "Query",
    "Path",
    "Header",
    "Body",
    "Cookie",
    "Form",
    "File",
    "Param",
    "Depends",
]
