# Flask Complete Example

A comprehensive example of building a REST API with REROUTE and Flask.

## Project Structure

After running `reroute init` and the commands below:

```
my-flask-api/
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
? Project name: my-flask-api
? Which framework would you like to use? flask
? Would you like to generate test cases? Yes

# Review and confirm:
# Project Name: my-flask-api
# Framework: FLASK
# Host: 0.0.0.0
# Port: 7376
# Include Tests: Yes
? Does this look correct? Yes

# Navigate to project directory
cd my-flask-api

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

**Note**: Dynamic path parameters (like `user_id`) are handled in your route methods, not in the folder structure. See the code examples below.

## Configuration

**config.py**

```python
from reroute import Config

class AppConfig(Config):
    # Server Configuration
    HOST = "0.0.0.0"
    PORT = 7376
    DEBUG = True

    # OpenAPI Documentation
    class OpenAPI:
        ENABLE = True
        DOCS_PATH = "/docs"              # Swagger UI
        REDOC_PATH = None                # ReDoc disabled
        JSON_PATH = "/openapi.json"
        TITLE = "My Flask API"
        VERSION = "1.0.0"
        DESCRIPTION = "A REST API built with REROUTE and Flask"

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
from flask import Flask
from reroute.adapters import FlaskAdapter
from config import AppConfig

# Create Flask app
app = Flask(__name__)

# Initialize REROUTE adapter
adapter = FlaskAdapter(
    flask_app=app,
    app_dir=Path(__file__).parent / "app",
    config=AppConfig
)

# Register all file-based routes
adapter.register_routes()

# Root endpoint
@adapter.get('/')
def root():
    """Welcome endpoint showing API information"""
    return {
        "message": "Welcome to My Flask API",
        "version": "1.0.0",
        "docs": "/swagger/",
        "openapi": "/openapi.json"
    }

# Health check endpoint
@adapter.get('/health')
def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "framework": "Flask + REROUTE"
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
```

## File-Based Routes

### Important: Using REROUTE's Parameter System

**Always use REROUTE's parameter injection:**
```python
from reroute.params import Query, Body, Path, Header, Cookie  # ✅ Works with Flask and FastAPI
```

**Why?**
- REROUTE provides a unified parameter system that works across both Flask and FastAPI
- Ensures your code is portable and framework-agnostic
- Automatic validation and OpenAPI documentation generation

### User Routes

**app/routes/users/page.py**

```python
from reroute import RouteBase
from reroute.params import Query, Body
from app.models.user import UserCreate, UserUpdate, UserResponse
from typing import Optional

# In-memory storage (use database in production)
users_db = []
next_id = 1

class UserRoutes(RouteBase):
    """User management endpoints - handles both list and individual user operations"""
    tag = "Users"

    def get(
        self,
        user_id: Optional[int] = Query(default=None, description="User ID for specific user"),
        page: int = Query(default=1, ge=1, description="Page number"),
        limit: int = Query(default=10, ge=1, le=100, description="Items per page")
    ):
        """
        List all users OR get a specific user

        - If user_id is provided: Returns a specific user
        - If user_id is None: Returns paginated list of users
        """
        # Get specific user
        if user_id is not None:
            user = next((u for u in users_db if u["id"] == user_id), None)
            if not user:
                return {"error": "User not found"}, 404
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

    def post(self, user: UserCreate = Body()):
        """
        Create a new user

        Creates a new user with the provided information.
        """
        global next_id

        # Check if email already exists
        if any(u["email"] == user.email for u in users_db):
            return {"error": "Email already exists"}, 400

        new_user = {
            "id": next_id,
            "name": user.name,
            "email": user.email,
            "age": user.age,
            "created_at": "2025-11-21T00:00:00"
        }
        users_db.append(new_user)
        next_id += 1

        return new_user, 201

    def put(
        self,
        user_id: int = Query(description="User ID to update"),
        user: UserUpdate = Body()
    ):
        """
        Update user

        Updates an existing user's information.
        """
        user_idx = next(
            (i for i, u in enumerate(users_db) if u["id"] == user_id),
            None
        )

        if user_idx is None:
            return {"error": "User not found"}, 404

        # Update only provided fields
        if user.name is not None:
            users_db[user_idx]["name"] = user.name
        if user.email is not None:
            users_db[user_idx]["email"] = user.email
        if user.age is not None:
            users_db[user_idx]["age"] = user.age

        return users_db[user_idx]

    def delete(self, user_id: int = Query(description="User ID to delete")):
        """
        Delete user

        Deletes a user by their ID.
        """
        user_idx = next(
            (i for i, u in enumerate(users_db) if u["id"] == user_id),
            None
        )

        if user_idx is None:
            return {"error": "User not found"}, 404

        deleted_user = users_db.pop(user_idx)
        return {"message": "User deleted", "user": deleted_user}
