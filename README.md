# REROUTE

**File-based routing for Python backends** - Inspired by Next.js, powered by FastAPI/Flask

REROUTE brings the simplicity of file-based routing to Python backend development. Just create files in folders, and they automatically become API endpoints.

## Features

- **File-based Routing**: Folder structure maps directly to URL paths
- **Class-based Routes**: Clean, organized route handlers with lifecycle hooks
- **Parameter Injection**: FastAPI-style parameter extraction (Query, Path, Header, Body, etc.)
- **Pydantic Models**: Generate data validation models with CLI
- **Framework Adapters**: Works with FastAPI (Flask, Django support coming)
- **Interactive CLI**: Next.js-style project scaffolding with beautiful prompts
- **Code Generation**: Quickly generate routes, CRUD operations, models, and tests
- **Environment Config**: .env file support with auto-loading
- **Powerful Decorators**: Rate limiting, caching, validation, and more
- **API Versioning**: Built-in support for base path prefixes (e.g., `/api/v1`)

## Installation

```bash
pip install reroute
```

## Quick Start

```bash
# Create a new project
reroute init myapi

# Navigate to project
cd myapi

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

Visit `http://localhost:7376/docs` for interactive API documentation.

## Documentation

📚 **[Complete Documentation](https://cbsajan.github.io/reroute-docs)** - Full guides, API reference, and examples

Quick links:
- [Getting Started](https://cbsajan.github.io/reroute-docs/getting-started/) - Installation and first route
- [CLI Commands](https://cbsajan.github.io/reroute-docs/cli/commands/) - Complete CLI reference
- [API Reference](https://cbsajan.github.io/reroute-docs/api/) - RouteBase, parameters, decorators, config
- [Examples](https://cbsajan.github.io/reroute-docs/examples/) - CRUD, authentication, rate limiting, caching
- [Contributing](CONTRIBUTING.md) - How to contribute to REROUTE

## How It Works

REROUTE uses your folder structure to create API routes. Each folder becomes a URL path, and each `page.py` file defines the route handlers.

```
app/routes/hello/page.py → /hello
app/routes/users/page.py → /users
app/routes/posts/page.py → /posts
```

**API Versioning with Base Path:**
Instead of creating nested folders, use `API_BASE_PATH` in config:

```python
# config.py
API_BASE_PATH = "/api/v1"
```

Now your routes are automatically prefixed:
```
app/routes/users/page.py → /api/v1/users
app/routes/posts/page.py → /api/v1/posts
```

## Key Concepts

### File-based Routing
Your folder structure is your API structure. No manual route registration needed.

### Class-based Routes
Each route is a Python class with methods for HTTP verbs (get, post, put, delete, etc.).

### Lifecycle Hooks
Routes support `before_request`, `after_request`, and `on_error` hooks for common patterns.

### Configuration
Every project has a `config.py` file to customize server settings, routing behavior, and more.

### API Versioning
Use `API_BASE_PATH` to prefix all routes (e.g., `/api/v1`).

## Framework Support

- **FastAPI** - Fully supported with OpenAPI docs
- **Flask** - Coming soon

## License

Apache License 2.0

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

- **Documentation**: [https://cbsajan.github.io/reroute-docs](https://cbsajan.github.io/reroute-docs)
- **Issues**: [GitHub Issues](https://github.com/cbsajan/reroute/issues)
- **PyPI**: [pypi.org/project/reroute](https://pypi.org/project/reroute)

---

Built with by developers, for developers.
