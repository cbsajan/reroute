# Quick Start

Build your first REROUTE application in 5 minutes using CLI commands.

## Step 1: Install REROUTE

=== "pip"

    ```bash
    pip install reroute[fastapi]
    ```

=== "uv (faster)"

    ```bash
    uv pip install reroute[fastapi]
    ```

## Step 2: Initialize Your Project

Use the REROUTE CLI to create your project structure automatically:

<div class="termy">

```console
$ reroute init my-reroute-app --framework fastapi

==================================================
REROUTE Project Initialization
==================================================

? Would you like to generate test cases? Yes
? Would you like to set up a database? No

==================================================
Project Configuration Review
==================================================
  Project Name: my-reroute-app
  Framework: FASTAPI
  Host: 0.0.0.0
  Port: 7376
  Include Tests: Yes
==================================================

? Does this look correct? Yes

Creating project: my-reroute-app

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

  Project: my-reroute-app
  Framework: FASTAPI
  Location: /path/to/my-reroute-app

Next Steps:
  1. cd my-reroute-app
  2. uv venv
  3. uv sync
  4. uv run main.py

Happy Coding!

API Docs: http://localhost:7376/docs
```

</div>

This creates a complete project structure:

```
my-reroute-app/
    app/
        __init__.py
        routes/
            __init__.py
    main.py           # Auto-generated entry point
    pyproject.toml    # Modern dependency management
    .gitignore
```

**Optional:** Install project dependencies:

=== "pip"

    ```bash
    pip install -e .
    ```

=== "uv (faster)"

    ```bash
    uv pip install -e .
    ```

!!! info "Modern Python Packaging"
    REROUTE projects include `pyproject.toml` for modern dependency management. Use `uv` for faster installations.

## Step 3: Generate a Route

Use the CLI to generate your first route:

<div class="termy">

```console
$ reroute create route --path /user --name User --methods GET,POST

  [ OK ] Creating route directory
  [ OK ] Generating route file

==================================================
[SUCCESS] Route created successfully!
==================================================

  Route: /user
  File: app/routes/user/page.py
  Methods: GET, POST
  Tag: User
```

</div>

This creates `app/routes/user/page.py` with GET and POST methods:

```python
from reroute import RouteBase
from reroute.decorators import rate_limit, cache

class UserRoutes(RouteBase):
    """UserRoutes handles /user endpoints."""

    tag = "User"

    def __init__(self):
        super().__init__()
        self.data = []

    @cache(duration=60)
    def get(self):
        """Handle GET requests - retrieve user"""
        return {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ]
        }

    @rate_limit("10/min")
    def post(self):
        """Handle POST requests - create new user"""
        return {"message": "User created", "id": 3}
```

!!! tip "Customize"
    Edit the generated file to customize the response data and add your business logic.

## Step 4: Your Application is Ready

The `reroute init` command already created `main.py` for you:

```python
from fastapi import FastAPI
from reroute.adapters import FastAPIAdapter
from pathlib import Path

app = FastAPI(title="My REROUTE App")

adapter = FastAPIAdapter(
    fastapi_app=app,
    app_dir=Path(__file__).parent / "app"
)
adapter.register_routes()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

No manual setup required. Everything is configured and ready to run.

## Step 5: Run the Application

<div class="termy">

```console
$ python main.py
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

</div>

Visit:

- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Users endpoint**: [http://localhost:8000/user](http://localhost:8000/user)

## Step 6: Test Your API

<div class="termy">

```console
// Get users
$ curl http://localhost:8000/user
{"users":[{"id":1,"name":"Alice"},{"id":2,"name":"Bob"}]}

// Create user
$ curl -X POST http://localhost:8000/user
{"message":"User created","id":3}
```

</div>

## Add More Features

### Rate Limiting

```python
from reroute import RouteBase
from reroute.decorators import rate_limit

class UserRoutes(RouteBase):
    @rate_limit("5/min")  # Limit to 5 requests per minute
    def post(self):
        return {"message": "User created"}
```

### Caching

```python
from reroute import RouteBase
from reroute.decorators import cache

class UserRoutes(RouteBase):
    @cache(duration=60)  # Cache for 60 seconds
    def get(self):
        return {"users": [...]}
```

### Lifecycle Hooks

```python
class UserRoutes(RouteBase):
    def before_request(self):
        print("Authenticating user...")
        return None  # Continue to handler

    def after_request(self, response):
        response["timestamp"] = "2024-01-15T10:30:00Z"
        return response
```

## Next Steps

<div class="grid cards" markdown>

-   **File-based Routing**

    ---

    Learn how folder structure maps to routes.

    [:octicons-arrow-right-24: File Routing](../guides/file-routing.md)

-   **Decorators**

    ---

    Master rate limiting, caching, and more.

    [:octicons-arrow-right-24: Decorators](../guides/decorators.md)

-   **API Reference**

    ---

    Explore all REROUTE features.

    [:octicons-arrow-right-24: API Reference](../api/index.md)

</div>
