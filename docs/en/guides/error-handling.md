# Error Handling

Learn how to properly handle errors in your REROUTE applications for robust, production-ready APIs.

---

## Overview

REROUTE provides multiple ways to handle errors:

1. **`on_error()` hook** - Class-level error handling
2. **Framework-native exceptions** - FastAPI/Flask exception handling
3. **Try-catch blocks** - Standard Python error handling
4. **Global error handlers** - Application-wide error handling

---

## Using the on_error Hook

The `on_error()` hook is called automatically when any exception occurs in your route handlers.

### Basic Usage

```python
from reroute import RouteBase

class UserRoutes(RouteBase):
    """User routes with custom error handling."""

    def on_error(self, error: Exception) -> dict:
        """
        Handle all errors for this route class.

        Args:
            error: The exception that occurred

        Returns:
            dict: Error response (will be converted to JSON)
        """
        # Log the error
        print(f"Error in UserRoutes: {type(error).__name__}: {error}")

        # Return user-friendly error response
        return {
            "error": "An error occurred",
            "message": str(error),
            "type": type(error).__name__
        }

    def get(self, user_id: int):
        # This will trigger on_error if user not found
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        return user
```

### Returning Custom Status Codes

```python
def on_error(self, error: Exception) -> tuple[dict, int]:
    """Return custom status codes based on error type."""

    if isinstance(error, ValueError):
        return {"error": "Invalid input", "details": str(error)}, 400

    elif isinstance(error, KeyError):
        return {"error": "Resource not found", "details": str(error)}, 404

    elif isinstance(error, PermissionError):
        return {"error": "Forbidden", "details": str(error)}, 403

    else:
        # Internal server error for unknown exceptions
        return {"error": "Internal server error"}, 500
```

---

## Framework-Native Exception Handling

### FastAPI HTTPException

```python
from fastapi import HTTPException
from reroute import RouteBase

class ProductRoutes(RouteBase):
    """Product routes using FastAPI exceptions."""

    def get(self, product_id: int):
        product = self.find_product(product_id)

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {product_id} not found"
            )

        if not self.user_has_access(product):
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to view this product"
            )

        return product

    def post(self, product_data: dict):
        if not self.validate_product_data(product_data):
            raise HTTPException(
                status_code=400,
                detail="Invalid product data",
                headers={"X-Error-Code": "INVALID_DATA"}
            )

        return self.create_product(product_data)
```

### Flask abort()

```python
from flask import abort
from reroute import RouteBase

class OrderRoutes(RouteBase):
    """Order routes using Flask abort."""

    def get(self, order_id: int):
        order = self.find_order(order_id)

        if not order:
            abort(404, description=f"Order {order_id} not found")

        if not self.user_owns_order(order):
            abort(403, description="Access denied")

        return order
```

---

## Try-Catch Blocks

### Handling Specific Exceptions

```python
from reroute import RouteBase
import requests

class ExternalAPIRoutes(RouteBase):
    """Routes that call external APIs."""

    def get(self):
        try:
            # Call external API
            response = requests.get(
                "https://api.example.com/data",
                timeout=5
            )
            response.raise_for_status()
            return response.json()

        except requests.Timeout:
            return {"error": "External API timeout"}, 504

        except requests.HTTPError as e:
            return {
                "error": "External API error",
                "status_code": e.response.status_code
            }, 502

        except requests.RequestException as e:
            return {"error": "Failed to connect to external API"}, 503
```

### Database Error Handling

```python
from reroute import RouteBase
from sqlalchemy.exc import IntegrityError, OperationalError

class DatabaseRoutes(RouteBase):
    """Routes with database operations."""

    def post(self, user_data: dict):
        try:
            user = User(**user_data)
            db.session.add(user)
            db.session.commit()
            return {"id": user.id, "created": True}

        except IntegrityError as e:
            db.session.rollback()
            return {
                "error": "Duplicate entry",
                "message": "User with this email already exists"
            }, 409

        except OperationalError as e:
            db.session.rollback()
            return {
                "error": "Database error",
                "message": "Could not connect to database"
            }, 503

        except Exception as e:
            db.session.rollback()
            return {"error": "Failed to create user"}, 500
```

---

## Global Error Handlers

### FastAPI Global Exception Handler

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from reroute.adapters import FastAPIAdapter

app = FastAPI()

# Global exception handler
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid value", "detail": str(exc)}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the error
    print(f"Unhandled exception: {type(exc).__name__}: {exc}")

    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

# Register REROUTE routes
adapter = FastAPIAdapter(fastapi_app=app, app_dir="./app")
adapter.register_routes()
```

### Flask Global Error Handler

```python
from flask import Flask, jsonify
from reroute.adapters import FlaskAdapter

app = Flask(__name__)

# Global error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found", "message": str(error)}), 404

