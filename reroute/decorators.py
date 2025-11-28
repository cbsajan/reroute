"""
REROUTE Decorators

Provides useful decorators for route methods including:
- rate_limit: Rate limiting per endpoint
- cache: Response caching
- requires: Authentication/authorization
- validate: Request validation
- timeout: Request timeout
- log_requests: Request logging
"""

import time
import functools
from typing import Callable, Dict, Any, Optional, List, Tuple
from datetime import datetime
from collections import defaultdict
import threading


# Rate Limiting Storage
# Security: Maximum number of unique keys to prevent unbounded memory growth
MAX_RATE_LIMIT_KEYS = 10000


class RateLimitStorage:
    """Thread-safe storage for rate limit tracking with size limits."""

    def __init__(self, max_keys: int = MAX_RATE_LIMIT_KEYS):
        self._storage: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
        self._max_keys = max_keys
        self._access_order: List[str] = []  # Track access order for LRU eviction

    def add_request(self, key: str, timestamp: float) -> None:
        """Add a request timestamp."""
        with self._lock:
            self._storage[key].append(timestamp)

    def get_requests(self, key: str) -> List[float]:
        """Get all request timestamps for a key."""
        with self._lock:
            return self._storage[key].copy()

    def cleanup(self, key: str, cutoff: float) -> None:
        """Remove requests older than cutoff timestamp."""
        with self._lock:
            self._storage[key] = [ts for ts in self._storage[key] if ts > cutoff]

    def _evict_lru_keys(self, count: int = 1) -> None:
        """Evict least recently used keys (must be called with lock held)."""
        for _ in range(min(count, len(self._access_order))):
            if self._access_order:
                old_key = self._access_order.pop(0)
                self._storage.pop(old_key, None)

    def check_and_add(self, key: str, timestamp: float, cutoff: float, max_requests: int) -> Tuple[bool, int]:
        """
        Atomically check rate limit and add request if allowed.

        Args:
            key: Rate limit key
            timestamp: Current request timestamp
            cutoff: Cutoff time for old requests
            max_requests: Maximum allowed requests in window

        Returns:
            Tuple of (allowed: bool, retry_after: int)
        """
        with self._lock:
            # Security: Enforce max keys limit to prevent memory exhaustion
            if key not in self._storage and len(self._storage) >= self._max_keys:
                # Evict oldest keys to make room
                self._evict_lru_keys(max(1, len(self._storage) - self._max_keys + 1))

            # Update access order for LRU tracking
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)

            # Cleanup old requests
            self._storage[key] = [ts for ts in self._storage[key] if ts > cutoff]

            # Check if limit exceeded
            if len(self._storage[key]) >= max_requests:
                # Calculate retry_after
                retry_after = int(self._storage[key][0] - cutoff) + 1
                return False, retry_after

            # Add current request
            self._storage[key].append(timestamp)
            return True, 0


# Global storage instances
_rate_limit_storage = RateLimitStorage()
_cache_storage: Dict[str, Dict[str, Any]] = {}
_cache_lock = threading.Lock()

# Security: Set maximum cache size to prevent unbounded memory growth
MAX_CACHE_SIZE = 1000


def _evict_oldest_cache_entries(target_size: int = MAX_CACHE_SIZE):
    """
    Evict oldest cache entries when cache size exceeds limit.
    Uses LRU (Least Recently Used) eviction strategy.

    Args:
        target_size: Maximum number of cache entries to keep
    """
    if len(_cache_storage) <= target_size:
        return

    # Sort by creation time (oldest first)
    sorted_entries = sorted(
        _cache_storage.items(),
        key=lambda x: x[1]["created_at"]
    )

    # Remove oldest entries to reach target size
    entries_to_remove = len(_cache_storage) - target_size
    for key, _ in sorted_entries[:entries_to_remove]:
        del _cache_storage[key]


def _cleanup_expired_caches():
    """Background thread to periodically clean up expired cache entries."""
    import logging
    logger = logging.getLogger(__name__)

    while True:
        time.sleep(60)  # Check every minute
        try:
            with _cache_lock:
                current_time = time.time()
                expired_keys = [
                    k for k, v in _cache_storage.items()
                    if v["expires_at"] < current_time
                ]
                for k in expired_keys:
                    del _cache_storage[k]

                # Security: Enforce maximum cache size
                _evict_oldest_cache_entries(MAX_CACHE_SIZE)

        except Exception as e:
            # Log the error instead of silently swallowing it
            logger.error(f"Cache cleanup failed: {e}", exc_info=True)


