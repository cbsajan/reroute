---
difficulty: medium
time: 25 minutes
prerequisites:
  - link: ../../start-here.md
  - link: ../easy/http-methods.md
  - link: crud-app.md
next: ../hard/authentication.md
---

# Error Handling

Master error handling in REROUTE to build robust APIs with clear error messages, proper status codes, and great developer experience.

## What You'll Learn

- HTTPException for common errors
- Custom exception classes
- Global error handlers
- Validation error handling
- Proper HTTP status codes
- Error response formatting
- Logging and monitoring

## Prerequisites

- Completed [HTTP Methods](../easy/http-methods.md) tutorial
- Completed [CRUD Application](crud-app.md) tutorial
- Understanding of HTTP status codes
- Working REROUTE project

---

## Why Good Error Handling Matters

**Bad error handling:**
```json
{
  "error": "Something went wrong"  # Useless!
}
```

**Good error handling:**
```json
{
  "detail": "User not found",
  "error_code": "USER_NOT_FOUND",
  "status": 404,
  "path": "/users/999",
  "timestamp": "2025-03-03T10:15:30Z",
  "suggestion": "Valid user IDs: 1, 2, 3"
}
```

Great error handling helps developers:
- Understand what went wrong
- Fix the issue quickly
- Build reliable integrations
- Provide better UX to end users

---

## Step 1: Create Demo Project

```bash
reroute init error-handling-demo --framework fastapi
cd error-handling-demo
```

Create routes:

```bash
reroute create route --path /users --name UserRoutes --methods GET,POST,PUT,DELETE
reroute create route --path /posts --name PostRoutes --methods GET,POST
```

---

## Step 2: Basic HTTPException

FastAPI's `HTTPException` is the primary way to return errors.

Edit `app/routes/users/page.py`:

```python
from typing import List, Dict, Optional
from reroute import RouteBase
from reroute.params import Query, Body
from fastapi import HTTPException, status
from pydantic import BaseModel, Field, EmailStr

# In-memory database
users_db = [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"},
]
next_id = 3

class UserCreate(BaseModel):
    """Schema for creating users."""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    age: Optional[int] = Field(None, ge=0, le=150)

class UserRoutes(RouteBase):
    """User management with error handling."""
    tag = "Users"

    def get(self, user_id: Optional[int] = Query(None, gt=0)):
        """
        Get user by ID with error handling.

        - **user_id**: User ID (optional)
        """
        # Get specific user
        if user_id is not None:
            user = next((u for u in users_db if u["id"] == user_id), None)

            if not user:
                # Raise 404 if user not found
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found",
                    headers={"X-Error-Code": "USER_NOT_FOUND"}
                )

            return user

        # List all users
        return {"users": users_db}

    def post(self, user: UserCreate = Body(...)):
        """
        Create new user with validation and error handling.
        """
        # Check for duplicate email
        if any(u["email"] == user.email for u in users_db):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{user.email}' already exists",
                headers={"X-Error-Code": "EMAIL_EXISTS"}
            )

        # Create user
        new_user = {
            "id": next_id,
            "name": user.name,
            "email": user.email,
            "age": user.age
        }
        users_db.append(new_user)

        return new_user, status.HTTP_201_CREATED

    def put(
        self,
        user_id: int = Query(..., gt=0),
        user: UserCreate = Body(...)
    ):
        """Update user with error handling."""
        # Find user
        user_idx = next(
            (i for i, u in enumerate(users_db) if u["id"] == user_id),
            None
        )

        if user_idx is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found. Cannot update.",
                headers={"X-Error-Code": "USER_NOT_FOUND"}
            )

        # Update user
        users_db[user_idx].update({
            "name": user.name,
            "email": user.email,
            "age": user.age
        })

        return users_db[user_idx]

    def delete(self, user_id: int = Query(..., gt=0)):
        """Delete user with error handling."""
        user_idx = next(
            (i for i, u in enumerate(users_db) if u["id"] == user_id),
            None
        )

        if user_idx is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found. Cannot delete.",
                headers={"X-Error-Code": "USER_NOT_FOUND"}
            )

        deleted = users_db.pop(user_idx)
        return {
            "message": "User deleted",
            "deleted": deleted
        }
```

