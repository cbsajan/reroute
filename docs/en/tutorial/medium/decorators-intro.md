---
difficulty: medium
time: 25 minutes
prerequisites:
  - link: ../../start-here.md
  - link: ../easy/http-methods.md
  - link: crud-app.md
next: error-handling.md
---

# Decorators

Learn how to use and create decorators to add powerful functionality like rate limiting, caching, and logging to your REROUTE API.

## What You'll Learn

- What decorators are and how they work
- Built-in REROUTE decorators (@cache, @rate_limit)
- Creating custom decorators
- Combining multiple decorators
- Performance optimization with caching
- API protection with rate limiting

## Prerequisites

- Completed [HTTP Methods](../easy/http-methods.md) tutorial
- Completed [CRUD Application](crud-app.md) tutorial
- Understanding of Python functions
- Working REROUTE project

---

## What are Decorators?

Decorators are functions that modify the behavior of other functions without changing their code. They "wrap" your functions to add extra functionality.

**Think of decorators as:**
- Gift wrapping around a present (your function)
- Middleware for your route handlers
- Plugins that add features automatically

**Example:**
```python
@cache(duration=60)  # This is a decorator
def get(self):
    # Your function code
    return {"data": "expensive computation"}
```

The `@cache` decorator wraps your `get` function to add caching behavior.

---

## Step 1: Create Demo Project

```bash
reroute init decorators-demo --framework fastapi
cd decorators-demo
```

Create a test route:

```bash
reroute create route --path /api --name ApiRoutes --methods GET,POST
```

---

## Step 2: Caching Decorator

Caching stores the result of expensive operations and returns the cached result on subsequent calls instead of re-computing.

### Basic Caching

Edit `app/routes/api/page.py`:

```python
import time
import asyncio
from reroute import RouteBase
from reroute.decorators import cache
from reroute.params import Query

class ApiRoutes(RouteBase):
    """API endpoints demonstrating decorators."""
    tag = "Decorators Demo"

    @cache(duration=300)  # Cache for 5 minutes
    def get(self, slow: bool = Query(False, description="Simulate slow operation")):
        """
        Get expensive data (cached for 5 minutes).

        - **slow**: If true, simulate 2-second delay
        """
        if slow:
            time.sleep(2)  # Simulate expensive operation

        return {
            "message": "This response is cached for 5 minutes",
            "timestamp": time.time(),
            "slow_operation": slow
        }

    @cache(duration=60, key_prefix="custom")  # Custom cache key
    def get_custom_key(self):
        """Cache with custom key prefix."""
        return {"data": "Cached with custom key", "time": time.time()}
```

### Test Caching

**First call (slow):**
```bash
curl "http://localhost:7376/api?slow=true"  # Takes 2 seconds
```

**Response 1:**
```json
{
  "message": "This response is cached for 5 minutes",
  "timestamp": 1234567890.123,
  "slow_operation": true
}
```

**Second call (instant - from cache):**
```bash
curl "http://localhost:7376/api?slow=true"  # Instant!
```

**Response 2:** (Same timestamp as first - from cache!)
```json
{
  "message": "This response is cached for 5 minutes",
  "timestamp": 1234567890.123,  // Same as first call!
  "slow_operation": true
}
```

`★ Insight ─────────────────────────────────────`
**Cache Hit vs Cache Miss**:
- **Cache Miss** (first call): Function executes, result stored in cache
- **Cache Hit** (subsequent calls): Result returned from cache without executing function

This dramatically improves performance for expensive operations like database queries, API calls, or complex computations. The 2-second delay only happens once!
`─────────────────────────────────────────────────`

### Cache with Parameters

Caching works with function parameters automatically:

```python
@cache(duration=300)
def get_products(self, category: str = Query(None)):
    """Different categories cached separately."""
    # Each category value has its own cache entry
    return {"category": category, "products": [...]}

# /api/products?category=electronics  # Cached separately
# /api/products?category=clothing     # Cached separately
```

### Cache Invalidation

Sometimes you need to clear cache manually:

```python
from reroute.decorators import cache

# In your route
@cache(duration=300, cache_key="user_data:{user_id}")
def get_user(self, user_id: int):
    return fetch_user_from_db(user_id)

# After updating user
def post_user(self, user_id: int, data: dict):
    update_user_in_db(user_id, data)
    # Clear the cache for this user
    cache.clear(f"user_data:{user_id}")
    return {"updated": True}
```