# Start cache cleanup thread
_cleanup_thread = threading.Thread(target=_cleanup_expired_caches, daemon=True)
_cleanup_thread.start()


def rate_limit(limit: str, key_func: Optional[Callable] = None, per_ip: bool = False):
    """
    Rate limit decorator for route methods.

    Args:
        limit: Rate limit string (e.g., "5/min", "100/hour", "1000/day")
        key_func: Optional function to generate rate limit key (default: uses method name)
        per_ip: Enable per-IP rate limiting (default: False for global rate limiting)

    Usage:
        @rate_limit("3/min")
        def get(self):
            return {"data": "..."}

        @rate_limit("10/hour", per_ip=True)  # Rate limit per client IP
        def post(self):
            return {"created": True}

        @rate_limit("100/day", key_func=lambda self: f"user_{self.get_user_id()}")
        def delete(self):
            return {"deleted": True}

    Returns:
        429 Too Many Requests if rate limit exceeded

    Note:
        When per_ip=True, the decorator extracts the client IP from:
        - Flask: flask.request.remote_addr (or X-Forwarded-For header if behind proxy)
        - FastAPI: request.client.host (if request param is declared in handler)
    """
    # Parse limit string
    parts = limit.split("/")
    if len(parts) != 2:
        raise ValueError(f"Invalid rate limit format: {limit}. Use format like '5/min'")

    max_requests = int(parts[0])
    period = parts[1].lower()

    # Convert period to seconds
    period_seconds = {
        "sec": 1,
        "second": 1,
        "min": 60,
        "minute": 60,
        "hour": 3600,
        "day": 86400,
    }

    if period not in period_seconds:
        raise ValueError(f"Invalid period: {period}. Use: sec, min, hour, day")

    window_seconds = period_seconds[period]

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract client IP if per_ip is enabled
            client_ip = None
            if per_ip and not key_func:
                # Security: Helper to validate IP address format
                def is_valid_ip(ip: str) -> bool:
                    """Validate IP address format to prevent header injection."""
                    import re
                    # IPv4 pattern
                    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
                    # IPv6 pattern (simplified)
                    ipv6_pattern = r'^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$'

                    if re.match(ipv4_pattern, ip):
                        # Validate each octet is 0-255
                        octets = ip.split('.')
                        return all(0 <= int(o) <= 255 for o in octets)
                    elif re.match(ipv6_pattern, ip):
                        return True
                    return False

                def sanitize_ip(raw_ip: str) -> str:
                    """Sanitize and validate IP from header."""
                    if not raw_ip:
                        return None
                    # Strip whitespace and take first IP if comma-separated
                    ip = raw_ip.split(',')[0].strip()
                    # Remove any potential injection characters
                    ip = ip.split()[0] if ip else None  # Take first token only
                    # Validate format
                    if ip and is_valid_ip(ip):
                        return ip
                    return None

                # Try Flask first (thread-local request)
                try:
                    from flask import request as flask_request
                    if flask_request:
                        # Get IP from X-Forwarded-For if behind proxy, else remote_addr
                        x_forwarded_for = flask_request.headers.get('X-Forwarded-For')
                        if x_forwarded_for:
                            # Security: Validate and sanitize the forwarded IP
                            client_ip = sanitize_ip(x_forwarded_for)
                        if not client_ip:
                            client_ip = flask_request.remote_addr
                except (ImportError, RuntimeError):
                    # Flask not available or no request context
                    pass

                # Try FastAPI (from kwargs) if Flask didn't work
                if not client_ip:
                    request = kwargs.get('request')
                    if request:
                        # FastAPI Request object
                        if hasattr(request, 'client') and request.client:
                            client_ip = request.client.host
                        # Check X-Forwarded-For header
                        elif hasattr(request, 'headers'):
                            x_forwarded_for = request.headers.get('X-Forwarded-For')
                            if x_forwarded_for:
                                # Security: Validate and sanitize the forwarded IP
                                client_ip = sanitize_ip(x_forwarded_for)

            # Generate rate limit key
            if key_func:
                key = f"rate_limit:{func.__name__}:{key_func(*args)}"
            elif per_ip and client_ip:
                key = f"rate_limit:{func.__name__}:ip:{client_ip}"
            else:
                key = f"rate_limit:{func.__name__}:default"

            current_time = time.time()
            cutoff_time = current_time - window_seconds

            # Atomically check and add request (prevents race condition)
            allowed, retry_after = _rate_limit_storage.check_and_add(
                key, current_time, cutoff_time, max_requests
            )

            if not allowed:
                # Security logging: Log rate limit exceeded event
                try:
                    from reroute.logging import security_logger
                    security_logger.log_rate_limit(
                        endpoint=func.__name__,
                        ip_address=client_ip,
                        limit=limit,
                        key=key
                    )
                except ImportError:
                    pass  # Security logging not available

                # Rate limit exceeded
                return {
                    "error": "Rate limit exceeded",
                    "limit": limit,
                    "retry_after": retry_after
                }, 429

            # Execute the actual function
            return func(*args, **kwargs)

        # Store metadata for introspection
        wrapper._rate_limit = limit
        return wrapper

    return decorator


