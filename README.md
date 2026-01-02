<div align="center">
  <img src="assets/logo-light.svg" alt="REROUTE Logo" width="200">
  <h1>REROUTE</h1>
  <p><em>File-based routing for Python backends</em></p>
  <p><strong>Inspired by Next.js, powered by FastAPI/Flask</strong></p>

  [![PyPI version](https://badge.fury.io/py/reroute.svg)](https://pypi.org/project/reroute/)
  [![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
  [![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/cbsajan/reroute/blob/main/LICENSE)

</div>

---

REROUTE brings the simplicity of file-based routing to Python backend development. Just create files in folders, and they automatically become API endpoints.

## Features

- **File-based Routing**: Folder structure maps directly to URL paths
- **Class-based Routes**: Clean, organized route handlers with lifecycle hooks
- **Multi-framework Support**: Works with FastAPI and Flask (Django coming soon)
- **Parameter Injection**: FastAPI-style parameter extraction (Query, Path, Header, Body, etc.)
- **Pydantic Models**: Generate data validation models with CLI
- **Interactive CLI**: Next.js-style project scaffolding with beautiful prompts
- **Code Generation**: Quickly generate routes, CRUD operations, models, and tests
- **Powerful Decorators**: Rate limiting, caching, validation, and more
- **Security Headers**: OWASP-compliant security headers out of the box (CSP, HSTS, X-Frame-Options)
- **Environment Config**: .env file support with auto-loading
- **API Versioning**: Built-in support for base path prefixes (e.g., `/api/v1`)

## Installation

```bash
# With FastAPI
pip install reroute[fastapi]

# With Flask
pip install reroute[flask]

# Or using uv (faster)
uv pip install reroute[fastapi]
```

## Quick Start

```bash
# Create a new project
reroute init myapi --framework fastapi

# Navigate to project
cd myapi

# Install dependencies
uv sync  # or: pip install -r requirements.txt

# Run the server
python main.py
```

Visit `http://localhost:7376/docs` for interactive API documentation.

## Generate Routes with CLI

```bash
# Generate a new route
reroute create route --path /users --name User --methods GET,POST

# This creates app/routes/users/page.py with:
# - GET endpoint for listing users
# - POST endpoint for creating users
# - Rate limiting and caching decorators
```

## Documentation

**[Complete Documentation](https://cbsajan.github.io/reroute-docs)** - Full guides, API reference, and examples

Quick links:
- [Getting Started](https://cbsajan.github.io/reroute-docs/latest/getting-started/quickstart/) - Installation and first route
- [CLI Commands](https://cbsajan.github.io/reroute-docs/latest/cli/commands/) - Complete CLI reference
- [Decorators](https://cbsajan.github.io/reroute-docs/latest/guides/decorators/) - Rate limiting, caching, validation
- [Security](https://cbsajan.github.io/reroute-docs/latest/guides/security/) - Security headers and best practices
- [API Reference](https://cbsajan.github.io/reroute-docs/latest/api/) - RouteBase, parameters, decorators, config
- [Examples](https://cbsajan.github.io/reroute-docs/latest/examples/) - CRUD, authentication, rate limiting, caching

## How It Works

REROUTE uses your folder structure to create API routes:

```
app/routes/
    users/
        page.py          -> /users
        [id]/
            page.py      -> /users/{id}
    products/
        page.py          -> /products
        categories/
            page.py      -> /products/categories
```

Each `page.py` contains a class with HTTP methods:

```python
from reroute import RouteBase
from reroute.decorators import cache, rate_limit

class UserRoutes(RouteBase):
    tag = "Users"

    @cache(duration=60)
    def get(self):
        """Get all users."""
        return {"users": ["Alice", "Bob"]}

    @rate_limit("10/min")
    def post(self):
        """Create a new user."""
        return {"message": "User created", "id": 1}
```

## Key Concepts

### File-based Routing
Your folder structure is your API structure. No manual route registration needed.

### Class-based Routes
Each route is a Python class with methods for HTTP verbs (get, post, put, delete, etc.).

### Lifecycle Hooks
Routes support `before_request`, `after_request`, and `on_error` hooks for common patterns.

### Decorators
Built-in decorators for rate limiting, caching, validation, and authentication.

### Configuration
Every project has a `config.py` file to customize server settings, routing behavior, and security headers.

### API Versioning
Use `API_BASE_PATH` to prefix all routes (e.g., `/api/v1`).

## Framework Support

| Framework | Status | OpenAPI Docs |
|-----------|--------|--------------|
| FastAPI | Fully Supported | Swagger UI, ReDoc |
| Flask | Fully Supported | Swagger UI, Scalar UI |
| Django | Coming Soon | - |

## License

Apache License 2.0

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

- **Documentation**: [https://cbsajan.github.io/reroute-docs](https://cbsajan.github.io/reroute-docs)
- **Issues**: [GitHub Issues](https://github.com/cbsajan/reroute/issues)
- **PyPI**: [pypi.org/project/reroute](https://pypi.org/project/reroute)

---

<div align="center">
  Built by developers, for developers.
</div>