`★ Insight ─────────────────────────────────────`
**HTTPException Best Practices**:
- Always use `status.HTTP_*` constants instead of raw numbers
- Include specific error details in the `detail` field
- Add custom headers for error codes (helps with client-side handling)
- Use clear, actionable error messages

This makes your API self-documenting and easier to integrate with.
`─────────────────────────────────────────────────`

---

## Step 3: Custom Exception Classes

Create reusable exceptions for common errors.

Create `app/exceptions.py`:

```python
from fastapi import HTTPException, status

class ResourceNotFoundException(HTTPException):
    """Raised when a resource is not found."""

    def __init__(self, resource_type: str, resource_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_type} with ID {resource_id} not found",
            headers={"X-Error-Code": "RESOURCE_NOT_FOUND", "X-Resource-Type": resource_type}
        )

class DuplicateResourceException(HTTPException):
    """Raised when trying to create a duplicate resource."""

    def __init__(self, resource_type: str, field: str, value: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{resource_type} with {field} '{value}' already exists",
            headers={"X-Error-Code": "DUPLICATE_RESOURCE", "X-Field": field}
        )

class ValidationException(HTTPException):
    """Raised when business validation fails."""

    def __init__(self, message: str, field: str = None):
        headers = {"X-Error-Code": "VALIDATION_ERROR"}
        if field:
            headers["X-Field"] = field

        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=message,
            headers=headers
        )

class PermissionDeniedException(HTTPException):
    """Raised when user lacks permission."""

    def __init__(self, action: str, resource: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: Cannot {action} {resource}",
            headers={"X-Error-Code": "PERMISSION_DENIED"}
        )

class RateLimitExceededException(HTTPException):
    """Raised when rate limit is exceeded."""

    def __init__(self, limit: str, retry_after: int = None):
        headers = {"X-Error-Code": "RATE_LIMIT_EXCEEDED"}
        if retry_after:
            headers["Retry-After"] = str(retry_after)

        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {limit}",
            headers=headers
        )
```

### Use Custom Exceptions

Edit `app/routes/posts/page.py`:

```python
from reroute import RouteBase
from reroute.params import Body
from app.exceptions import (
    ResourceNotFoundException,
    DuplicateResourceException,
    ValidationException
)
from pydantic import BaseModel

posts_db = [
    {"id": 1, "title": "First Post", "content": "..."},
    {"id": 2, "title": "Second Post", "content": "..."}
]
next_id = 3

class PostCreate(BaseModel):
    title: str
    content: str

class PostRoutes(RouteBase):
    """Post management with custom exceptions."""
    tag = "Posts"

    def get(self, post_id: int = Query(..., gt=0)):
        """Get post - uses custom exception."""
        post = next((p for p in posts_db if p["id"] == post_id), None)

        if not post:
            # Clean and reusable!
            raise ResourceNotFoundException("Post", post_id)

        return post

    def post(self, post: PostCreate = Body(...)):
        """Create post with duplicate check."""
        # Check for duplicate title
        if any(p["title"] == post.title for p in posts_db):
            raise DuplicateResourceException("Post", "title", post.title)

        # Business validation
        if len(post.content) < 10:
            raise ValidationException(
                "Content must be at least 10 characters long",
                field="content"
            )

        new_post = {
            "id": next_id,
            "title": post.title,
            "content": post.content
        }
        posts_db.append(new_post)

        return new_post, status.HTTP_201_CREATED
```

### Test Custom Exceptions

**Resource not found:**
```bash
curl http://localhost:7376/posts?post_id=999
```

**Response:** (404 Not Found)
```json
{
  "detail": "Post with ID 999 not found"
}
```

**Headers:**
```
X-Error-Code: RESOURCE_NOT_FOUND
X-Resource-Type: Post
```

**Duplicate resource:**
```bash
curl -X POST http://localhost:7376/posts \
  -H "Content-Type: application/json" \
  -d '{"title": "First Post", "content": "Some content"}'
```

**Response:** (409 Conflict)
```json
{
  "detail": "Post with title 'First Post' already exists"
}
```