def cache(duration: int = 60, key_func: Optional[Callable] = None):
    """
    Cache decorator for route methods.

    Args:
        duration: Cache duration in seconds (default: 60)
        key_func: Optional function to generate cache key

    Usage:
        @cache(duration=300)  # Cache for 5 minutes
        def get(self):
            return {"expensive": "data"}

        @cache(duration=60, key_func=lambda self: f"user_{self.user_id}")
        def get(self):
            return {"user_data": "..."}

        @cache(duration=3600)  # Cache for 1 hour
        def get(self):
            return self.fetch_from_database()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = f"cache:{func.__name__}:{key_func(*args)}"
            else:
                cache_key = f"cache:{func.__name__}:default"

            current_time = time.time()

            # Check cache
            with _cache_lock:
                if cache_key in _cache_storage:
                    cached_data = _cache_storage[cache_key]
                    if current_time < cached_data["expires_at"]:
                        # Cache hit
                        return cached_data["data"]
                    else:
                        # Cache expired
                        del _cache_storage[cache_key]

            # Cache miss - execute function (outside lock to avoid blocking)
            result = func(*args, **kwargs)

            # Store in cache with double-checked locking
            with _cache_lock:
                # Double-check: Another thread may have populated cache while we executed
                if cache_key in _cache_storage:
                    existing = _cache_storage[cache_key]
                    if time.time() < existing["expires_at"]:
                        # Another thread already cached a valid result, use it
                        # (our result is discarded but this prevents redundant work next time)
                        return existing["data"]

                # Security: Enforce cache size limit before adding new entry
                if len(_cache_storage) >= MAX_CACHE_SIZE:
                    _evict_oldest_cache_entries(MAX_CACHE_SIZE - 1)

                _cache_storage[cache_key] = {
                    "data": result,
                    "expires_at": time.time() + duration,  # Use fresh timestamp
                    "created_at": time.time()
                }

            return result

        # Store metadata
        wrapper._cache_duration = duration
        return wrapper

    return decorator


def requires(*roles: str, check_func: Optional[Callable] = None):
    """
    Authentication/authorization decorator with role-based access control.

    IMPORTANT: This decorator requires you to provide a check_func that validates
    user authentication and roles. Without it, the decorator will deny all access
    (fail-safe/fail-closed security pattern).

    Args:
        *roles: Required roles (e.g., "admin", "user", "moderator")
        check_func: Custom authentication check function that should:
                   - Accept (*args, **kwargs) from the route handler
                   - Return True if user is authenticated and has required role(s)
                   - Return False if authentication/authorization fails
                   - If roles are specified, check if user has at least one of them

    Usage:
        # With role checking
        @requires("admin", check_func=lambda self: user_has_role(self.request, "admin"))
        def delete(self):
            return {"deleted": True}

        # Multiple roles (user needs at least one)
        @requires("admin", "moderator", check_func=lambda self: user_has_any_role(self.request, ["admin", "moderator"]))
        def put(self):
            return {"updated": True}

        # Authentication only (no role check)
        @requires(check_func=lambda self: is_authenticated(self.request))
        def get(self):
            return {"data": "..."}

    Returns:
        401 Unauthorized if authentication fails
        403 Forbidden if authorization/role check fails
        500 Internal Server Error if check_func is not provided (fail-safe)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Security: Fail-safe pattern - if roles are specified but no check_func,
            # deny access by default instead of allowing it
            if roles and not check_func:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(
                    f"@requires decorator on {func.__name__} specifies roles {roles} "
                    f"but no check_func is provided. Access denied by default. "
                    f"Please implement check_func to enable authorization."
                )
                return {
                    "error": "Internal Server Error",
                    "message": "Authorization not properly configured"
                }, 500

            # If custom check function provided, use it
            if check_func:
                try:
                    # Call check function with route handler arguments
                    is_authorized = check_func(*args, **kwargs)

                    if not is_authorized:
                        # Security logging: Log auth/authz failure
                        try:
                            from reroute.logging import security_logger
                            if roles:
                                security_logger.log_authz_failure(
                                    resource=func.__name__,
                                    required_roles=list(roles)
                                )
                            else:
                                security_logger.log_auth_failure(
                                    reason="Authentication check returned False",
                                    resource=func.__name__
                                )
                        except ImportError:
                            pass

                        # If roles were specified, this is an authorization failure (403)
                        # If no roles, this is an authentication failure (401)
                        if roles:
                            return {
                                "error": "Forbidden",
                                "message": f"Requires one of the following roles: {', '.join(roles)}"
                            }, 403
                        else:
                            return {
                                "error": "Unauthorized",
                                "message": "Authentication required"
                            }, 401

                except Exception as e:
                    # Security logging: Log security error
                    try:
                        from reroute.logging import security_logger
                        security_logger.log_security_error(
                            error=str(e),
                            context=f"Authorization check for {func.__name__}"
                        )
                    except ImportError:
                        pass

                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Authorization check failed with exception: {e}", exc_info=True)
                    return {
                        "error": "Internal Server Error",
                        "message": "Authorization check failed"
                    }, 500

            # Authorization successful, execute the function
            return func(*args, **kwargs)

        # Store metadata for documentation
        wrapper._required_roles = roles
        wrapper._auth_check = check_func
        return wrapper

    return decorator