---

## Step 3: Rate Limiting Decorator

Rate limiting protects your API from abuse by limiting how many requests can be made in a time period.

### Basic Rate Limiting

Edit `app/routes/api/page.py`:

```python
from reroute.decorators import rate_limit

class ApiRoutes(RouteBase):

    @rate_limit("10/minute")  # Max 10 requests per minute
    def post(self, data: dict = Body(...)):
        """
        Create resource (rate limited).

        - Max 10 requests per minute per IP
        """
        return {"created": True, "data": data}

    @rate_limit("100/hour")  # Max 100 requests per hour
    def get_heavy(self):
        """Expensive endpoint with stricter limit."""
        return {"data": "heavy computation result"}
```

### Test Rate Limiting

**First 10 requests succeed:**
```bash
for i in {1..10}; do
  curl -X POST http://localhost:7376/api \
    -H "Content-Type: application/json" \
    -d '{"test": "'$i'"}'
done
```

All succeed ✅

**11th request fails:**
```bash
curl -X POST http://localhost:7376/api \
  -H "Content-Type: application/json" \
  -d '{"test": "11"}'
```

**Response:** (429 Too Many Requests)
```json
{
  "detail": "Rate limit exceeded: 10/minute"
}
```

### Rate Limit Patterns

```python
# Different limits for different endpoints
@rate_limit("10/minute")
def post_sensitive(self):
    """Strict limit for sensitive operations."""
    pass

@rate_limit("60/minute")
def get_search(self):
    """Relaxed limit for read operations."""
    pass

@rate_limit("1000/day")
def get_public(self):
    """Daily limit for public API."""
    pass
```

### Rate Limit by User

Rate limit based on user ID instead of IP:

```python
from reroute.params import Header

@rate_limit("100/hour", key_func=lambda r: r.headers.get("user-id"))
def get_user_content(self, user_id: str = Header(...)):
    """Rate limit per user, not per IP."""
    return {"user": user_id, "content": [...]}
```

---

## Step 4: Logging Decorator

Create a custom decorator to log requests:

```python
from functools import wraps
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def log_execution(func):
    """Decorator to log function execution time and details."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        # Log incoming request
        logger.info(f"→ {func.__name__} called with args: {kwargs}")

        try:
            # Execute function
            result = func(*args, **kwargs)

            # Calculate execution time
            execution_time = time.time() - start_time

            # Log success
            logger.info(
                f"✓ {func.__name__} completed in {execution_time:.3f}s"
            )

            return result

        except Exception as e:
            execution_time = time.time() - start_time

            # Log error
            logger.error(
                f"✗ {func.__name__} failed after {execution_time:.3f}s: {str(e)}"
            )
            raise

    return wrapper

# Usage in routes
class ApiRoutes(RouteBase):

    @log_execution
    @cache(duration=60)
    def get(self):
        return {"data": "logged and cached"}

    @log_execution
    def post(self, data: dict = Body(...)):
        return {"created": True, "data": data}
```

**Server logs output:**
```
2025-03-03 10:15:23 - __main__ - INFO - → get called with args: {}
2025-03-03 10:15:23 - __main__ - INFO - ✓ get completed in 0.001s

2025-03-03 10:15:30 - __main__ - INFO - → post called with args: {'data': {'test': 'value'}}
2025-03-03 10:15:30 - __main__ - INFO - ✓ post completed in 0.002s
```

---

## Step 5: Authentication Decorator

Create a decorator to protect routes with authentication:

```python
from functools import wraps
from fastapi import HTTPException, Header

def require_auth(func):
    """Decorator to require authentication."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # In real app, validate JWT token
        # For demo, check for API key header

        # Get self (route instance) to access headers
        # This is simplified - real implementation would use FastAPI dependencies

        return func(*args, **kwargs)

    return wrapper

# Better approach with FastAPI dependencies
from fastapi import Depends, HTTPException, status

async def verify_api_key(api_key: str = Header(..., alias="X-API-Key")):
    """Verify API key."""
    valid_keys = {
        "demo-key-123": "user_1",
        "test-key-456": "user_2"
    }

    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    return valid_keys[api_key]

# Usage in routes
class ApiRoutes(RouteBase):

    async def get_protected(
        self,
        user_id: str = Depends(verify_api_key)
    ):
        """Protected endpoint (requires API key)."""
        return {
            "message": "Authenticated",
            "user": user_id,
            "data": "sensitive information"
        }
```

