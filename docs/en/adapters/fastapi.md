# FastAPI Adapter Documentation

## Overview

The FastAPI adapter integrates REROUTE's file-based routing with FastAPI applications, providing seamless OpenAPI documentation and automatic validation.

## Features

- **File-based routing**: Automatically discovers and registers routes from `routes/` directory
- **Native OpenAPI support**: Built-in Swagger UI and ReDoc (can be disabled)
- **Auto-reload**: Automatic module detection for uvicorn reload
- **Flexible configuration**: Override config values at runtime
- **CORS support**: Built-in CORS middleware
- **Type validation**: Automatic request/response validation via Pydantic

## Basic Setup

```python
from fastapi import FastAPI
from reroute.adapters import FastAPIAdapter
from config import AppConfig

# Create FastAPI app
app = FastAPI()

# Initialize REROUTE adapter
adapter = FastAPIAdapter(
    fastapi_app=app,
    app_dir="./app",
    config=AppConfig
)

# Register all file-based routes
adapter.register_routes()

# Add manual routes (optional)
@app.get("/")
def root():
    """Welcome endpoint"""
    return {
        "message": "Welcome to My API",
        "docs": "/docs"
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
    AUTO_RELOAD = True

    # OpenAPI/Swagger Documentation
    class OpenAPI:
        ENABLE = True                    # Enable/disable all documentation

        # Documentation Endpoints
        DOCS_PATH = "/docs"              # Swagger UI (set to None to disable)
        REDOC_PATH = "/redoc"            # ReDoc UI (set to None to disable)
        JSON_PATH = "/openapi.json"      # OpenAPI spec endpoint

        # API Metadata
        TITLE = "My API"
        VERSION = "1.0.0"
        DESCRIPTION = "My API built with REROUTE"
```

## Documentation UIs

When OpenAPI is enabled, the following endpoints are available:

- **Swagger UI**: `http://localhost:7376/docs`
- **ReDoc UI**: `http://localhost:7376/redoc`
- **OpenAPI Spec**: `http://localhost:7376/openapi.json`

### Disabling Documentation

To disable specific UIs, set their paths to `None`:

```python
class OpenAPI:
    ENABLE = True
    DOCS_PATH = "/docs"      # Swagger enabled
    REDOC_PATH = None        # ReDoc disabled
    JSON_PATH = None         # OpenAPI JSON disabled
```

**Note**: When you set a path to `None`, the route is completely removed from FastAPI - you'll get a 404 when accessing it.

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
    reload=False,
    workers=4
)

# Custom log level
adapter.run_server(
    log_level="debug",
    access_log=True
)
```

### Available Parameters

Common uvicorn parameters:

- `host` (str): Host to bind (default: from config.HOST)
- `port` (int): Port to bind (default: from config.PORT)
- `reload` (bool): Enable auto-reload (default: from config.AUTO_RELOAD)
- `workers` (int): Number of worker processes
- `log_level` (str): Logging level ("critical", "error", "warning", "info", "debug", "trace")
- `access_log` (bool): Enable access log
- `use_colors` (bool): Enable colored logging
- `proxy_headers` (bool): Enable X-Forwarded-Proto, X-Forwarded-For headers
- `forwarded_allow_ips` (str): Comma-separated list of IPs to trust with proxy headers

### Auto-Reload

When `AUTO_RELOAD = True` or `reload=True` is passed, the adapter automatically detects the import string:

```python
# This automatically becomes: uvicorn main:app --reload
adapter.run_server(reload=True)
```

Output:
```
[INFO] Auto-reload enabled: main:app
```

## Request Validation

FastAPI automatically validates requests using Pydantic models:

```python
from fastapi import Query
from pydantic import BaseModel

class User(BaseModel):
    name: str
    email: str
    age: int

@app.post("/users")
def create_user(user: User):
    """Create a new user"""
    return {
        "id": 1,
        "name": user.name,
        "email": user.email
    }

@app.get("/users")
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
```

## CORS Configuration

```python
class AppConfig(Config):
    ENABLE_CORS = True
    CORS_ALLOW_ORIGINS = ["*"]  # or ["http://localhost:3000"]
    CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    CORS_ALLOW_HEADERS = ["*"]
    CORS_ALLOW_CREDENTIALS = False