```

### Product Routes

**app/routes/products/page.py**

```python
from reroute import RouteBase
from reroute.decorators import cache, rate_limit
from reroute.params import Query

class ProductRoutes(RouteBase):
    """Product management endpoints"""
    tag = "Products"

    @cache(duration=300)  # Cache for 5 minutes
    def get(
        self,
        category: str = Query(default=None, description="Filter by category"),
        min_price: float = Query(default=None, ge=0, description="Minimum price")
    ):
        """
        List products with optional filters

        Returns a list of products, optionally filtered by category and price.
        """
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

    @rate_limit("10/min")  # Max 10 requests per minute
    def post(self):
        """
        Create a new product

        Creates a new product (rate limited to prevent abuse).
        """
        return {"message": "Product created"}, 201
```

## Running the Application

```bash
# Development (with auto-reload)
python main.py

# Production
adapter.run_server(debug=False, threaded=True)
```

## API Documentation

Once running, access the documentation at:

- **Swagger UI**: http://localhost:7376/swagger/
- **Scalar UI**: http://localhost:7376/scalar/
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
```

## Key Features Demonstrated

1. **OpenAPI Documentation** - Automatic Swagger UI with Spectree
2. **Request Validation** - Pydantic models for type safety
3. **Query Parameters** - Pagination and filtering
4. **Body Validation** - Structured request bodies
5. **Rate Limiting** - Protect endpoints from abuse
6. **Caching** - Improve performance for expensive operations
7. **CORS** - Cross-origin requests for frontend integration
8. **Error Handling** - Proper HTTP status codes
9. **File-Based Routing** - Organized route structure
10. **Auto-Generated HTTP Tests** - `.http` files with `--http-test` flag

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

### Problem 2: ModuleNotFoundError: No module named 'spectree'

**Error:**
```
ModuleNotFoundError: No module named 'spectree'
```

**Solution:**
Flask adapter requires Spectree for OpenAPI support. Install it:
```bash
pip install spectree
```

Or install with Flask extras:
```bash
pip install reroute[flask]
```

### Problem 3: Routes not being registered

**Symptom:** Routes defined in `app/routes/` are not accessible (404 errors)

**Common Causes:**
1. **Missing page.py file:** Route files must be named `page.py`
2. **Wrong directory structure:** Ensure routes are in `app/routes/`
3. **Class not inheriting RouteBase:** Route class must inherit from `reroute.RouteBase`

**Solution:**
```python
# Correct structure:
# app/routes/users/page.py
from reroute import RouteBase

class UserRoutes(RouteBase):  # Must inherit RouteBase
    def get(self):
        return {"message": "Users"}
```

### Problem 4: Swagger UI shows 404

**Symptom:** Accessing `/swagger/` returns 404

**Solutions:**
1. Check `config.py` has OpenAPI enabled:
```python
class OpenAPI:
    ENABLE = True
    DOCS_PATH = "/docs"
```

2. Ensure Spectree is installed: `pip install spectree`

3. Verify Flask app is using the adapter:
```python
adapter = FlaskAdapter(flask_app=app, app_dir="./app", config=AppConfig)
adapter.register_routes()
```

### Problem 5: CORS errors in browser

**Error:** `Access-Control-Allow-Origin` header missing

**Solution:**
Enable CORS in `config.py`:
```python
class AppConfig(Config):
    ENABLE_CORS = True
    CORS_ALLOW_ORIGINS = ["http://localhost:3000"]  # Add your frontend URL
    CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE"]
```

Or install Flask-CORS manually if not working:
```bash
pip install flask-cors
```

## Next Steps

- Add database integration (SQLAlchemy, Peewee)
- Implement authentication (JWT, OAuth2)
- Add input sanitization
- Set up logging and monitoring
- Deploy to production

## See Also

- [Flask Adapter Documentation](../adapters/flask.md)
- [FastAPI Example](fastapi-example.md)
- [Configuration Guide](../guides/configuration.md)