### Test Authentication

**Without API key:**
```bash
curl http://localhost:7376/api/protected
```

**Response:** (401 Unauthorized)
```json
{
  "detail": "Missing API key"
}
```

**With valid API key:**
```bash
curl http://localhost:7376/api/protected \
  -H "X-API-Key: demo-key-123"
```

**Response:** (200 OK)
```json
{
  "message": "Authenticated",
  "user": "user_1",
  "data": "sensitive information"
}
```

---

## Step 6: Combining Multiple Decorators

You can stack multiple decorators:

```python
class ApiRoutes(RouteBase):

    @rate_limit("10/minute")
    @cache(duration=60)
    @log_execution
    def get(self):
        """
        This endpoint has:
        - Rate limiting (10/minute)
        - Caching (60 seconds)
        - Logging
        """
        return {"message": "Protected and optimized"}

    # Order matters! Decorators are applied bottom to top:
    # 1. log_execution (innermost - runs first)
    # 2. cache
    # 3. rate_limit (outermost - runs last)
```

### Understanding Decorator Order

```python
@decorator_a
@decorator_b
def my_function():
    pass

# Equivalent to:
my_function = decorator_a(decorator_b(my_function))

# Execution order (when function is called):
# 1. decorator_a's wrapper runs first
# 2. then decorator_b's wrapper
# 3. finally, my_function runs
```

**Practical example:**
```python
@rate_limit("10/minute")      # Runs first (check limit)
@cache(duration=60)           # Runs second (check cache)
@log_execution                # Runs last (log the call)
def get_expensive_data(self):
    # Actual function
    pass

# When called:
# 1. Check rate limit
# 2. Check cache (if hit, return without logging execution)
# 3. Log execution
# 4. Run function
```

---

## Step 7: Custom Decorator with Parameters

Create flexible decorators with parameters:

```python
from functools import wraps

def validate_content_type(content_type):
    """Decorator to validate request content type."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # In real app, check request headers
            # This is simplified

            print(f"Validating content-type: {content_type}")
            return func(*args, **kwargs)

        return wrapper
    return decorator

# Usage
class ApiRoutes(RouteBase):

    @validate_content_type("application/json")
    def post_json(self):
        return {"accepted": "json"}

    @validate_content_type("multipart/form-data")
    def post_form(self):
        return {"accepted": "form"}
```

---

## Step 8: Async Decorators

Support async functions:

```python
from functools import wraps
import asyncio

def async_timer(func):
    """Decorator to time async functions."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()

        try:
            result = await func(*args, **kwargs)

            elapsed = time.time() - start
            print(f"{func.__name__} took {elapsed:.3f}s")

            return result

        except Exception as e:
            elapsed = time.time() - start
            print(f"{func.__name__} failed after {elapsed:.3f}s")
            raise

    return wrapper

# Usage
class ApiRoutes(RouteBase):

    @async_timer
    @cache(duration=60)
    async def get_async(self):
        """Async endpoint with timing and caching."""
        await asyncio.sleep(1)  # Simulate async operation
        return {"message": "Async operation complete"}
```

---

## Common Decorator Patterns

### Pattern 1: Retry Logic

```python
def retry(max_attempts=3, delay=1):
    """Decorator to retry failed operations."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    print(f"Attempt {attempt + 1} failed, retrying...")
                    time.sleep(delay)
        return wrapper
    return decorator

@retry(max_attempts=3, delay=2)
def get_external_api(self):
    """Retry if external API fails."""
    return requests.get("https://external-api.com").json()
```

### Pattern 2: Measure Performance

```python
def measure_performance(func):
    """Measure and log performance metrics."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()

        metrics = {
            "function": func.__name__,
            "duration_ms": round((end - start) * 1000, 2),
            "timestamp": datetime.now().isoformat()
        }

        # In real app, send to monitoring service
        print(f"PERFORMANCE: {metrics}")

        return result

    return wrapper
```

### Pattern 3: Data Validation

