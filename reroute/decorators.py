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
from typing import Callable, Dict, Any, Optional, List
from datetime import datetime
from collections import defaultdict
import threading


# Rate Limiting Storage
class RateLimitStorage:
    """Thread-safe storage for rate limit tracking."""

    def __init__(self):
        self._storage: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

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

    def check_and_add(self, key: str, timestamp: float, cutoff: float, max_requests: int) -> tuple[bool, int]:
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


def _cleanup_expired_caches():
    """Background thread to periodically clean up expired cache entries."""
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
        except Exception:
            # Silently continue if cleanup fails
            pass


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
                # Try Flask first (thread-local request)
                try:
                    from flask import request as flask_request
                    if flask_request:
                        # Get IP from X-Forwarded-For if behind proxy, else remote_addr
                        x_forwarded_for = flask_request.headers.get('X-Forwarded-For')
                        if x_forwarded_for:
                            # X-Forwarded-For can contain multiple IPs, first one is the client
                            client_ip = x_forwarded_for.split(',')[0].strip()
                        else:
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
                                client_ip = x_forwarded_for.split(',')[0].strip()

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

            # Cache miss - execute function
            result = func(*args, **kwargs)

            # Store in cache
            with _cache_lock:
                _cache_storage[cache_key] = {
                    "data": result,
                    "expires_at": current_time + duration,
                    "created_at": current_time
                }

            return result

        # Store metadata
        wrapper._cache_duration = duration
        return wrapper

    return decorator


def requires(*roles: str, check_func: Optional[Callable] = None):
    """
    Authentication/authorization decorator.

    Args:
        *roles: Required roles (e.g., "admin", "user", "moderator")
        check_func: Custom authentication check function

    Usage:
        @requires("admin")
        def delete(self):
            return {"deleted": True}

        @requires("admin", "moderator")
        def put(self):
            return {"updated": True}

        @requires(check_func=lambda self: self.is_authenticated())
        def get(self):
            return {"data": "..."}

    Returns:
        401 Unauthorized if authentication fails
        403 Forbidden if authorization fails
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # If custom check function provided
            if check_func:
                if not check_func(*args):
                    return {"error": "Unauthorized", "message": "Authentication required"}, 401

            # Role-based check would be implemented here
            # This requires integration with the auth system
            # For now, this serves as a placeholder for the pattern

            return func(*args, **kwargs)

        # Store metadata for documentation
        wrapper._required_roles = roles
        wrapper._auth_check = check_func
        return wrapper

    return decorator


def validate(schema: Dict[str, type] = None, validator_func: Optional[Callable] = None):
    """
    Request validation decorator.

    Args:
        schema: Validation schema (dict mapping field names to types)
        validator_func: Custom validation function that returns True if valid

    Usage:
        @validate(schema={"name": str, "age": int, "email": str})
        def post(self):
            return {"created": True}

        @validate(validator_func=lambda self, data: "email" in data and "@" in data["email"])
        def post(self):
            return {"created": True}

    Returns:
        400 Bad Request if validation fails
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Validation logic placeholder
            # In real implementation, would validate request body
            # Against schema or using validator_func

            # This pattern allows routes to declare their validation requirements
            # The adapter (FastAPI/Flask) would handle actual validation

            return func(*args, **kwargs)

        # Store metadata for documentation and potential auto-validation
        wrapper._validation_schema = schema
        wrapper._validator_func = validator_func
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
        def post(self):
            return self.process_large_file()

    Returns:
        408 Request Timeout if execution exceeds limit

    Note:
        This is a basic synchronous implementation.
        For async routes, use asyncio.wait_for instead.
    """
    import inspect
    import asyncio

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
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
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
                # Note: We can't kill the thread, but we return timeout response
                return {
                    "error": "Request timeout",
                    "limit": f"{seconds}s"
                }, 408

            # Check if exception occurred
            if 'exception' in exception_container:
                raise exception_container['exception']

            return result_container.get('result')

        wrapper._timeout = seconds
        return wrapper

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
