# Class-based Routes

Build routes using Python classes with HTTP methods.

## Basic Structure

```python
from reroute import RouteBase

class MyRoutes(RouteBase):
    def get(self):
        """Handle GET requests"""
        return {"message": "GET"}

    def post(self):
        """Handle POST requests"""
        return {"message": "POST"}
```

## HTTP Methods

Supported methods:
- `get()` - GET requests
- `post()` - POST requests
- `put()` - PUT requests
- `delete()` - DELETE requests
- `patch()` - PATCH requests

## Constructor

Initialize state in `__init__`:

```python
class UserRoutes(RouteBase):
    def __init__(self):
        super().__init__()
        self.users = []
```

## Custom Tags

Set Swagger tags:

```python
class UserRoutes(RouteBase):
    tag = "User Management"
```

## Learn More

- [Lifecycle Hooks](lifecycle-hooks.md)
- [Decorators](decorators.md)