---

## Step 4: Global Error Handlers

Catch all exceptions and return consistent error responses.

Edit `main.py`:

```python
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create app
app = FastAPI(title="Error Handling Demo")

# ... your existing adapter setup ...

# Global exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    logger.warning(f"Validation error: {errors}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation failed",
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }
    )

# Global exception handler for HTTP exceptions
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle all HTTP exceptions."""
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path),
            "method": request.method,
            "timestamp": datetime.now().isoformat()
        },
        headers=getattr(exc, "headers", None)
    )

# Catch-all exception handler
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc) if app.debug else "An error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )
```

### Test Global Handlers

**Validation error:**
```bash
curl -X POST http://localhost:7376/users \
  -H "Content-Type: application/json" \
  -d '{"name": "A", "email": "invalid-email"}'
```

**Response:** (422 Unprocessable Entity)
```json
{
  "detail": "Validation failed",
  "errors": [
    {
      "field": "name",
      "message": "ensure this value has at least 2 characters",
      "type": "string_too_short"
    },
    {
      "field": "email",
      "message": "value is not a valid email address",
      "type": "value_error.email"
    }
  ],
  "timestamp": "2025-03-03T10:15:30Z"
}
```

---

## Step 5: Standardized Error Response Format

Create a consistent error response structure.

Create `app/responses.py`:

```python
from fastapi import status
from typing import Optional, Dict, Any
from datetime import datetime

class ErrorResponse:
    """Standardized error response format."""

    @staticmethod
    def create(
        detail: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = None,
        field: str = None,
        suggestion: str = None,
        **extra
    ) -> Dict[str, Any]:
        """
        Create standardized error response.

        Args:
            detail: Human-readable error message
            status_code: HTTP status code
            error_code: Machine-readable error code
            field: Field that caused the error (if applicable)
            suggestion: Helpful suggestion for fixing the error
            **extra: Additional metadata
        """
        response = {
            "detail": detail,
            "status_code": status_code,
            "timestamp": datetime.now().isoformat()
        }

        if error_code:
            response["error_code"] = error_code
        if field:
            response["field"] = field
        if suggestion:
            response["suggestion"] = suggestion

        response.update(extra)
        return response

    @staticmethod
    def not_found(resource_type: str, resource_id: Any) -> Dict[str, Any]:
        """404 Not Found error."""
        return ErrorResponse.create(
            detail=f"{resource_type} with ID '{resource_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            resource_type=resource_type,
            resource_id=str(resource_id)
        )

    @staticmethod
    def validation_error(field: str, message: str) -> Dict[str, Any]:
        """422 Validation error."""
        return ErrorResponse.create(
            detail=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            field=field
        )

    @staticmethod
    def conflict(resource_type: str, field: str, value: str) -> Dict[str, Any]:
        """409 Conflict error."""
        return ErrorResponse.create(
            detail=f"{resource_type} with {field} '{value}' already exists",
            status_code=status.HTTP_409_CONFLICT,
            error_code="DUPLICATE_RESOURCE",
            field=field,
            value=value
        )

    @staticmethod
    def unauthorized(detail: str = "Authentication required") -> Dict[str, Any]:
        """401 Unauthorized error."""
        return ErrorResponse.create(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED",
            suggestion="Provide valid authentication credentials"
        )

    @staticmethod
    def forbidden(action: str, resource: str) -> Dict[str, Any]:
        """403 Forbidden error."""
        return ErrorResponse.create(
            detail=f"Permission denied: Cannot {action} {resource}",
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN",
            suggestion="Contact administrator for access"
        )
```

### Use Standardized Responses

Edit `app/routes/users/page.py`:

```python
from fastapi import HTTPException, status
from app.responses import ErrorResponse

class UserRoutes(RouteBase):

    def get(self, user_id: int = Query(..., gt=0)):
        user = next((u for u in users_db if u["id"] == user_id), None)

        if not user:
            # Use standardized error
            error = ErrorResponse.not_found("User", user_id)
            raise HTTPException(
                status_code=error["status_code"],
                detail=error["detail"],
                headers={"X-Error-Code": error["error_code"]}
            )

        return user

    def post(self, user: UserCreate = Body(...)):
        if any(u["email"] == user.email for u in users_db):
            # Use standardized error
            error = ErrorResponse.conflict("User", "email", user.email)
            raise HTTPException(
                status_code=error["status_code"],
                detail=error["detail"]
            )

        # Create user...
```

