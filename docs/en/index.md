# REROUTE

<div class="hero-section" markdown>

<img src="assets/logo-dark.svg" alt="REROUTE Logo" class="hero-logo">

**File-based routing for Python backends**

<div class="badges" markdown>

[![PyPI version](https://badge.fury.io/py/reroute.svg)](https://pypi.org/project/reroute/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/cbsajan/reroute/blob/main/LICENSE)

</div>

</div>

---

REROUTE brings the simplicity and elegance of Next.js-style file-based routing to Python web frameworks. Build clean, maintainable APIs with zero configuration.

---

## Features

<div class="grid cards" markdown>

-   **File-based Routing**

    ---

    Organize routes by folders and files, just like Next.js. No manual route registration needed. Your folder structure becomes your API structure.

    [:octicons-arrow-right-24: Learn more](guides/file-routing.md)

-   **Class-based Handlers**

    ---

    HTTP methods as class methods: `get()`, `post()`, `put()`, `delete()`. Clean, intuitive, and Pythonic approach to API development.

    [:octicons-arrow-right-24: Learn more](guides/class-routes.md)

-   **Powerful Decorators**

    ---

    Built-in rate limiting, caching, validation, and authentication. Extend functionality with custom decorators easily.

    [:octicons-arrow-right-24: Learn more](guides/decorators.md)

-   **Multi-framework Support**

    ---

    Works with FastAPI and Flask. Django coming soon. Switch frameworks without rewriting your route logic.

    [:octicons-arrow-right-24: Adapters](adapters/index.md)

-   **Security Headers**

    ---

    OWASP-compliant security headers out of the box. CSP, HSTS, X-Frame-Options, and more - configured automatically.

    [:octicons-arrow-right-24: Security](guides/security.md)

-   **CLI Scaffolding**

    ---

    Generate projects, routes, and models with CLI commands. `reroute init` and `reroute create` for rapid development.

    [:octicons-arrow-right-24: CLI](cli/index.md)

</div>

---

## Quick Start

### Requirements

- Python 3.8+
- FastAPI or Flask

### Installation

=== "pip"

    ```bash
    pip install reroute[fastapi]
    ```

=== "uv (faster)"

    ```bash
    uv pip install reroute[fastapi]
    ```

### Create a Project

<div class="termy">

```console
$ reroute init my-app --framework fastapi

==================================================
REROUTE Project Initialization
==================================================

? Would you like to generate test cases? Yes
? Would you like to set up a database? No

==================================================
Project Configuration Review
==================================================
  Project Name: my-app
  Framework: FASTAPI
  Host: 0.0.0.0
  Port: 7376
  Include Tests: Yes
==================================================

? Does this look correct? Yes

Creating project: my-app

  [ OK ] Creating project structure
  [ OK ] Creating config.py
  [ OK ] Creating logger.py
  [ OK ] Generating FASTAPI application
  [ OK ] Creating example route
  [ OK ] Creating root and health routes
  [ OK ] Creating test cases
  [ OK ] Creating .env.example
  [ OK ] Creating requirements.txt
  [ OK ] Creating pyproject.toml

==================================================
[SUCCESS] Project created successfully!
==================================================

  Project: my-app
  Framework: FASTAPI
  Location: /path/to/my-app

Next Steps:
  1. cd my-app
  2. uv venv
  3. uv sync
  4. uv run main.py

Happy Coding!

API Docs: http://localhost:7376/docs
```

</div>

### Generate a Route

<div class="termy">

```console
$ reroute create route --path /users --name User --methods GET,POST

  [ OK ] Creating route directory
  [ OK ] Generating route file

==================================================
[SUCCESS] Route created successfully!
==================================================

  Route: /users
  File: app/routes/users/page.py
  Methods: GET, POST
  Tag: User
```

</div>

This creates `app/routes/users/page.py`:

```python
from reroute import RouteBase
from reroute.decorators import cache, rate_limit

class UserRoutes(RouteBase):
    """User API endpoints."""

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

### Run the Application

```bash
python main.py
```

Visit:

- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Users Endpoint**: [http://localhost:8000/users](http://localhost:8000/users)

---

## How It Works

Your folder structure becomes your API routes:

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

Each `page.py` contains a class inheriting from `RouteBase` with HTTP methods:

```python
from reroute import RouteBase

class UserRoutes(RouteBase):
    def get(self):
        """Handle GET requests."""
        return {"users": [...]}

    def post(self):
        """Handle POST requests."""
        return {"message": "Created"}

    def put(self, id: int):
        """Handle PUT requests."""
        return {"message": f"Updated {id}"}

    def delete(self, id: int):
        """Handle DELETE requests."""
        return {"message": f"Deleted {id}"}
```

---

## What's Next?

<div class="grid cards" markdown>

-   **Quick Start**

    ---

    Get up and running in 5 minutes with the full tutorial.

    [:octicons-arrow-right-24: Quick Start](getting-started/quickstart.md)

-   **User Guide**

    ---

    Deep dives into routing, decorators, lifecycle hooks, and more.

    [:octicons-arrow-right-24: Guides](guides/index.md)

-   **API Reference**

    ---

    Complete API documentation for all REROUTE features.

    [:octicons-arrow-right-24: API Reference](api/index.md)

-   **Examples**

    ---

    Real-world patterns: CRUD, authentication, caching, and more.

    [:octicons-arrow-right-24: Examples](examples/index.md)

</div>

---

## Community & Support

- **GitHub**: [github.com/cbsajan/reroute](https://github.com/cbsajan/reroute)
- **PyPI**: [pypi.org/project/reroute](https://pypi.org/project/reroute)
- **Issues**: [Report bugs or request features](https://github.com/cbsajan/reroute/issues)
- **Contributing**: [Contributing Guide](contributing.md)

---

## License

REROUTE is released under the [Apache License 2.0](https://github.com/cbsajan/reroute/blob/main/LICENSE).
