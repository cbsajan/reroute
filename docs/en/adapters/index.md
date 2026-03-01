# Adapters

REROUTE adapters integrate file-based routing with different Python web frameworks.

## Available Adapters

<div class="grid cards" markdown>

-   **FastAPI**

    ---

    High-performance async framework with automatic API docs.

    [:octicons-arrow-right-24: FastAPI Guide](fastapi.md)

-   **Flask**

    ---

    Lightweight and flexible WSGI framework with Swagger UI support.

    [:octicons-arrow-right-24: Flask Guide](flask.md)

-   **Django**

    ---

    Full-featured framework (coming soon).

    [:octicons-arrow-right-24: Django Guide](django.md)

</div>

## How Adapters Work

Adapters translate REROUTE's file-based routes into framework-specific routes:

=== "FastAPI"

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

=== "Flask"

    ```python
    from flask import Flask
    from reroute.adapters import FlaskAdapter
    from pathlib import Path

    app = Flask(__name__)
    adapter = FlaskAdapter(
        flask_app=app,
        app_dir=Path(__file__).parent / "app"
    )
    adapter.register_routes()
    ```

## Common Features

All adapters support:

- **File-based routing discovery** - Automatic route registration from folder structure
- **HTTP method mapping** - GET, POST, PUT, DELETE, PATCH, OPTIONS
- **Lifecycle hooks** - before_request, after_request, on_error
- **Decorator integration** - Rate limiting, caching, validation
- **Custom configuration** - Framework-specific settings
- **Security headers** - OWASP-compliant security headers (v0.2.0+)

## Choosing an Adapter

| Feature | FastAPI | Flask | Django |
|---------|---------|-------|--------|
| Async Support | Full | Partial | Full |
| Auto API Docs | Built-in (Swagger/ReDoc) | Via Flask-Swagger | No |
| Performance | Excellent | Good | Good |
| Learning Curve | Medium | Low | High |
| REROUTE Support | Full | Full | Coming Soon |

## Framework-Specific Guides

- [FastAPI Integration](fastapi.md) - Async routes, OpenAPI, dependency injection
- [Flask Integration](flask.md) - Blueprints, extensions, Swagger UI
- [Django Integration](django.md) - Coming soon

## Custom Adapters

You can create custom adapters for other frameworks by extending the base adapter class. See the [Adapters API Reference](../api/adapters.md) for the adapter interface.