---

## Step 6: HTTP Status Code Best Practices

Use appropriate status codes for different scenarios:

```python
from fastapi import status

# 2xx Success
status.HTTP_200_OK              # Success
status.HTTP_201_CREATED         # Resource created
status.HTTP_204_NO_CONTENT      # Success with no response body

# 3xx Redirection
status.HTTP_301_MOVED_PERMANENTLY  # Permanent redirect
status.HTTP_302_FOUND                 # Temporary redirect
status.HTTP_304_NOT_MODIFIED         # Resource not modified (caching)

# 4xx Client Errors
status.HTTP_400_BAD_REQUEST               # Invalid request
status.HTTP_401_UNAUTHORIZED              # Authentication required
status.HTTP_403_FORBIDDEN                 # Authenticated but not authorized
status.HTTP_404_NOT_FOUND                 # Resource not found
status.HTTP_405_METHOD_NOT_ALLOWED        # HTTP method not supported
status.HTTP_409_CONFLICT                  # Conflicts with current state
status.HTTP_422_UNPROCESSABLE_ENTITY      # Semantic errors
status.HTTP_429_TOO_MANY_REQUESTS         # Rate limit exceeded
status.HTTP_413_REQUEST_ENTITY_TOO_LARGE  # Request too large

# 5xx Server Errors
status.HTTP_500_INTERNAL_SERVER_ERROR     # Unexpected error
status.HTTP_501_NOT_IMPLEMENTED           # Feature not implemented
status.HTTP_503_SERVICE_UNAVAILABLE       # Service temporarily unavailable
```

### Decision Tree for Status Codes

```
Request received
    │
    ├─ Authenticated?
    │   ├─ No → 401 Unauthorized
    │   └─ Yes → Has permission?
    │       ├─ No → 403 Forbidden
    │       └─ Yes → Resource exists?
    │           ├─ No → 404 Not Found
    │           └─ Yes → Valid data?
    │               ├─ No → 400 Bad Request
    │               ├─ Business rule violation → 422 Unprocessable Entity
    │               └─ Yes → Success
    │                   ├─ Created → 201 Created
    │                   ├─ Updated → 200 OK
    │                   └─ Deleted → 204 No Content
```

---

## Step 7: Logging Errors

Implement comprehensive error logging.

Edit `main.py`:

```python
import logging
from datetime import datetime
from fastapi import Request

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing."""
    start_time = time.time()

    # Log request
    logger.info(f"→ {request.method} {request.url.path}")

    try:
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.info(
            f"← {request.method} {request.url.path} "
            f"- {response.status_code} - {duration:.3f}s"
        )

        # Add timing header
        response.headers["X-Process-Time"] = str(duration)

        return response

    except Exception as e:
        duration = time.time() - start_time

        # Log error
        logger.error(
            f"✗ {request.method} {request.url.path} "
            f"- Failed after {duration:.3f}s - {str(e)}"
        )
        raise

# Exception handler with logging
@app.exception_handler(Exception)
async def log_exception_handler(request: Request, exc: Exception):
    """Log exceptions before returning error."""
    logger.error(
        f"Exception: {exc.__class__.__name__} - {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.now().isoformat()
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )
```

---

## Common Error Scenarios

### Scenario 1: Invalid JSON

```python
# Pydantic handles this automatically
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2)

# If client sends invalid JSON, FastAPI returns 422:
{
  "detail": "Validation failed",
  "errors": [...]
}
```

### Scenario 2: Missing Required Field

