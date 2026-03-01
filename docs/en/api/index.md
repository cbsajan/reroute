# API Reference

Complete API documentation for REROUTE.

## Core Classes

<div class="grid cards" markdown>

-   :material-code-braces: [**RouteBase**](routebase.md)

    ---

    Base class for all file-based routes

-   :material-cog: [**Config**](config.md)

    ---

    Configuration system

-   :material-puzzle: [**Adapters**](adapters.md)

    ---

    Framework integration adapters

</div>

## Decorators

<div class="grid cards" markdown>

-   :material-alpha-d-box: [**Built-in Decorators**](decorators.md)

    ---

    rate_limit, cache, requires, validate, etc.

</div>

## Quick Reference

### RouteBase

```python
from reroute import RouteBase

class MyRoute(RouteBase):
    tag = "Custom Tag"  # Optional Swagger tag

    def get(self):
        """Handle GET requests"""
        pass

    def before_request(self):
        """Run before every request"""
        return None

    def after_request(self, response):
        """Run after successful request"""
        return response

    def on_error(self, error):
        """Handle errors"""
        return {"error": str(error)}
```

### Decorators

```python
from reroute.decorators import rate_limit, cache

@rate_limit("5/min")
@cache(duration=60)
def my_endpoint(self):
    pass
```

**Note:** All decorators (`rate_limit`, `cache`, `requires`, `validate`, `timeout`, `log_requests`) are fully implemented. See [Decorators API](decorators.md) for detailed documentation.

### Config

```python
from reroute import Config

class MyConfig(Config):
    PORT = 8000
    HOST = "0.0.0.0"
    API_BASE_PATH = "/api/v1"
    ENABLE_CORS = True
    CORS_ALLOW_ORIGINS = ["*"]
```

### Adapters

```python
from reroute.adapters import FastAPIAdapter, FlaskAdapter

# FastAPI
adapter = FastAPIAdapter(fastapi_app=app, app_dir=path)
adapter.register_routes()

# Flask
adapter = FlaskAdapter(flask_app=app, app_dir=path)
adapter.register_routes()
```

## Modules

- `reroute.core` - Core routing engine
- `reroute.adapters` - Framework adapters
- `reroute.cli` - Command-line interface
- `reroute.decorators` - Built-in decorators
- `reroute.config` - Configuration system

## Type Hints

REROUTE is fully typed and supports type checking with mypy:

```python
from typing import Dict, Any
from reroute import RouteBase

class TypedRoute(RouteBase):
    def get(self) -> Dict[str, Any]:
        return {"status": "ok"}
```

## Learn More

- [RouteBase API](routebase.md) - Route class methods and hooks
- [Decorators API](decorators.md) - All decorator options
- [Config API](config.md) - Configuration options
- [Adapters API](adapters.md) - Adapter interfaces
