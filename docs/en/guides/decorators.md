# Decorators

Use decorators to add functionality to your routes without modifying handler logic.

## Rate Limiting

Control request frequency per endpoint.

```python
from reroute import RouteBase
from reroute.decorators import rate_limit

class MyRoutes(RouteBase):
    # Global rate limit
    @rate_limit("5/min")
    def post(self):
        return {"created": True}

    # Per-IP rate limit (v0.1.6+)
    @rate_limit("10/hour", per_ip=True)
    def get(self):
        return {"data": "..."}

    # Custom key function
    @rate_limit("100/day", key_func=lambda self: f"user_{self.user_id}")
    def delete(self):
        return {"deleted": True}
```

**Supported periods:** `sec`, `min`, `hour`, `day`

**New in v0.1.6:** Per-IP rate limiting with automatic IP extraction from request headers.

## Caching

Cache responses to improve performance.

```python
from reroute import RouteBase
from reroute.decorators import cache

class MyRoutes(RouteBase):
    @cache(duration=60)  # Cache for 60 seconds
    def get(self):
        return {"data": "expensive_operation_result"}

    # Custom cache key
    @cache(duration=300, key_func=lambda self: f"user_{self.user_id}")
    def get(self):
        return {"user_data": "..."}
```

**Note:** Cache is in-memory. For production, consider using Redis or a distributed cache system.

## Request Validation

### Option 1: @validate Decorator (New in v0.1.6)

Simple validation for basic use cases.

```python
from reroute import RouteBase
from reroute.decorators import validate

class MyRoutes(RouteBase):
    # Type validation
    @validate(schema={"name": str, "age": int, "email": str})
    def post(self, data):
        return {"created": True, "data": data}

    # Required fields
    @validate(required_fields=["email", "password"])
    def post(self, data):
        return {"authenticated": True}

    # Custom validator
    @validate(validator_func=lambda data: (
        ("@" in data.get("email", ""), "Invalid email format")
    ))
    def post(self, data):
        return {"validated": True}

    # Combined validation
    @validate(
        schema={"name": str, "age": int},
        required_fields=["email"],
        validator_func=lambda data: (data["age"] >= 18, "Must be 18+")
    )
    def post(self, data):
        return {"account_created": True}
```

**When to use:**
- Simple type checking
- Required field validation
- Quick custom validators

### Option 2: Pydantic Models (Recommended)

For complex validation with better type safety and IDE support.

```python
from reroute import RouteBase
from reroute.params import Body
from pydantic import BaseModel, field_validator, EmailStr

class UserCreate(BaseModel):
    name: str
    age: int
    email: EmailStr

    @field_validator('age')
    def validate_age(cls, v):
        if v < 18:
            raise ValueError('User must be 18 or older')
        return v

class MyRoutes(RouteBase):
    def post(self, user: UserCreate = Body()):
        """Automatically validates request body"""
        return {"validated": True, "user": user.model_dump()}
```

**Advantages:**
- Automatic validation and detailed error messages
- Type hints and IDE autocomplete
- OpenAPI schema generation
- Advanced field validators
- Nested model support

## Request Timeout

Prevent long-running requests from blocking your application.

```python
from reroute import RouteBase
from reroute.decorators import timeout
import asyncio
import time

class MyRoutes(RouteBase):
    # Async handler (recommended - works everywhere)
    @timeout(5)
    async def get(self):
        await asyncio.sleep(10)  # Will timeout
        return {"data": "..."}

    # Sync handler (Unix: true timeout, Windows: best effort)
    @timeout(30)
    def post(self):
        time.sleep(60)  # Will timeout
        return {"processed": True}
```

**Platform Support:**
- **Async handlers**: Full timeout support on all platforms (recommended)
- **Sync handlers on Unix/Linux/Mac**: True timeout using signals
- **Sync handlers on Windows**: Returns timeout response but function continues in background

!!! tip "Best Practice"
    Use async handlers (`async def`) for guaranteed timeout behavior across all platforms.

## Authentication & Authorization

Protect routes with role-based access control.