```

CORS is implemented via FastAPI's CORSMiddleware.

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
from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    email: str

class UserRoutes(RouteBase):
    tag = "Users"  # OpenAPI tag

    def get(self, user_id: int):
        """Get user by ID"""
        return {"id": user_id, "name": "John"}

    def post(self, user: UserCreate):
        """Create new user"""
        return {
            "id": 1,
            "name": user.name,
            "email": user.email
        }
```

## Error Handling

```python
from fastapi import FastAPI, HTTPException
from reroute.adapters import FastAPIAdapter

app = FastAPI()
adapter = FastAPIAdapter(app)

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Not found"}

@app.exception_handler(500)
async def server_error_handler(request, exc):
    return {"error": "Internal server error"}

# Custom exception
class UserNotFoundError(Exception):
    pass

@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(request, exc):
    return {"error": "User not found"}
```

## Async Support

FastAPI fully supports async/await:

```python
from reroute import RouteBase

class UserRoutes(RouteBase):
    async def get(self, user_id: int):
        """Async get user"""
        # Simulate async DB call
        await asyncio.sleep(0.1)
        return {"id": user_id, "name": "John"}

    async def post(self, user: UserCreate):
        """Async create user"""
        await save_to_db(user)
        return {"id": 1, "created": True}
```

## Background Tasks

```python
from fastapi import BackgroundTasks

@app.post("/send-email")
def send_email(email: str, background_tasks: BackgroundTasks):
    """Send email in background"""
    background_tasks.add_task(send_email_task, email)
    return {"message": "Email will be sent"}

def send_email_task(email: str):
    # Actual email sending logic
    pass
```

## Dependencies

Use FastAPI's dependency injection:

```python
from fastapi import Depends

def get_current_user(token: str = Header()):
    # Verify token and return user
    return {"id": 1, "name": "John"}

@app.get("/me")
def get_me(user = Depends(get_current_user)):
    """Get current user"""
    return user
```

## Best Practices

1. **Use config for defaults, kwargs for overrides**: Keep standard settings in config, use `run_server()` kwargs for temporary changes

2. **Disable unused docs**: Set `REDOC_PATH = None` if you only use Swagger

3. **Use async when possible**: Async routes improve performance for I/O-bound operations

4. **Tag your routes**: Use `tag` attribute in RouteBase for organized documentation

5. **Enable reload in development**: Set `AUTO_RELOAD = True` in DevConfig

6. **Use dependency injection**: Leverage FastAPI's Depends for authentication, database connections, etc.

## Troubleshooting

### Auto-reload not working

1. Make sure `AUTO_RELOAD = True` or pass `reload=True`
2. Verify the adapter can detect the module (check for "[INFO] Auto-reload enabled" message)
3. If it shows a warning, run directly: `uvicorn main:app --reload`

### Documentation not showing

1. Check if `OpenAPI.ENABLE = True` in config
2. Verify paths are not set to `None`
3. Access the correct URLs: `/docs` or `/redoc`

### Routes not registering

1. Verify `routes/` directory exists
2. Check file is named `page.py`
3. Ensure class inherits from `RouteBase`
4. Check for any import errors in your route files

### CORS errors

1. Set `ENABLE_CORS = True` in config
2. Add your frontend origin to `CORS_ALLOW_ORIGINS`
3. Verify `CORS_ALLOW_CREDENTIALS` setting

## Deployment

### Production Settings

```python
class ProdConfig(Config):
    DEBUG = False
    AUTO_RELOAD = False
    LOG_LEVEL = "WARNING"

    class OpenAPI:
        ENABLE = False  # Disable docs in production

# Run with multiple workers
adapter.run_server(workers=4, log_level="warning")
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Uvicorn Direct

If you prefer running uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## See Also

- [Flask Adapter Documentation](flask.md)
- [Configuration Guide](../guides/configuration.md)
- [REROUTE Documentation Home](../index.md)
- [GitHub Repository](https://github.com/cbsajan/reroute)
- [FastAPI Official Documentation](https://fastapi.tiangolo.com/)
