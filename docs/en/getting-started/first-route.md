# Your First Route

Let's create your first file-based route with REROUTE.

## Understanding File-based Routing

In REROUTE, the folder structure determines your API routes:

```
app/routes/
└── user/
    └── page.py  → /user endpoint
```

The `page.py` file contains the route logic as a class.

## Creating a Simple Route

### 1. Create the File Structure

```bash
mkdir -p app/routes/hello
```

### 2. Create the Route Handler

Create `app/routes/hello/page.py`:

```python
from reroute import RouteBase

class HelloRoutes(RouteBase):
    """Simple hello world route"""

    def get(self):
        """Handle GET requests"""
        return {"message": "Hello, REROUTE!"}
```

### 3. Register with Your App

In your `main.py`:

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

### 4. Test It

```bash
curl http://localhost:8000/hello
# {"message": "Hello, REROUTE!"}
```

## Adding Multiple HTTP Methods

Handle different HTTP methods with corresponding class methods:

```python
from reroute import RouteBase

class TodoRoutes(RouteBase):
    """Todo management routes"""

    tag = "Todos"

    def __init__(self):
        super().__init__()
        self.todos = []

    def get(self):
        """Get all todos"""
        return {"todos": self.todos}

    def post(self):
        """Create a todo"""
        todo = {"id": len(self.todos) + 1, "title": "New Todo"}
        self.todos.append(todo)
        return {"created": todo}

    def put(self):
        """Update a todo"""
        return {"message": "Todo updated"}

    def delete(self):
        """Delete a todo"""
        if self.todos:
            deleted = self.todos.pop()
            return {"deleted": deleted}
        return {"message": "No todos to delete"}
```

## Adding Custom Swagger Tags

Organize your API documentation with custom tags:

```python
class UserRoutes(RouteBase):
    tag = "User Management"  # Shows in Swagger UI

    def get(self):
        return {"users": []}
```

## Using State

Store state in your route class:

```python
class CounterRoutes(RouteBase):
    """Simple counter API"""

    def __init__(self):
        super().__init__()
        self.count = 0

    def get(self):
        """Get current count"""
        return {"count": self.count}

    def post(self):
        """Increment count"""
        self.count += 1
        return {"count": self.count}
```

## Route Method Signatures

Each HTTP method can accept different parameters based on your framework:

=== "FastAPI"

    ```python
    from fastapi import Request, Response

    class MyRoutes(RouteBase):
        def get(self, request: Request):
            return {"ip": request.client.host}

        async def post(self, request: Request):
            body = await request.json()
            return {"received": body}
    ```

=== "Flask"

    ```python
    from flask import request

    class MyRoutes(RouteBase):
        def get(self):
            return {"ip": request.remote_addr}

        def post(self):
            body = request.get_json()
            return {"received": body}
    ```

## Next Steps

<div class="grid cards" markdown>

-   :material-file-tree: [**File-based Routing**](../guides/file-routing.md)

    ---

    Learn nested routes and dynamic segments

-   :material-alpha-d-box: [**Decorators**](../guides/decorators.md)

    ---

    Add rate limiting, caching, and validation

-   :material-cog: [**Lifecycle Hooks**](../guides/lifecycle-hooks.md)

    ---

    Control request/response flow

</div>