```python
from reroute import RouteBase
from reroute.decorators import requires

class MyRoutes(RouteBase):
    # Role-based authorization
    @requires("admin")
    def delete(self):
        return {"deleted": True}

    # Multiple roles (OR logic)
    @requires("admin", "moderator")
    def put(self):
        return {"updated": True}

    # Custom authentication check
    @requires(check_func=lambda self: self.is_authenticated())
    def get(self):
        return {"data": "protected"}
```

**Returns:**
- `401 Unauthorized` if authentication fails
- `403 Forbidden` if user lacks required role

**Note:** Requires integration with your authentication system.

## Request Logging

Automatically log request details.

```python
from reroute import RouteBase
from reroute.decorators import log_requests
import logging

logger = logging.getLogger(__name__)

class MyRoutes(RouteBase):
    # Default logging (prints to console)
    @log_requests()
    def get(self):
        return {"data": "..."}

    # Custom logger
    @log_requests(logger_func=logger.info)
    def post(self):
        return {"created": True}
```

## Combining Decorators

Stack multiple decorators for comprehensive route protection.

```python
from reroute import RouteBase
from reroute.decorators import rate_limit, cache, validate, timeout, requires
from reroute.params import Body
from pydantic import BaseModel

class UserCreate(BaseModel):
    email: str
    name: str
    age: int

class MyRoutes(RouteBase):
    # Multiple decorators on read endpoint
    @rate_limit("10/min", per_ip=True)
    @cache(duration=30)
    @timeout(5)
    async def get(self):
        """Rate-limited, cached, with timeout"""
        return {"data": "..."}

    # Protected write endpoint with validation
    @requires("admin")
    @rate_limit("5/min")
    @validate(required_fields=["email", "name"])
    @timeout(10)
    def post(self, data):
        """Admin-only, rate-limited, validated, with timeout"""
        return {"created": True, "data": data}

    # Best practice: Pydantic validation + decorators
    @rate_limit("10/min", per_ip=True)
    @requires("user")
    @timeout(15)
    async def put(self, user: UserCreate = Body()):
        """Authenticated, rate-limited, fully validated, with timeout"""
        return {"updated": True, "user": user.model_dump()}
```

**Decorator Execution Order:**

Decorators are applied from **bottom to top** (closest to function first):

```python
@cache(60)        # 3. Response cached
@rate_limit("5/min")  # 2. Check rate limit
@timeout(10)      # 1. Start timeout timer
def get(self):
    return {"data": "..."}
```

!!! warning "Decorator Order Matters"
    Place `@timeout` closest to the function for accurate timeout measurement.
    Place `@cache` outermost to cache the final response (after rate limits pass).

## Best Practices

### 1. Choose the Right Validation Approach

- **@validate decorator**: Quick type checks and required fields
- **Pydantic models**: Complex validation, nested data, OpenAPI docs

### 2. Use Async Handlers When Possible

```python
# ✅ Good: Async with timeout
@timeout(5)
async def get(self):
    await asyncio.sleep(1)
    return {"data": "..."}

# ⚠️ OK on Unix, limited on Windows
@timeout(5)
def get(self):
    time.sleep(1)
    return {"data": "..."}
```

### 3. Layer Security Decorators

```python
@requires("admin")        # Authentication first
@rate_limit("5/min")      # Then rate limiting
@validate(schema={...})   # Then validation
@timeout(10)              # Finally timeout
def sensitive_operation(self, data):
    return {"status": "success"}
```

### 4. Per-IP Rate Limiting for Public APIs

```python
# ✅ Good: Prevent abuse per client
@rate_limit("100/hour", per_ip=True)
def public_api(self):
    return {"data": "..."}

# ❌ Bad: Single shared limit for all users
@rate_limit("100/hour")
def public_api(self):
    return {"data": "..."}
```

### 5. Cache Expensive Operations

```python
@cache(duration=300)  # 5 minutes
async def expensive_query(self):
    # Database query, API call, etc.
    return await self.fetch_from_database()
```

## Learn More

- [API Reference](../api/decorators.md) - Complete decorator documentation
- [Security Guide](security.md) - Best practices for securing routes
- [Testing Guide](testing.md) - How to test decorated routes
