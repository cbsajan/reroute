# FastAPI Complete Example

A comprehensive example of building a high-performance async REST API with REROUTE and FastAPI.

## Project Structure

After running `reroute init` and the commands below:

```
my-fastapi-api/
├── app/
│   ├── __init__.py
│   ├── root.py                     # Root (/) and health (/health) routes
│   ├── models/                     # Created by: reroute create model
│   │   ├── __init__.py
│   │   └── user.py
│   └── routes/
│       ├── __init__.py
│       ├── hello/                  # Auto-generated example
│       │   └── page.py
│       ├── users/                  # Created by: reroute create route
│       │   └── page.py
│       └── products/               # Created by: reroute create route
│           └── page.py
├── tests/
│   ├── __init__.py
│   └── test_main.py
├── config.py
├── logger.py
├── main.py
└── requirements.txt
```

## Installation

```bash
# Create a new REROUTE project
reroute init

# Interactive prompts:
? Project name: my-fastapi-api
? Which framework would you like to use? fastapi
? Would you like to generate test cases? Yes

# Review and confirm:
# Project Name: my-fastapi-api
# Framework: FASTAPI
# Host: 0.0.0.0
# Port: 7376
# Include Tests: Yes
? Does this look correct? Yes

# Navigate to project directory
cd my-fastapi-api

# Generate user model (Pydantic schemas)
reroute create model --name User

# Generate user routes (handles both list and individual user operations)
# Add --http-test flag to generate .http test file automatically
reroute create route --path /users --name UserRoutes --methods GET,POST,PUT,DELETE --http-test

# Generate product routes with HTTP test file
reroute create route --path /products --name ProductRoutes --methods GET,POST --http-test

# Your project structure is now ready!
```

**Note**: The `--http-test` flag is optional. If included, REROUTE automatically generates a `.http` test file in the `tests/` directory with pre-configured API test requests for the route.

**Note**: Dynamic path parameters (like `user_id`) are passed as query parameters in your route methods, not in the folder structure. See the code examples below.

## Configuration

**config.py**

```python
from reroute import Config

class AppConfig(Config):
    # Server Configuration
    HOST = "0.0.0.0"
    PORT = 7376
    AUTO_RELOAD = True

    # OpenAPI Documentation
    class OpenAPI:
        ENABLE = True
        DOCS_PATH = "/docs"              # Swagger UI
        REDOC_PATH = "/redoc"            # ReDoc UI
        JSON_PATH = "/openapi.json"
        TITLE = "My FastAPI API"
        VERSION = "1.0.0"
        DESCRIPTION = "A high-performance REST API built with REROUTE and FastAPI"

    # CORS Configuration
    ENABLE_CORS = True
    CORS_ALLOW_ORIGINS = ["http://localhost:3000"]
    CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    CORS_ALLOW_HEADERS = ["*"]
    CORS_ALLOW_CREDENTIALS = False
```

## Main Application

**main.py**

```python
from pathlib import Path
from fastapi import FastAPI
from reroute.adapters import FastAPIAdapter
from config import AppConfig

# Create FastAPI app
app = FastAPI(
    title="My FastAPI API",
    description="A REST API built with REROUTE and FastAPI",
    version="1.0.0"
)

# Initialize REROUTE adapter
adapter = FastAPIAdapter(
    fastapi_app=app,
    app_dir=Path(__file__).parent / "app",
    config=AppConfig
)

# Register all file-based routes
adapter.register_routes()

# Root endpoint
@app.get("/")
async def root():
    """Welcome endpoint showing API information"""
    return {
        "message": "Welcome to My FastAPI API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json"
    }

# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "framework": "FastAPI + REROUTE"
    }

if __name__ == "__main__":
    adapter.run_server()
```

## Pydantic Models

**app/models/user.py**

```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Base user schema with common fields"""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    age: Optional[int] = Field(None, ge=0, le=150)

class UserCreate(BaseModel):
    """Schema for creating a new user"""
    name: str
    email: EmailStr
    password: str = Field(..., min_length=8)
    age: Optional[int] = None

class UserUpdate(BaseModel):
    """Schema for updating user (all fields optional)"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    age: Optional[int] = None

class UserResponse(BaseModel):
    """Schema for user responses (without password)"""
    id: int
    name: str
    email: EmailStr
    age: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
```