def validate(schema: Dict[str, type] = None, validator_func: Optional[Callable] = None, required_fields: List[str] = None):
    """
    Request validation decorator.

    Args:
        schema: Validation schema (dict mapping field names to types)
        validator_func: Custom validation function that returns (bool, error_message)
        required_fields: List of required field names

    Usage:
        @validate(schema={"name": str, "age": int, "email": str})
        def post(self, data):
            return {"created": True}

        @validate(required_fields=["email", "password"])
        def post(self, data):
            return {"created": True}

        @validate(validator_func=lambda data: (
            ("@" in data.get("email", ""), "Invalid email format")
            if "email" in data else (True, None)
        ))
        def post(self, data):
            return {"created": True}

    Returns:
        400 Bad Request if validation fails

    Note:
        Validation looks for data in kwargs under common parameter names:
        'data', 'body', 'json', 'user', 'item', etc.
        For Pydantic models, use the params system (Body, Query, etc.) instead.
    """
    import inspect
    import logging

    logger = logging.getLogger(__name__)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Try to find request data in kwargs
            # Common parameter names used in route handlers
            data_param_names = ['data', 'body', 'json', 'payload', 'request_data',
                               'user', 'item', 'model', 'params']

            request_data = None
            data_param_name = None

            # Search for data in kwargs
            for param_name in data_param_names:
                if param_name in kwargs:
                    request_data = kwargs[param_name]
                    data_param_name = param_name
                    break

            # If no data found and schema/required_fields specified, try to get from Pydantic model
            if request_data is None:
                # Check if any kwarg is a Pydantic model (has model_dump method)
                for param_name, param_value in kwargs.items():
                    if hasattr(param_value, 'model_dump'):
                        request_data = param_value.model_dump()
                        data_param_name = param_name
                        break
                    elif hasattr(param_value, 'dict'):  # Pydantic v1
                        request_data = param_value.dict()
                        data_param_name = param_name
                        break

            # Convert dict-like objects to dict for validation
            if request_data is not None and hasattr(request_data, '__dict__') and not isinstance(request_data, dict):
                try:
                    request_data = vars(request_data)
                except TypeError:
                    pass  # Keep original if conversion fails

            # Perform validation if data was found
            if request_data is not None:
                # Validate required fields
                if required_fields:
                    missing_fields = [field for field in required_fields if field not in request_data]
                    if missing_fields:
                        return {
                            "error": "Validation failed",
                            "message": f"Missing required fields: {', '.join(missing_fields)}",
                            "missing_fields": missing_fields
                        }, 400

                # Validate schema (type checking)
                if schema:
                    validation_errors = []
                    for field_name, expected_type in schema.items():
                        if field_name in request_data:
                            field_value = request_data[field_name]
                            # Check type
                            if not isinstance(field_value, expected_type):
                                actual_type = type(field_value).__name__
                                expected_type_name = expected_type.__name__
                                validation_errors.append(
                                    f"Field '{field_name}': expected {expected_type_name}, got {actual_type}"
                                )

                    if validation_errors:
                        return {
                            "error": "Validation failed",
                            "message": "Type validation errors",
                            "validation_errors": validation_errors
                        }, 400

                # Custom validator function
                if validator_func:
                    try:
                        # Validator should return (is_valid: bool, error_message: str)
                        if len(args) > 0:
                            # If called as method (self is first arg)
                            result = validator_func(args[0], request_data)
                        else:
                            result = validator_func(request_data)

                        # Handle different return types
                        if isinstance(result, tuple):
                            is_valid, error_message = result
                        else:
                            is_valid = bool(result)
                            error_message = "Custom validation failed"

                        if not is_valid:
                            return {
                                "error": "Validation failed",
                                "message": error_message or "Custom validation failed"
                            }, 400
                    except Exception as e:
                        logger.error(f"Validator function error: {e}")
                        return {
                            "error": "Validation error",
                            "message": f"Validator function raised exception: {str(e)}"
                        }, 400

            elif schema or required_fields:
                # Data is required but not found
                logger.warning(
                    f"@validate decorator on {func.__name__} couldn't find request data. "
                    f"Looking for kwargs: {', '.join(data_param_names)}"
                )

            # All validation passed or no validation needed
            return func(*args, **kwargs)

        # Store metadata for documentation and potential auto-validation
        wrapper._validation_schema = schema
        wrapper._validator_func = validator_func
        wrapper._required_fields = required_fields
        return wrapper

    return decorator