```python
# Client: POST /users with body {}
# Response (422):
{
  "detail": "Validation failed",
  "errors": [
    {
      "field": "name",
      "message": "Field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Scenario 3: Invalid Data Type

```python
# Client: POST /users with body {"name": 123}
# Response (422):
{
  "detail": "Validation failed",
  "errors": [
    {
      "field": "name",
      "message": "Input should be a valid string",
      "type": "string_type"
    }
  ]
}
```

### Scenario 4: Business Rule Violation

```python
def post(self, user: UserCreate):
    if user.age < 18:
        raise ValidationException(
            "User must be 18 or older",
            field="age"
        )
```

---

## Troubleshooting

### Problem 1: Generic Error Messages

**Symptom:** All errors return "Internal server error"

**Cause:** Not catching specific exceptions

**Solution:**
```python
# Bad
try:
    result = some_operation()
except:
    raise HTTPException(500, "Error")

# Good
try:
    result = some_operation()
except ValueError as e:
    raise HTTPException(400, f"Invalid value: {e}")
except PermissionError:
    raise HTTPException(403, "Permission denied")
```

### Problem 2: Stack Traces Leaking

**Symptom:** Sensitive info in error responses

**Cause:** Returning exception details directly

**Solution:**
```python
# Bad
return {"error": str(exc)}

# Good - sanitize errors
if app.debug:
    return {"error": str(exc)}
else:
    return {"error": "Internal server error"}
```

### Problem 3: No Error Logging

**Symptom:** Don't know what errors are happening

**Cause:** Not logging exceptions

**Solution:**
```python
@app.exception_handler(Exception)
async def global_handler(request, exc):
    # Always log
    logger.error(f"Error: {exc}", exc_info=True)
    return {"detail": "Error occurred"}
```

---

## Best Practices

### 1. Use Specific Status Codes

```python
# Good - specific codes
raise HTTPException(404, "User not found")
raise HTTPException(409, "Email already exists")
raise HTTPException(422, "Validation failed")

# Bad - generic code
raise HTTPException(400, "Error")  # Too vague
```

### 2. Include Actionable Information

```python
# Good
raise HTTPException(
    404,
    f"User {user_id} not found. Valid IDs: {[u['id'] for u in users_db]}"
)

# Bad
raise HTTPException(404, "Not found")
```

### 3. Consistent Error Format

```python
# Good - consistent structure
{
  "detail": "Error message",
  "error_code": "USER_NOT_FOUND",
  "timestamp": "2025-03-03T10:15:30Z"
}

# Bad - inconsistent
{"error": "Not found"}
{"message": "User doesn't exist"}
{"detail": "Error 404"}
```

### 4. Log Every Error

```python
# Always log before raising
logger.error(f"User {user_id} not found")
raise HTTPException(404, "User not found")
```

### 5. Use Custom Exceptions

```python
# Good - reusable
raise ResourceNotFoundException("User", user_id)

# Bad - repeated
raise HTTPException(404, f"User {user_id} not found")
raise HTTPException(404, f"Post {post_id} not found")
raise HTTPException(404, f"Comment {comment_id} not found")
```

---

## Summary

In this tutorial, you learned:

✅ **HTTPException**: Basic error handling
✅ **Custom Exceptions**: Reusable exception classes
✅ **Global Handlers**: Catch-all error handling
✅ **Validation Errors**: Pydantic validation responses
✅ **Status Codes**: Using appropriate HTTP codes
✅ **Error Formatting**: Consistent error responses
✅ **Logging**: Comprehensive error logging
✅ **Best Practices**: Production-ready patterns

**Key takeaways:**
- Use specific status codes (404, 409, 422, not just 400)
- Create custom exceptions for reusable error patterns
- Implement global handlers for consistent responses
- Log all errors with context
- Return actionable error messages
- Never expose sensitive data in errors

---

## Next Steps

**Continue learning:**
- [Authentication](../hard/authentication.md) - JWT authentication *(Coming Soon)*
- [Database Integration](../hard/database-integration.md) - Error handling with databases *(Coming Soon)*
- [Production Deployment](../../deployment/production.md) - Production error monitoring

**Practice ideas:**
- Implement error tracking (Sentry, Rollbar)
- Create error documentation for API consumers
- Build error dashboard for monitoring
- Add rate limiting with helpful error messages

---

**Ready to secure your API?** Continue to [Authentication](../hard/authentication.md)!