## File-Based Routes

### Important: REROUTE vs FastAPI Imports

**Use REROUTE's parameter system:**
```python
from reroute.params import Query, Body, Path, Header, Cookie  # ✅ Cross-framework compatibility
```

**Use FastAPI's native features:**
```python
from fastapi import HTTPException, BackgroundTasks, Depends  # ✅ FastAPI-specific features
```

**Why?**
- REROUTE's `params` work with both Flask and FastAPI
- FastAPI's exception handling and dependency injection are framework-specific and should be used directly

### User Routes (Async)

**app/routes/users/page.py**

```python
import asyncio
from typing import Optional

from reroute import RouteBase
from reroute.params import Query, Body  # REROUTE's parameter injection
from fastapi import HTTPException  # FastAPI's exception handling
from app.models.user import UserCreate, UserUpdate, UserResponse

# In-memory storage (use async database in production)
users_db = []
next_id = 1

class UserRoutes(RouteBase):
    """User management endpoints - handles both list and individual user operations (async)"""
    tag = "Users"

    async def get(
        self,
        user_id: Optional[int] = Query(default=None, description="User ID for specific user"),
        page: int = Query(default=1, ge=1, description="Page number"),
        limit: int = Query(default=10, ge=1, le=100, description="Items per page")
    ):
        """
        List all users OR get a specific user (async)

        - If user_id is provided: Returns a specific user
        - If user_id is None: Returns paginated list of users
        """
        # Simulate async database call
        await asyncio.sleep(0.01)

        # Get specific user
        if user_id is not None:
            user = next((u for u in users_db if u["id"] == user_id), None)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return user

        # List all users with pagination
        start = (page - 1) * limit
        end = start + limit
        paginated_users = users_db[start:end]

        return {
            "page": page,
            "limit": limit,
            "total": len(users_db),
            "users": paginated_users
        }

    async def post(self, user: UserCreate = Body(...)):
        """
        Create a new user (async)

        Creates a new user with the provided information asynchronously.
        """
        global next_id

        # Check if email already exists
        if any(u["email"] == user.email for u in users_db):
            raise HTTPException(status_code=400, detail="Email already exists")

        # Simulate async database save
        await asyncio.sleep(0.01)

        new_user = {
            "id": next_id,
            "name": user.name,
            "email": user.email,
            "age": user.age,
            "created_at": "2025-11-21T00:00:00"
        }
        users_db.append(new_user)
        next_id += 1

        return new_user

    async def put(
        self,
        user_id: int = Query(..., description="User ID to update"),
        user: UserUpdate = Body(...)
    ):
        """
        Update user (async)

        Updates an existing user's information asynchronously.
        """
        user_idx = next(
            (i for i, u in enumerate(users_db) if u["id"] == user_id),
            None
        )

        if user_idx is None:
            raise HTTPException(status_code=404, detail="User not found")

        # Simulate async database update
        await asyncio.sleep(0.01)

        # Update only provided fields
        if user.name is not None:
            users_db[user_idx]["name"] = user.name
        if user.email is not None:
            users_db[user_idx]["email"] = user.email
        if user.age is not None:
            users_db[user_idx]["age"] = user.age

        return users_db[user_idx]

    async def delete(self, user_id: int = Query(..., description="User ID to delete")):
        """
        Delete user (async)

        Deletes a user by their ID asynchronously.
        """
        user_idx = next(
            (i for i, u in enumerate(users_db) if u["id"] == user_id),
            None
        )

        if user_idx is None:
            raise HTTPException(status_code=404, detail="User not found")

        # Simulate async database delete
        await asyncio.sleep(0.01)

        deleted_user = users_db.pop(user_idx)
        return {"message": "User deleted", "user": deleted_user}
```

### Product Routes with Background Tasks

**app/routes/products/page.py**

