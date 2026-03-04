# Adapters

REROUTE adapters integrate file-based routing with Python web frameworks.

## Available Adapter

<div class="grid cards" markdown>

-   **FastAPI**

    ---

    High-performance async framework with automatic API docs.

    [:octicons-arrow-right-24: FastAPI Guide](fastapi.md)

</div>

## How Adapters Work

Adapters translate REROUTE's file-based routes into framework-specific routes:

```python
from fastapi import FastAPI
from reroute.adapters import FastAPIAdapter
from pathlib import Path

app = FastAPI()
adapter = FastAPIAdapter(
    fastapi_app=app,
    app_dir=Path(__file__).parent / "app"
)
adapter.register_routes()
```

## Common Features

The FastAPI adapter supports:

- **File-based routing discovery** - Automatic route registration from folder structure
- **HTTP method mapping** - GET, POST, PUT, DELETE, PATCH, OPTIONS
- **Lifecycle hooks** - before_request, after_request, on_error
- **Decorator integration** - Rate limiting, caching, validation
- **Custom configuration** - Framework-specific settings
- **Security headers** - OWASP-compliant security headers (v0.2.0+)

## Why FastAPI?

REROUTE focuses exclusively on FastAPI because it offers:

| Feature | FastAPI |
|---------|---------|
| Async Support | Full async/await support |
| Auto API Docs | Built-in Swagger UI and ReDoc |
| Performance | Excellent (on par with NodeJS and Go) |
| Type Safety | Full Python type hints support |
| Validation | Automatic request/response validation |
| Learning Curve | Medium - easy to learn |

## Framework-Specific Guide

- [FastAPI Integration](fastapi.md) - Async routes, OpenAPI, dependency injection

## Custom Adapters

You can create custom adapters for other frameworks by extending the base adapter class. See the [Adapters API Reference](../api/adapters.md) for the adapter interface.
