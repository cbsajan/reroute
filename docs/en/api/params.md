# Parameter Injection API

FastAPI-style parameter injection for automatic request data extraction and validation.

## Overview

REROUTE provides automatic parameter injection similar to FastAPI, allowing you to declare parameters in your route methods and have them automatically extracted, validated, and type-converted from HTTP requests.

## Available Parameters

| Parameter | Source | Example |
|-----------|--------|---------|
| `Query` | URL query string | `?limit=10&offset=0` |
| `Path` | URL path segments | `/users/{id}` |
| `Header` | HTTP headers | `Authorization: Bearer token` |
| `Body` | JSON request body | Pydantic models |
| `Cookie` | HTTP cookies | Session cookies |
| `Form` | Form data | HTML forms |
| `File` | File uploads | Multipart form data |

## Import

```python
from reroute.params import Query, Path, Header, Body, Cookie, Form, File
```

## Query Parameters

Extract data from URL query strings with automatic validation.

### Basic Usage

```python
from reroute import RouteBase
from reroute.params import Query

class UsersRoutes(RouteBase):
    def get(self,
            limit: int = Query(10, description="Maximum results"),
            offset: int = Query(0, description="Skip results"),
            search: str = Query(None, description="Search term")):
        return {
            "limit": limit,
            "offset": offset,
            "search": search
        }
```

**Request:** `GET /users?limit=20&offset=5&search=john`

**Result:** `{"limit": 20, "offset": 5, "search": "john"}`

### Validation

```python
def get(self,
        limit: int = Query(10, ge=1, le=100),  # Between 1 and 100
        age: int = Query(..., gt=0),  # Greater than 0
        name: str = Query(..., min_length=3, max_length=50)):  # Length constraints
    pass
```

### Available Constraints

| Constraint | Type | Description |
|------------|------|-------------|
| `ge` | Numeric | Greater than or equal |
| `gt` | Numeric | Greater than |
| `le` | Numeric | Less than or equal |
| `lt` | Numeric | Less than |
| `min_length` | String | Minimum string length |
| `max_length` | String | Maximum string length |
| `regex` | String | Regex pattern matching |

## Path Parameters

Extract dynamic segments from URL paths.

```python
from reroute.params import Path

class UserDetailRoutes(RouteBase):
    def get(self, id: int = Path(..., description="User ID", gt=0)):
        return {"user_id": id}
```

**Request:** `GET /users/123`

**Result:** `{"user_id": 123}`

## Header Parameters

Extract HTTP headers (case-insensitive).

```python
from reroute.params import Header

class SecureRoutes(RouteBase):
    def post(self,
             authorization: str = Header(..., description="Bearer token"),
             user_agent: str = Header(None, description="User agent")):
        if not authorization.startswith("Bearer "):
            return {"error": "Invalid auth header"}
        return {"authenticated": True}
```

**Request:**
```http
POST /api/data
Authorization: Bearer abc123
User-Agent: Mozilla/5.0
```

**Result:** Headers automatically extracted and validated

## Body Parameters

Extract and validate JSON request bodies with Pydantic models.

### With Pydantic Models

```python
from reroute.params import Body
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    age: int

class UsersRoutes(RouteBase):
    def post(self, user: UserCreate = Body(..., description="User data")):
        return {
            "message": "User created",
            "user": user.model_dump()
        }
```

**Request:**
```http
POST /users
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "age": 30
}
```

**Result:** Automatic validation and type conversion using Pydantic

### Without Models

```python
def post(self, data: dict = Body(...)):
    return {"received": data}
```

## Cookie Parameters

Extract cookie values.

```python
from reroute.params import Cookie

class SessionRoutes(RouteBase):
    def get(self, session_id: str = Cookie(None, description="Session ID")):
        if not session_id:
            return {"error": "No session"}
        return {"session_id": session_id}
```

## Form Parameters

Handle HTML form data.

```python
from reroute.params import Form

class FormRoutes(RouteBase):
    def post(self,
             username: str = Form(...),
             password: str = Form(...)):
        return {"username": username}
```

## File Parameters

Handle file uploads.

!!! note "Framework-Specific"
    File handling differs between frameworks:

    - **FastAPI**: Use `UploadFile` type for streaming large files
    - **Flask**: Access files via `request.files`

### FastAPI Example

```python
from fastapi import UploadFile
from reroute.params import File

class UploadRoutes(RouteBase):
    async def post(self, file: UploadFile = File(..., description="Upload file")):
        contents = await file.read()
        return {
            "filename": file.filename,
            "size": len(contents),
            "content_type": file.content_type
        }
```

### Flask Example

```python
from flask import request
from reroute import RouteBase

class UploadRoutes(RouteBase):
    def post(self):
        file = request.files.get('file')
        if not file:
            return {"error": "No file uploaded"}, 400
        return {
            "filename": file.filename,
            "size": len(file.read())
        }
```

## Required vs Optional

### Required Parameters

Use `...` (Ellipsis) for required parameters:

```python
name: str = Query(...)  # Required
id: int = Path(...)  # Required
```

Missing required parameters will return a validation error.

### Optional Parameters

Use `None` or a default value:

```python
search: str = Query(None)  # Optional, defaults to None
limit: int = Query(10)  # Optional, defaults to 10
```

## Combining Parameters

You can mix multiple parameter types in a single handler:

```python
from reroute.params import Query, Path, Header, Body
from app.models.user import UserCreate

class UserDetailRoutes(RouteBase):
    def put(self,
            id: int = Path(..., description="User ID"),
            user: UserCreate = Body(..., description="User data"),
            authorization: str = Header(..., description="Auth token"),
            force: bool = Query(False, description="Force update")):

        # All parameters automatically extracted and validated
        return {
            "id": id,
            "user": user.model_dump(),
            "force": force
        }
```

**Request:**
```http
PUT /users/123?force=true
Authorization: Bearer token123
Content-Type: application/json

{
  "name": "Updated Name",
  "email": "new@example.com",
  "age": 31
}
```

## Type Conversion

Parameters are automatically converted to their annotated types:

```python
limit: int = Query(10)  # "20" → 20
is_active: bool = Query(False)  # "true" → True
tags: List[str] = Query([])  # "a,b,c" → ["a", "b", "c"]
```

## Validation Errors

When validation fails, REROUTE returns a detailed error response:

```json
{
  "error": "Required query parameter 'id' is missing",
  "type": "ValueError"
}
```

## Best Practices

1. **Use Pydantic models for complex body data**
   ```python
   user: UserCreate = Body(...)  # Better than dict
   ```

2. **Add descriptions for API documentation**
   ```python
   limit: int = Query(10, description="Maximum number of results")
   ```

3. **Validate inputs with constraints**
   ```python
   age: int = Query(..., ge=0, le=150)
   ```

4. **Use type hints**
   ```python
   name: str = Query(...)  # Type hint helps with IDE autocomplete
   ```

5. **Combine with Pydantic for complex validation**
   ```python
   from pydantic import BaseModel, EmailStr, field_validator

   class UserCreate(BaseModel):
       email: EmailStr
       age: int

       @field_validator('age')
       @classmethod
       def validate_age(cls, v):
           if v < 18:
               raise ValueError('Must be 18 or older')
           return v
   ```

## See Also

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [RouteBase API](routebase.md)
- [Configuration](config.md)