def timeout(seconds: int):
    """
    Request timeout decorator.

    Args:
        seconds: Maximum execution time in seconds

    Usage:
        @timeout(5)  # 5 second timeout
        def get(self):
            return {"data": self.slow_operation()}

        @timeout(30)
        async def post(self):  # Works with async too
            return await self.process_large_file()

    Returns:
        408 Request Timeout if execution exceeds limit

    Note:
        - Async handlers: Uses asyncio.wait_for() for true timeout
        - Sync handlers on Unix: Uses signal.alarm() for true timeout
        - Sync handlers on Windows: Thread-based timeout (function continues in background)

        Recommendation: Use async handlers for guaranteed timeout behavior.
    """
    import inspect
    import asyncio
    import platform
    import sys
    import logging

    logger = logging.getLogger(__name__)

    def decorator(func: Callable) -> Callable:
        # Handle async functions separately
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    # Use asyncio.wait_for for proper async timeout
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=seconds
                    )
                    return result
                except asyncio.TimeoutError:
                    return {
                        "error": "Request timeout",
                        "limit": f"{seconds}s"
                    }, 408

            async_wrapper._timeout = seconds
            return async_wrapper

        # Handle sync functions
        # Use signal-based timeout on Unix systems for true timeout
        if platform.system() != 'Windows' and hasattr(sys.modules.get('signal', None), 'alarm'):
            import signal

            @functools.wraps(func)
            def unix_wrapper(*args, **kwargs):
                def timeout_handler(signum, frame):
                    raise TimeoutError(f"Function exceeded {seconds}s timeout")

                # Set signal alarm
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(seconds)

                try:
                    result = func(*args, **kwargs)
                    signal.alarm(0)  # Cancel alarm
                    return result
                except TimeoutError as e:
                    signal.alarm(0)  # Cancel alarm
                    return {
                        "error": "Request timeout",
                        "limit": f"{seconds}s",
                        "message": str(e)
                    }, 408
                except Exception as e:
                    signal.alarm(0)  # Cancel alarm
                    raise
                finally:
                    # Restore old handler
                    signal.signal(signal.SIGALRM, old_handler)

            unix_wrapper._timeout = seconds
            return unix_wrapper

        # Windows fallback: Thread-based timeout (function continues in background)
        @functools.wraps(func)
        def windows_wrapper(*args, **kwargs):
            result_container = {}
            exception_container = {}

            def target():
                try:
                    result_container['result'] = func(*args, **kwargs)
                except Exception as e:
                    exception_container['exception'] = e

            # Run function in thread with timeout
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout=seconds)

            if thread.is_alive():
                # Function is still running - timeout occurred
                # WARNING: Thread cannot be killed, continues in background
                logger.warning(
                    f"Timeout occurred for {func.__name__} but function continues in background "
                    f"(Windows limitation). Consider using async handlers for true timeout."
                )
                return {
                    "error": "Request timeout",
                    "limit": f"{seconds}s",
                    "warning": "Function continues in background (Windows limitation)"
                }, 408

            # Check if exception occurred
            if 'exception' in exception_container:
                raise exception_container['exception']

            return result_container.get('result')

        windows_wrapper._timeout = seconds
        return windows_wrapper

    return decorator