@app.errorhandler(500)
def internal_error(error):
    # Log the error
    print(f"Internal error: {error}")
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(Exception)
def handle_exception(error):
    # Log all unhandled exceptions
    print(f"Unhandled exception: {type(error).__name__}: {error}")

    return jsonify({
        "error": "An error occurred",
        "type": type(error).__name__
    }), 500

# Register REROUTE routes
adapter = FlaskAdapter(flask_app=app, app_dir="./app")
adapter.register_routes()
```

---

## Validation Errors

### Pydantic Validation

```python
from reroute import RouteBase
from reroute.params import Body
from pydantic import BaseModel, Field, ValidationError

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    age: int = Field(..., ge=0, le=150)

class UserRoutes(RouteBase):
    """User routes with Pydantic validation."""

    def post(self, user: UserCreate = Body()):
        """
        Pydantic automatically validates the request body.
        Returns 422 Unprocessable Entity if validation fails.
        """
        # If we reach here, validation passed
        return self.create_user(user.model_dump())

    def on_error(self, error: Exception):
        """Handle validation errors."""
        if isinstance(error, ValidationError):
            return {
                "error": "Validation failed",
                "details": error.errors()
            }, 422

        return {"error": "Internal server error"}, 500
```

---

## Best Practices

### 1. **Don't Expose Internal Details**

❌ **Bad**:
```python
def on_error(self, error: Exception):
    return {"error": str(error), "traceback": traceback.format_exc()}, 500
```

✅ **Good**:
```python
def on_error(self, error: Exception):
    # Log full error internally
    logger.error(f"Error: {error}", exc_info=True)

    # Return safe error to user
    return {"error": "An error occurred"}, 500
```

### 2. **Use Specific Error Messages**

❌ **Bad**:
```python
raise ValueError("Error")
```

✅ **Good**:
```python
raise ValueError(f"Invalid user ID: {user_id}. Must be a positive integer.")
```

### 3. **Log All Errors**

```python
import logging

logger = logging.getLogger(__name__)

class MyRoutes(RouteBase):
    def on_error(self, error: Exception):
        # Log with context
        logger.error(
            f"Error in {self.__class__.__name__}: {error}",
            exc_info=True,
            extra={"route_class": self.__class__.__name__}
        )

        return {"error": "An error occurred"}, 500
```

### 4. **Use Appropriate HTTP Status Codes**

- **400 Bad Request** - Client sent invalid data
- **401 Unauthorized** - Not authenticated
- **403 Forbidden** - Authenticated but not authorized
- **404 Not Found** - Resource doesn't exist
- **409 Conflict** - Resource conflict (e.g., duplicate entry)
- **422 Unprocessable Entity** - Validation failed
- **500 Internal Server Error** - Unexpected server error
- **502 Bad Gateway** - External service error
- **503 Service Unavailable** - Service temporarily down
- **504 Gateway Timeout** - External service timeout

### 5. **Graceful Degradation**

```python
class DataRoutes(RouteBase):
    def get(self):
        try:
            # Try primary data source
            data = self.fetch_from_primary_db()
        except Exception as e:
            logger.warning(f"Primary DB failed: {e}")

            try:
                # Fall back to cache
                data = self.fetch_from_cache()
            except Exception:
                # Last resort - return empty result
                data = []

        return {"data": data}
```

---

## Error Response Format

### Standard Format

Use a consistent error response format across your API:

```python
{
    "error": "Brief error description",
    "message": "Detailed error message",
    "code": "ERROR_CODE",
    "details": {},  // Optional additional context
    "timestamp": "2025-11-23T10:30:00Z"
}
```

### Implementation

```python
from datetime import datetime

class BaseRoute(RouteBase):
    """Base class with standardized error handling."""

    def on_error(self, error: Exception):
        error_response = {
            "error": self._get_error_title(error),
            "message": str(error),
            "code": self._get_error_code(error),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        status_code = self._get_status_code(error)
        return error_response, status_code

    def _get_error_title(self, error: Exception) -> str:
        mapping = {
            ValueError: "Invalid Input",
            KeyError: "Resource Not Found",
            PermissionError: "Access Denied",
        }
        return mapping.get(type(error), "Internal Error")

    def _get_error_code(self, error: Exception) -> str:
        return type(error).__name__.upper()

    def _get_status_code(self, error: Exception) -> int:
        mapping = {
            ValueError: 400,
            KeyError: 404,
            PermissionError: 403,
        }
        return mapping.get(type(error), 500)
```

---

## Testing Error Handling

```python
import pytest
from fastapi.testclient import TestClient

def test_error_handling():
    # Test 404 error
    response = client.get("/users/99999")
    assert response.status_code == 404
    assert "error" in response.json()

    # Test validation error
    response = client.post("/users", json={"age": -5})
    assert response.status_code == 422

    # Test server error handling
    with pytest.raises(Exception):
        response = client.get("/broken-endpoint")
```

---

## Next Steps

- [Security Best Practices](security.md) - Secure your error handling
- [Testing](testing.md) - Test your error handlers
