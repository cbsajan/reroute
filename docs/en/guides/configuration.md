# Configuration

Customize REROUTE's behavior with configuration options.

## Basic Configuration

```python
from reroute import Config

class MyConfig(Config):
    PORT = 8000
    HOST = "0.0.0.0"
    DEBUG = True
```

## Available Options

### Server Settings
- `PORT` - Server port (default: 8000)
- `HOST` - Server host (default: "127.0.0.1")
- `DEBUG` - Debug mode (default: False)
- `AUTO_RELOAD` - Auto-reload on changes (default: True)

### Routing
- `API_BASE_PATH` - Base path for routes (default: "/")
- `ROUTES_DIR` - Routes directory (default: "app/routes")

### CORS
- `ENABLE_CORS` - Enable CORS (default: False)
- `CORS_ALLOW_ORIGINS` - Allowed origins
- `CORS_ALLOW_METHODS` - Allowed methods
- `CORS_ALLOW_HEADERS` - Allowed headers

### Logging
- `VERBOSE_LOGGING` - Verbose logs (default: False)
- `LOG_LEVEL` - Log level (default: "INFO")

### OpenAPI Documentation

Configure API documentation using the `OpenAPI` nested class:

```python
class MyConfig(Config):
    class OpenAPI:
        ENABLE = True                    # Enable/disable OpenAPI docs
        TITLE = "My API"                 # API title
        VERSION = "1.0.0"                # API version
        DESCRIPTION = "My API docs"      # API description
        DOCS_PATH = "/docs"              # Swagger UI path
        REDOC_PATH = "/redoc"            # ReDoc path (set to None to disable)
        JSON_PATH = "/openapi.json"      # OpenAPI JSON specification path
```

#### Adapter-Specific Behavior

**FastAPI:**

- `JSON_PATH` is fully customizable and defines the exact URL endpoint
- Required when `ENABLE = True` (application exits with error if `None`)

```python
JSON_PATH = "/api/v1/openapi.json"  # Spec available at this exact URL
```

**Flask (Spectree):**

- `JSON_PATH` setting is not used
- The JSON specification path is automatically derived from `DOCS_PATH`

```python
DOCS_PATH = "/docs"   # JSON spec available at: /docs/openapi.json
DOCS_PATH = "/api"    # JSON spec available at: /api/openapi.json
```

## Usage

```python
from reroute.adapters import FastAPIAdapter

adapter = FastAPIAdapter(
    fastapi_app=app,
    app_dir=path,
    config=MyConfig
)
```