def log_requests(logger_func: Optional[Callable] = None):
    """
    Request logging decorator.

    Args:
        logger_func: Custom logging function (default: prints to console)

    Usage:
        @log_requests()
        def get(self):
            return {"data": "..."}

        import logging
        @log_requests(logger_func=logging.info)
        def post(self):
            return {"created": True}
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            # Log request start
            log_msg = f"[{datetime.now().isoformat()}] {func.__name__} started"
            if logger_func:
                logger_func(log_msg)
            else:
                print(log_msg)

            # Execute function
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time

                # Log success
                log_msg = f"[{datetime.now().isoformat()}] {func.__name__} completed in {elapsed:.3f}s"
                if logger_func:
                    logger_func(log_msg)
                else:
                    print(log_msg)

                return result

            except Exception as e:
                elapsed = time.time() - start_time

                # Log error
                log_msg = f"[{datetime.now().isoformat()}] {func.__name__} failed in {elapsed:.3f}s: {str(e)}"
                if logger_func:
                    logger_func(log_msg)
                else:
                    print(log_msg)

                raise

        return wrapper

    return decorator


# Utility functions

def clear_cache(pattern: str = None):
    """
    Clear cached responses.

    Args:
        pattern: Optional pattern to match cache keys (clears all if None)

    Usage:
        clear_cache()  # Clear all caches
        clear_cache("user_")  # Clear all user-related caches
    """
    with _cache_lock:
        if pattern:
            keys_to_delete = [k for k in _cache_storage.keys() if pattern in k]
            for key in keys_to_delete:
                del _cache_storage[key]
        else:
            _cache_storage.clear()


def clear_rate_limits():
    """
    Clear all rate limit counters.

    Usage:
        clear_rate_limits()  # Reset all rate limits
    """
    global _rate_limit_storage
    _rate_limit_storage = RateLimitStorage()


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.

    Returns:
        Dictionary with cache stats (size, keys, etc.)
    """
    with _cache_lock:
        current_time = time.time()
        active_caches = sum(
            1 for v in _cache_storage.values()
            if v["expires_at"] > current_time
        )

        return {
            "total_keys": len(_cache_storage),
            "active_caches": active_caches,
            "expired_caches": len(_cache_storage) - active_caches
        }


# =============================================================================
# Standardized Error Response Helper
# =============================================================================

def error_response(
    message: str,
    status_code: int = 400,
    error_type: str = "Error",
    details: Optional[Dict[str, Any]] = None
) -> tuple:
    """
    Create a standardized error response.

    Provides consistent error format across all REROUTE endpoints.

    Args:
        message: Human-readable error message
        status_code: HTTP status code (default: 400)
        error_type: Error category (default: "Error")
        details: Optional additional error details

    Returns:
        Tuple of (error_dict, status_code)

    Usage:
        from reroute.decorators import error_response

        @rate_limit("5/min")
        def post(self, data):
            if not data.get("email"):
                return error_response("Email is required", 400, "ValidationError")

            if not is_valid_email(data["email"]):
                return error_response(
                    "Invalid email format",
                    400,
                    "ValidationError",
                    details={"field": "email", "value": data["email"]}
                )

            return {"success": True}
    """
    response = {
        "error": error_type,
        "message": message
    }

    if details:
        response["details"] = details

    return response, status_code


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    # Decorators
    "rate_limit",
    "cache",
    "requires",
    "validate",
    "timeout",
    "log_requests",
    # Utilities
    "clear_cache",
    "clear_rate_limits",
    "get_cache_stats",
    "error_response",
    # Constants
    "MAX_CACHE_SIZE",
    "MAX_RATE_LIMIT_KEYS",
]
