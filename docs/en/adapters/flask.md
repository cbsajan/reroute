# Flask Adapter Documentation

## Overview

The Flask adapter integrates REROUTE's file-based routing with Flask applications, providing automatic OpenAPI documentation via Spectree.

## Features

- **File-based routing**: Automatically discovers and registers routes from `routes/` directory
- **OpenAPI documentation**: Swagger UI and Scalar UI via Spectree
- **Dynamic HTTP method decorators**: `@adapter.get()`, `@adapter.post()`, etc.
- **Flexible configuration**: Override config values at runtime
- **CORS support**: Built-in CORS configuration
- **Route validation**: Automatic request/response validation with Pydantic

## Basic Setup

```python
from flask import Flask
from reroute.adapters import FlaskAdapter
from config import AppConfig

# Create Flask app
app = Flask(__name__)

# Initialize REROUTE adapter
adapter = FlaskAdapter(
    flask_app=app,
    app_dir="./app",
    config=AppConfig
)

# Register all file-based routes
adapter.register_routes()

# Add manual routes (optional)
@adapter.get('/')
def root():
    """Welcome endpoint"""
    return {
        "message": "Welcome to My API",
        "docs": "/docs"  # Swagger UI path (configurable via DOCS_PATH)
    }

# Run server
if __name__ == "__main__":
    adapter.run_server()
```

## Configuration

### OpenAPI Configuration

```python
from reroute import Config

class AppConfig(Config):
    # Server Configuration
    HOST = "0.0.0.0"
    PORT = 7376
    DEBUG = False

    # OpenAPI/Swagger Documentation
    class OpenAPI:
        ENABLE = True                    # Enable/disable all documentation

        # Documentation Endpoints
        DOCS_PATH = "/docs"              # Swagger UI (set to None to disable)
        REDOC_PATH = None                # ReDoc disabled (broken CDN)
        JSON_PATH = "/openapi.json"      # OpenAPI spec endpoint

        # API Metadata
        TITLE = "My API"
        VERSION = "1.0.0"
        DESCRIPTION = "My API built with REROUTE"
```

**Note**: ReDoc is disabled for Flask due to broken CDN URLs in Spectree. Use Swagger UI or Scalar UI instead.

## Documentation UIs

When OpenAPI is enabled, the following endpoints are available (paths are configurable):

- **Swagger UI**: `http://localhost:7376/docs` (configured via `DOCS_PATH`)
- **Scalar UI**: `http://localhost:7376/scalar/` (separate endpoint, always available when OpenAPI enabled)
- **OpenAPI Spec**: `http://localhost:7376/openapi.json` (configured via `JSON_PATH`)

**Note:** The actual paths depend on your configuration. The defaults shown above match the config example.

### Disabling Documentation

To disable specific UIs, set their paths to `None`:

```python
class OpenAPI:
    ENABLE = True
    DOCS_PATH = "/docs"      # Swagger enabled
    REDOC_PATH = None        # ReDoc disabled
    JSON_PATH = None         # OpenAPI JSON disabled
```

## HTTP Method Decorators

The adapter provides decorators for all HTTP methods:

```python
# GET request
@adapter.get('/users')
def list_users():
    return {"users": []}

# POST request
@adapter.post('/users')
def create_user():
    return {"id": 1, "name": "John"}

# PUT request
@adapter.put('/users/<int:user_id>')
def update_user(user_id: int):
    return {"id": user_id, "updated": True}

# DELETE request
@adapter.delete('/users/<int:user_id>')
def delete_user(user_id: int):
    return {"deleted": True}

# Generic route (multiple methods)
@adapter.route('/health', methods=['GET', 'HEAD'])
def health():
    return {"status": "healthy"}
```

Available method decorators:
- `@adapter.get(path)`
- `@adapter.post(path)`
- `@adapter.put(path)`
- `@adapter.patch(path)`
- `@adapter.delete(path)`
- `@adapter.head(path)`
- `@adapter.options(path)`
- `@adapter.route(path, methods=[])`

