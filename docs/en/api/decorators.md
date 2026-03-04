# Decorators API

Built-in decorators for REROUTE routes.

## rate_limit

Limit request rate globally or per IP address.

```python
from reroute.decorators import rate_limit

# Global rate limit
@rate_limit("5/min")
def post(self):
    return {"created": True}

# Per-IP rate limit (v0.1.6+)
@rate_limit("10/hour", per_ip=True)
def post(self):
    return {"created": True}

# Custom key function
@rate_limit("100/day", key_func=lambda self: f"user_{self.get_user_id()}")
def delete(self):
    return {"deleted": True}
```

**Parameters:**
- `limit` (str): Rate limit string (e.g., "5/min", "100/hour", "1000/day")
- `key_func` (Callable, optional): Function to generate custom rate limit key
- `per_ip` (bool, optional): Enable per-IP rate limiting (default: False). **New in v0.1.6**

**Returns:**
- `429 Too Many Requests` if rate limit exceeded

**Note:** Per-IP rate limiting automatically extracts client IP from:
- Flask: `request.remote_addr` or `X-Forwarded-For` header
- FastAPI: `request.client.host` or `X-Forwarded-For` header

## cache

Cache responses for a duration.

```python
from reroute.decorators import cache

@cache(duration=60)
def get(self):
    return {"data": "cached"}
```

**Parameters:**
- `duration` (int): Cache duration in seconds

## validate

Validate request data with schema, required fields, or custom validators. **Fully implemented in v0.1.6.**

```python
from reroute.decorators import validate

# Schema validation (type checking)
@validate(schema={"name": str, "age": int, "email": str})
def post(self, data):
    return {"created": True}

# Required fields validation
@validate(required_fields=["email", "password"])
def post(self, data):
    return {"token": "abc123"}

# Custom validator function
@validate(validator_func=lambda data: (
    ("@" in data.get("email", ""), "Invalid email format")
    if "email" in data else (True, None)
))
def post(self, data):
    return {"registered": True}

# Combined validation
@validate(
    schema={"name": str, "age": int},
    required_fields=["email"],
    validator_func=lambda data: (data["age"] >= 18, "Must be 18+")
)
def post(self, data):
    return {"account_created": True}
```

**Parameters:**
- `schema` (Dict[str, type], optional): Type validation schema mapping field names to types
- `required_fields` (List[str], optional): List of required field names
- `validator_func` (Callable, optional): Custom validator returning `(bool, error_message)` or just `bool`

**Returns:**
- `400 Bad Request` if validation fails with detailed error messages

**Note:** The decorator searches for data in kwargs under common parameter names: `data`, `body`, `json`, `payload`, `user`, `item`, etc. Also supports Pydantic model extraction.

### Alternative: Pydantic Models (Recommended)

For complex validation, use Pydantic models with the params system:

```python
from reroute import RouteBase
from reroute.params import Body
from pydantic import BaseModel, field_validator

class UserCreate(BaseModel):
    name: str
    age: int

    @field_validator('age')
    def validate_age(cls, v):
        if v < 18:
            raise ValueError('User must be 18 or older')
        return v

class MyRoutes(RouteBase):
    def post(self, user: UserCreate = Body()):
        """Request body is automatically validated"""
        return {"validated": True, "user": user.model_dump()}
```

**Advantages of Pydantic:**
- Automatic validation and error messages
- Type hints and IDE autocomplete
- OpenAPI schema generation
- Advanced field validators

See [Database Examples](../examples/database.md) for more validation patterns.

## timeout

Set maximum execution time for route handlers. **Enhanced in v0.1.6.**

```python
from reroute.decorators import timeout

# Async handler (recommended - works everywhere)
@timeout(5)
async def get(self):
    await asyncio.sleep(10)  # Will timeout after 5 seconds
    return {"data": "..."}

# Sync handler
@timeout(30)
def post(self):
    time.sleep(60)  # Will timeout after 30 seconds
    return {"processed": True}
```

**Parameters:**
- `seconds` (int): Maximum execution time in seconds

**Returns:**
- `408 Request Timeout` if execution exceeds limit

**Platform Behavior:**
- **Async handlers**: Uses `asyncio.wait_for()` for true timeout (all platforms)
- **Sync handlers on Unix/Linux/Mac**: Uses `signal.alarm()` for true timeout (execution is stopped)
- **Sync handlers on Windows**: Thread-based timeout (function continues in background)

!!! tip "Recommendation"
    Use async handlers for guaranteed timeout behavior across all platforms.

## requires

Authentication and authorization decorator with fail-safe design. **Enhanced in v0.2.0.**

```python
from reroute.decorators import requires

# Role-based authorization with check function
@requires("admin", check_func=lambda self: self.user.has_role("admin"))
def delete(self):
    return {"deleted": True}

# Multiple roles (OR logic) - user needs at least one
@requires("admin", "moderator", check_func=lambda self: self.user.has_any_role(["admin", "moderator"]))
def put(self):
    return {"updated": True}

# Authentication only (no role check)
@requires(check_func=lambda self: self.is_authenticated())
def get(self):
    return {"data": "..."}
```

**Parameters:**
- `*roles` (str): Required roles for access
- `check_func` (Callable): Authentication/authorization check function that returns `True` or `False`

**Returns:**
- `401 Unauthorized` if authentication fails (no roles specified)
- `403 Forbidden` if authorization fails (roles specified but check failed)

!!! important "check_func Required for Role Checks"
    When specifying roles, you must provide a `check_func` that validates the user's roles. This ensures explicit authorization logic in your application.

**Example with Flask:**
```python
from reroute.decorators import requires
from flask import g

def is_admin(self):
    return hasattr(g, 'user') and g.user.role == 'admin'

@requires("admin", check_func=is_admin)
def delete(self):
    return {"deleted": True}
```

**Example with FastAPI:**
```python
from reroute.decorators import requires

def check_auth(self, request=None):
    # Your JWT/session validation logic
    return request and hasattr(request.state, 'user')

@requires(check_func=check_auth)
def get(self, request):
    return {"user": request.state.user}
```

## log_requests

Automatic request logging with customizable logger.

```python
from reroute.decorators import log_requests
import logging

@log_requests()
def get(self):
    return {"data": "..."}

# With custom logger function
@log_requests(logger_func=logging.info)
def post(self):
    return {"created": True}
```

**Parameters:**
- `logger_func` (Callable, optional): Custom logging function