```python
def validate_schema(schema):
    """Validate data against schema before processing."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Validate input
            # In real app, use JSON schema validation
            print(f"Validating against schema: {schema}")
            return func(*args, **kwargs)
        return wrapper
    return decorator

@validate_schema({"type": "object", "properties": {"name": {"type": "string"}}})
def post_user(self, user: dict = Body(...)):
    return {"created": True, "user": user}
```

---

## Performance Tips

### 1. Cache Expensive Operations

```python
# Good - cached
@cache(duration=300)
async def get_expensive_report(self):
    # Complex computation
    return generate_report()

# Bad - recomputed every time
async def get_expensive_report(self):
    return generate_report()
```

### 2. Rate Limit Public APIs

```python
# Protect your resources
@rate_limit("10/minute")
def post_contact(self):
    """Prevent spam on contact form."""
    send_email(...)
    return {"sent": True}
```

### 3. Use Async Decorators for Async Functions

```python
# Good - async-aware
@async_timer
async def get_data(self):
    await database_query()
    return data

# Works but not ideal - sync decorator on async function
@timer
async def get_data(self):
    await database_query()
    return data
```

---

## Troubleshooting

### Problem 1: Decorator Not Applied

**Symptom:** Decorator doesn't seem to work

**Cause:** Forgot `@` symbol or parentheses

**Solution:**
```python
# Wrong
cache(duration=60)
def get(self):
    pass

# Correct
@cache(duration=60)
def get(self):
    pass
```

### Problem 2: Cache Not Working

**Symptom:** Function executes every time

**Cause:** Cache key collision or duration too short

**Solution:**
```python
# Use custom key prefix
@cache(duration=300, key_prefix="user:{user_id}")
def get_user(self, user_id: int):
    pass

# Increase duration
@cache(duration=3600)  # 1 hour
def get_static_data(self):
    pass
```

### Problem 3: Rate Limit Too Strict

**Symptom:** Legitimate users blocked

**Cause:** Limit too low for use case

**Solution:**
```python
# Adjust limits based on usage
@rate_limit("100/minute")  # Was 10/minute
def get_api(self):
    pass

# Or use different limits for different users
@rate_limit("1000/hour", key_func=lambda r: get_user_tier(r))
def get_api(self):
    pass
```

---

## Best Practices

### 1. Use Descriptive Decorator Names

```python
# Good - clear intent
@require_auth
@cache_response(duration=60)
@log_request

# Avoid - vague names
@protect
@store
@record
```

### 2. Keep Decorators Simple

```python
# Good - single responsibility
@cache(duration=60)
@rate_limit("10/minute")

# Avoid - complex multi-purpose decorator
@optimize_and_protect_and_log
```

### 3. Document Decorator Behavior

```python
@rate_limit("10/minute")
# Rate limit: 10 requests per minute per IP
# Returns 429 if exceeded
def post(self):
    """Create resource."""
    pass
```

### 4. Handle Errors Gracefully

```python
def robust_timer(func):
    """Decorator that logs errors instead of crashing."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            # Re-raise or return error response
            raise
    return wrapper
```

---

## Summary

In this tutorial, you learned:

✅ **Decorator Basics**: What decorators are and how they work
✅ **Caching**: `@cache` decorator for performance optimization
✅ **Rate Limiting**: `@rate_limit` decorator for API protection
✅ **Custom Decorators**: Creating your own decorators
✅ **Authentication**: Protecting routes with auth decorators
✅ **Logging**: Tracking function execution
✅ **Combining Decorators**: Stacking multiple decorators
✅ **Async Support**: Decorators for async functions
✅ **Common Patterns**: Retry, validation, performance monitoring

**Key takeaways:**
- Decorators add cross-cutting concerns without cluttering business logic
- Built-in decorators (@cache, @rate_limit) solve common problems
- Custom decorators let you add reusable functionality
- Stack decorators carefully - order matters
- Use decorators for logging, auth, validation, caching, rate limiting

---

## Next Steps

**Continue learning:**
- [Error Handling](error-handling.md) - Advanced error management
- [Security Guide](../../guides/security.md) - Production security practices
- [Caching Examples](../../examples/caching.md) - Advanced caching strategies

**Practice ideas:**
- Create a decorator to compress JSON responses
- Build a decorator to track API usage metrics
- Implement a decorator for request/response transformation

---

**Ready to handle errors like a pro?** Continue to [Error Handling](error-handling.md)!