## Request Validation

Use REROUTE params for automatic validation:

```python
from reroute.params import Query, Body, Path

@adapter.get('/users')
def list_users(
    page: int = Query(default=1, description="Page number"),
    limit: int = Query(default=10, description="Items per page")
):
    """List users with pagination"""
    return {
        "page": page,
        "limit": limit,
        "users": []
    }

# Using Pydantic models
from pydantic import BaseModel

class User(BaseModel):
    name: str
    email: str

@adapter.post('/users')
def create_user(user: User = Body()):
    """Create a new user"""
    return {
        "id": 1,
        "name": user.name,
        "email": user.email
    }
```

## Running the Server

### Basic Usage

```python
# Use config defaults
adapter.run_server()
```

### Override Parameters

```python
# Override port
adapter.run_server(port=8080)

# Override multiple parameters
adapter.run_server(
    port=8080,
    debug=True,
    use_reloader=True
)

# Disable debug even if config has DEBUG=True
adapter.run_server(debug=False)
```

### Available Parameters

- `host` (str): Host to bind (default: from config.HOST)
- `port` (int): Port to bind (default: from config.PORT)
- `debug` (bool): Enable debug mode (default: from config.DEBUG)
- `use_reloader` (bool): Enable auto-reloader
- `use_debugger` (bool): Enable debugger
- `threaded` (bool): Handle requests in separate threads
- `processes` (int): Number of processes to spawn

## CORS Configuration

```python
class AppConfig(Config):
    ENABLE_CORS = True
    CORS_ALLOW_ORIGINS = ["*"]  # or ["http://localhost:3000"]
    CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    CORS_ALLOW_HEADERS = ["*"]
    CORS_ALLOW_CREDENTIALS = False
```

## File-Based Routes

Create routes in `app/routes/` directory:

```
app/
└── routes/
    ├── users/
    │   └── page.py
    └── products/
        └── page.py
```

**Example: `app/routes/users/page.py`**

```python
from reroute import RouteBase
from reroute.params import Query

class UserRoutes(RouteBase):
    tag = "Users"  # OpenAPI tag

    def get(self, user_id: int = Query(description="User ID")):
        """Get user by ID"""
        return {"id": user_id, "name": "John"}

    def post(self):
        """Create new user"""
        return {"id": 1, "created": True}
```

## Error Handling

```python
from flask import Flask
from reroute.adapters import FlaskAdapter

app = Flask(__name__)
adapter = FlaskAdapter(app)

@app.errorhandler(404)
def not_found(error):
    return {"error": "Not found"}, 404

@app.errorhandler(500)
def server_error(error):
    return {"error": "Internal server error"}, 500
```

## Best Practices

1. **Use config for defaults, kwargs for overrides**: Keep standard settings in config, use `run_server()` kwargs for temporary changes

2. **Disable unused docs**: Set `REDOC_PATH = None` if not needed

3. **Use Pydantic models**: Leverage Pydantic for request/response validation

4. **Tag your routes**: Use `tag` attribute in RouteBase for organized documentation

5. **Avoid debug in production**: Set `DEBUG = False` in production config

## Troubleshooting

### Documentation not showing

1. Check if `OpenAPI.ENABLE = True` in config
2. Verify `spectree` is installed: `pip install spectree`
3. Ensure paths are not set to `None`

### Routes not registering

1. Verify `routes/` directory exists
2. Check file is named `page.py`
3. Ensure class inherits from `RouteBase`

### CORS errors

1. Set `ENABLE_CORS = True` in config
2. Add your frontend origin to `CORS_ALLOW_ORIGINS`
3. Install flask-cors: `pip install flask-cors`

## See Also

- [FastAPI Adapter Documentation](fastapi.md)
- [Configuration Guide](../guides/configuration.md)
- [REROUTE Documentation Home](../index.md)
- [GitHub Repository](https://github.com/cbsajan/reroute)