```python
import asyncio

from reroute import RouteBase
from reroute.decorators import cache
from reroute.params import Query  # REROUTE's parameter injection
from fastapi import BackgroundTasks  # FastAPI's background tasks

class ProductRoutes(RouteBase):
    """Product management endpoints with caching"""
    tag = "Products"

    @cache(duration=300)  # Cache for 5 minutes
    async def get(
        self,
        category: str = Query(default=None, description="Filter by category"),
        min_price: float = Query(default=None, ge=0, description="Minimum price")
    ):
        """
        List products with optional filters (async + cached)

        Returns a list of products, optionally filtered by category and price.
        Results are cached for 5 minutes.
        """
        # Simulate async database query
        await asyncio.sleep(0.05)

        products = [
            {"id": 1, "name": "Laptop", "price": 999.99, "category": "Electronics"},
            {"id": 2, "name": "Mouse", "price": 29.99, "category": "Electronics"},
            {"id": 3, "name": "Desk", "price": 299.99, "category": "Furniture"},
        ]

        # Apply filters
        if category:
            products = [p for p in products if p["category"] == category]
        if min_price is not None:
            products = [p for p in products if p["price"] >= min_price]

        return {"products": products}

    async def post(self, background_tasks: BackgroundTasks):
        """
        Create a new product (async with background task)

        Creates a new product and sends notifications in the background.
        """
        # Add background task
        background_tasks.add_task(send_notification, "New product created")

        return {"message": "Product created", "notification": "sent in background"}, 201

async def send_notification(message: str):
    """Background task to send notifications"""
    await asyncio.sleep(2)  # Simulate email sending
    print(f"Notification sent: {message}")
```

## Running the Application

```bash
# Development (with auto-reload)
python main.py

# Production with multiple workers
adapter.run_server(workers=4, reload=False, log_level="warning")
```

## API Documentation

Once running, access the documentation at:

- **Swagger UI**: http://localhost:7376/docs
- **ReDoc UI**: http://localhost:7376/redoc
- **OpenAPI JSON**: http://localhost:7376/openapi.json

## Testing

REROUTE can automatically generate `.http` test files when you use the `--http-test` flag. These files contain pre-configured HTTP requests for testing your API directly in VS Code (with REST Client extension) or other HTTP clients.

### Auto-Generated HTTP Test Files

If you used `--http-test` when creating routes, you'll have test files in the `tests/` directory with ready-to-use requests:

**tests/users.http** (auto-generated)
```http
### List all users
GET http://localhost:7376/users

### Create a new user
POST http://localhost:7376/users
Content-Type: application/json

{
  "name": "Test User",
  "email": "test@example.com",
  "password": "password123",
  "age": 25
}

### Get specific user
GET http://localhost:7376/users?user_id=1

### Update user
PUT http://localhost:7376/users?user_id=1
Content-Type: application/json

{
  "name": "Updated Name",
  "age": 30
}

### Delete user
DELETE http://localhost:7376/users?user_id=1
```

### Manual .http Files

You can also create custom test files manually:

**test_users.http**

```http
### Get all users
GET http://localhost:7376/users

### Create a new user
POST http://localhost:7376/users
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepass123",
  "age": 30
}

### Get specific user (using query parameter)
GET http://localhost:7376/users?user_id=1

### Update user (using query parameter)
PUT http://localhost:7376/users?user_id=1
Content-Type: application/json

{
  "name": "John Updated",
  "age": 31
}

### Delete user (using query parameter)
DELETE http://localhost:7376/users?user_id=1

### Test products with filters
GET http://localhost:7376/products?category=Electronics&min_price=50
```

### How to Use .http Files

