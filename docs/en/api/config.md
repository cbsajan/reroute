# Config API

Configuration class for REROUTE with support for environment variables and nested configuration.

## Basic Usage

```python
from reroute import Config, DevConfig, ProdConfig

# Use default config
class MyConfig(Config):
    PORT = 8000
    DEBUG = True

# Or use predefined configs
DevConfig.load_from_env()  # Loads from .env.dev
ProdConfig.load_from_env()  # Loads from .env.prod
```

## Configuration Structure

REROUTE configuration is organized into three parts:

### 1. Config.Internal (Framework Internals - PROTECTED)
Framework-critical settings that **cannot be modified**. These ensure REROUTE works correctly.

```python
Config.Internal.ROUTES_DIR_NAME  # "routes"
Config.Internal.ROUTE_FILE_NAME  # "page.py"
Config.Internal.SUPPORTED_HTTP_METHODS  # ["get", "post", ...]
Config.Internal.IGNORE_FOLDERS  # ["__pycache__", ".git", ...]
```

⚠️ **Warning:** Attempting to override `Config.Internal` in a child class will raise a `TypeError`.

### 2. Config.Env (Environment Configuration)
Controls how environment variables are loaded from `.env` files.

```python
class Config:
    class Env:
        file = ".env"  # Path to .env file
        auto_load = True  # Automatically load on startup
        override = True  # Override existing env vars
```

### 3. User Settings (Top-level)
All other configuration options that developers can customize.

## Server Options

### PORT
Server port number.
- Type: `int`
- Default: `8000`

### HOST
Server host address.
- Type: `str`
- Default: `"127.0.0.1"`

### DEBUG
Enable debug mode.
- Type: `bool`
- Default: `False`

### AUTO_RELOAD
Auto-reload on code changes.
- Type: `bool`
- Default: `True`

## Routing Options

### API_BASE_PATH
Base path for all routes.
- Type: `str`
- Default: `"/"`

### ROUTES_DIR
Routes directory path.
- Type: `str`
- Default: `"app/routes"`

## CORS Options

### ENABLE_CORS
Enable CORS.
- Type: `bool`
- Default: `False`

### CORS_ALLOW_ORIGINS
Allowed origins for CORS.
- Type: `List[str]`
- Default: `["*"]`

### CORS_ALLOW_METHODS
Allowed HTTP methods.
- Type: `List[str]`
- Default: `["GET", "POST", "PUT", "DELETE"]`

### CORS_ALLOW_HEADERS
Allowed headers.
- Type: `List[str]`
- Default: `["*"]`

## Logging Options

### VERBOSE_LOGGING
Enable verbose logging.
- Type: `bool`
- Default: `False`

### LOG_LEVEL
Logging level.
- Type: `str`
- Default: `"INFO"`
- Options: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"`

## Health Check Options (v0.2.0+)

Built-in health check endpoint for monitoring and load balancers.

### HEALTH_CHECK_ENABLED
Enable the health check endpoint.
- Type: `bool`
- Default: `True`

### HEALTH_CHECK_PATH
Path for the health check endpoint.
- Type: `str`
- Default: `"/health"`

**Usage:**
```python
from reroute import Config

class AppConfig(Config):
    # Enable health check (default)
    HEALTH_CHECK_ENABLED = True
    HEALTH_CHECK_PATH = "/health"

# Or disable if using custom health checks
class CustomConfig(Config):
    HEALTH_CHECK_ENABLED = False
```

**Response Format:**
```json
{
  "status": "healthy",
  "service": "My API",
  "version": "1.0.0"
}
```

The health check endpoint is automatically registered with both FastAPI and Flask adapters.

## Environment Variables

### Loading from .env Files

REROUTE supports automatic loading of environment variables from `.env` files:

```python
# Load from default .env file
Config.load_from_env()

# Load from custom file
Config.load_from_env(".env.production")

# DevConfig loads from .env.dev automatically
DevConfig.load_from_env()

# ProdConfig loads from .env.prod automatically
ProdConfig.load_from_env()
```

### Environment Variable Format

All environment variables must be prefixed with `REROUTE_*`:

**.env Example:**
```bash
# Server Configuration
REROUTE_HOST=0.0.0.0
REROUTE_PORT=8000

# Framework Behavior
REROUTE_DEBUG=True
REROUTE_VERBOSE_LOGGING=True
REROUTE_LOG_LEVEL=DEBUG
REROUTE_AUTO_RELOAD=True

# CORS Configuration
REROUTE_ENABLE_CORS=True
REROUTE_CORS_ALLOW_ORIGINS=http://localhost:3000,http://localhost:5173

# API Configuration
REROUTE_API_BASE_PATH=/api/v1
```

### Type Conversion

Environment variables are automatically converted to the correct type:

- **Boolean**: `True`, `true`, `1`, `yes`, `on` → `True`
- **Integer**: `"8000"` → `8000`
- **List**: `"a,b,c"` → `["a", "b", "c"]`
- **String**: Used as-is

### Custom .env Files by Environment

```python
class DevConfig(Config):
    class Env:
        file = ".env.dev"
        auto_load = True
        override = True  # Override system env vars

    DEBUG = True
    LOG_LEVEL = "DEBUG"

class ProdConfig(Config):
    class Env:
        file = ".env.prod"
        auto_load = True
        override = False  # Don't override system env vars

    DEBUG = False
    LOG_LEVEL = "WARNING"
```

### Requirements

Install `python-dotenv` for `.env` file support:

```bash
pip install python-dotenv
```

If not installed, REROUTE will only load from system environment variables.

## Protected Settings (Config.Internal)

The following settings are **framework-critical** and cannot be modified:

| Setting | Value | Purpose |
|---------|-------|---------|
| `ROUTES_DIR_NAME` | `"routes"` | Directory name for routes |
| `ROUTE_FILE_NAME` | `"page.py"` | File name for route handlers |
| `SUPPORTED_HTTP_METHODS` | `["get", "post", ...]` | Supported HTTP methods |
| `ALLOWED_ROUTE_EXTENSIONS` | `[".py"]` | Allowed route file extensions |
| `ENABLE_PATH_VALIDATION` | `True` | Enable security path validation |
| `IGNORE_FOLDERS` | `["__pycache__", ...]` | Folders to ignore during route discovery |
| `IGNORE_FILES` | `["__init__.py", ...]` | Files to ignore during route loading |

Attempting to override these will raise a `TypeError`:

```python
# This will FAIL with TypeError
class BadConfig(Config):
    class Internal:
        ROUTES_DIR_NAME = "custom"  # ERROR!
```

## Predefined Configurations

### DevConfig
Optimized for development:
- `.env.dev` file
- `DEBUG = True`
- `LOG_LEVEL = "DEBUG"`
- `AUTO_RELOAD = True`
- `VERBOSE_LOGGING = True`

### ProdConfig
Optimized for production:
- `.env.prod` file
- `DEBUG = False`
- `LOG_LEVEL = "WARNING"`
- `AUTO_RELOAD = False`
- `VERBOSE_LOGGING = False`
- `Env.override = False` (respects system env vars)