**VS Code (Recommended)**:
1. Install the [REST Client extension](https://marketplace.visualstudio.com/items?itemName=humao.rest-client)
2. Open any `.http` file
3. Click "Send Request" above each request or press `Ctrl+Alt+R`

**Other Clients**:
- IntelliJ IDEA / PyCharm (built-in support)
- Postman (import as collection)
- Insomnia (import as workspace)

### Using curl

```bash
# List users
curl http://localhost:7376/users

# Create user
curl -X POST http://localhost:7376/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane","email":"jane@example.com","password":"pass123","age":25}'

# Get user by ID (using query parameter)
curl "http://localhost:7376/users?user_id=1"

# Update user (using query parameter)
curl -X PUT "http://localhost:7376/users?user_id=1" \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane Updated"}'

# Delete user (using query parameter)
curl -X DELETE "http://localhost:7376/users?user_id=1"

# Get products with filter
curl "http://localhost:7376/products?category=Electronics"
```

## Key Features Demonstrated

1. **Async/Await** - Full async support for high concurrency
2. **OpenAPI Documentation** - Automatic Swagger UI and ReDoc
3. **Request Validation** - Pydantic models for type safety
4. **Query Parameters** - Pagination and filtering
5. **Body Validation** - Structured request bodies
6. **Background Tasks** - Non-blocking operations
7. **Caching** - Improve performance for expensive operations
8. **CORS** - Cross-origin requests for frontend integration
9. **HTTPException** - Proper error handling
10. **Auto-Reload** - Automatic module detection for development
11. **File-Based Routing** - Organized route structure
12. **Auto-Generated HTTP Tests** - `.http` files with `--http-test` flag

## Performance Tips

1. **Use async for I/O operations**: Database calls, API requests, file operations
2. **Enable multiple workers in production**: `adapter.run_server(workers=4)`
3. **Cache expensive operations**: Use `@cache()` decorator
4. **Use background tasks**: For non-critical operations like emails
5. **Disable docs in production**: Set `OpenAPI.ENABLE = False`

## Deployment

### Docker

**Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run with uvicorn
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi
  template:
    metadata:
      labels:
        app: fastapi
    spec:
      containers:
      - name: fastapi
        image: my-fastapi-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: WORKERS
          value: "2"
```

## Troubleshooting

### Problem 1: IndentationError in config.py

**Error:**
```
IndentationError: unexpected indent
```

**Solution:**
This is caused by a bug in earlier versions of the REROUTE template. Update REROUTE to the latest version:
```bash
pip install --upgrade reroute
```

Or manually fix `config.py` by ensuring each line under `class OpenAPI:` is properly indented with 8 spaces.

### Problem 2: Auto-reload not working

**Symptom:** Changes to route files don't trigger server restart

**Solutions:**
1. Ensure `AUTO_RELOAD = True` in `config.py`:
```python
class AppConfig(Config):
    AUTO_RELOAD = True
```

2. Run with reload enabled:
```python
adapter.run_server(reload=True)
```

3. Check uvicorn is installed: `pip install uvicorn[standard]`

### Problem 3: RuntimeWarning: coroutine was never awaited

**Error:**
```
RuntimeWarning: coroutine 'UserRoutes.get' was never awaited
```

**Solution:**
Ensure async route methods are called with `await`:
```python
# Correct:
async def get(self):
    result = await some_async_function()
    return result

# Wrong:
def get(self):  # Missing 'async'
    result = await some_function()  # Can't await in non-async function
```

### Problem 4: HTTPException not returning proper status codes

**Symptom:** All errors return 500 instead of specified status codes

**Solution:**
Use FastAPI's `HTTPException` for error handling:
```python
from fastapi import HTTPException  # FastAPI-specific

async def get(self, user_id: int):
    user = await get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

Don't return tuples like Flask - FastAPI uses `HTTPException`.

### Problem 5: Pydantic validation errors

**Error:**
```
pydantic.error_wrappers.ValidationError: 1 validation error
```

**Common Causes:**
1. **Missing required fields:** Request body doesn't include all required fields
2. **Wrong data types:** Sending string where int is expected
3. **Email validation:** Invalid email format when using `EmailStr`

**Solution:**
1. Check your Pydantic model requirements:
```python
class UserCreate(BaseModel):
    name: str  # Required
    email: EmailStr  # Required and must be valid email
    age: Optional[int] = None  # Optional
```

2. Send correct data in requests:
```json
{
  "name": "John",
  "email": "valid@email.com",
  "age": 30
}
```

3. Install email validation: `pip install pydantic[email]`

## Next Steps

- Add async database integration (Tortoise ORM, SQLAlchemy with asyncpg)
- Implement JWT authentication
- Add WebSocket support for real-time features
- Set up Redis for distributed caching
- Add comprehensive error handling
- Implement request/response logging
- Deploy with Docker and Kubernetes

## See Also

- [FastAPI Adapter Documentation](../adapters/fastapi.md)
- [Flask Example](flask-example.md)
- [Configuration Guide](../guides/configuration.md)
- [Async Best Practices](https://fastapi.tiangolo.com/async/)
