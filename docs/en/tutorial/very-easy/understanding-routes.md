---
difficulty: very easy
time: 10 minutes
prerequisites:
  - link: first-server.md
next: ../easy/dynamic-routes.md
---

# Understanding Routes

Learn how REROUTE's file-based routing system works.

## What You'll Learn

- How file structure maps to URLs
- RouteBase class fundamentals
- HTTP method handlers
- Route organization best practices

## Prerequisites

- Completed [First Server](first-server.md) tutorial
- Basic understanding of URLs and HTTP methods

---

## File-Based Routing Concept

REROUTE uses file-based routing inspired by Next.js. Your folder structure **becomes** your API structure.

```
app/routes/                becomes          API Endpoint
├── page.py               →                /
├── users/
│   ├── page.py           →                /users
│   ├── [id]/
│   │   └── page.py       →                /users/{id}
│   └── profile/
│       └── page.py       →                /users/profile
└── posts/
    ├── page.py           →                /posts
    └── [id]/
        └── page.py       →                /posts/{id}
```

---

## Basic Route Structure

### File Location

Each route is a file named `page.py`:

```
app/routes/
└── hello/
    └── page.py
```

### File Content

```python
from reroute import RouteBase

class HelloRoutes(RouteBase):
    """Route handler for /hello endpoint."""

    def get(self):
        """Handle GET requests."""
        return {"message": "Hello, World!"}

    def post(self):
        """Handle POST requests."""
        return {"message": "Created"}
```

### Result

- File: `app/routes/hello/page.py`
- URL: `http://localhost:7376/hello`
- Methods: GET, POST

---

## HTTP Method Handlers

### Available Methods

```python
class UserRoutes(RouteBase):
    def get(self):
        """GET /users - List all users"""
        return {"users": []}

    def post(self):
        """POST /users - Create a user"""
        return {"id": 1, "created": True}

    def put(self, id: int):
        """PUT /users/{id} - Update a user"""
        return {"id": id, "updated": True}

    def patch(self, id: int):
        """PATCH /users/{id} - Partial update"""
        return {"id": id, "patched": True}

    def delete(self, id: int):
        """DELETE /users/{id} - Delete a user"""
        return {"id": id, "deleted": True}
```

### Method Mapping

| Class Method | HTTP Method | Description |
|--------------|-------------|-------------|
| `get()` | GET | Retrieve data |
| `post()` | POST | Create data |
| `put()` | PUT | Replace data |
| `patch()` | PATCH | Partial update |
| `delete()` | DELETE | Remove data |

---

## Path Parameters

### Dynamic Segments

Use `[param_name]` folder for path parameters:

```
app/routes/
└── users/
    └── [id]/
        └── page.py
```

**Handler:**

```python
class UserDetailRoutes(RouteBase):
    def get(self, id: int):
        """GET /users/{id}"""
        return {"user_id": id}
```

**Result:**
- URL: `/users/123`
- `id` parameter: `123`

---

## Root Routes

### app/root.py

Special file for root and health endpoints:

```python
from fastapi import Request
from reroute import RouteBase

class RootRoutes(RouteBase):
    def get(self, request: Request):
        """GET / - Root endpoint"""
        return {
            "message": "Welcome",
            "docs": "/docs",
            "health": "/health"
        }

def health():
    """GET /health - Health check"""
    return {"status": "healthy"}
```

**Why separate?**
- Root endpoint doesn't follow `/routes/` pattern
- Health checks are infrastructure-related
- Keeps application routes clean

---

## Route Organization

### Feature-Based Organization

```
app/routes/
├── users/
│   ├── page.py           # /users
│   ├── [id]/
│   │   └── page.py       # /users/{id}
│   └── profile/
│       └── page.py       # /users/profile
├── posts/
│   ├── page.py           # /posts
│   └── [id]/
│       └── page.py       # /posts/{id}
└── comments/
    └── page.py           # /comments
```

**Advantages:**
- Easy to find related routes
- Clear resource hierarchy
- Scalable structure

---

## Common Patterns

### CRUD Routes

```
app/routes/
├── users/
│   ├── page.py           # List & Create
│   └── [id]/
│       └── page.py       # Get, Update, Delete
```

**users/page.py:**
```python
class UserRoutes(RouteBase):
    def get(self):
        """List all users"""
        return {"users": []}

    def post(self):
        """Create a user"""
        return {"id": 1}
```

**users/[id]/page.py:**
```python
class UserDetailRoutes(RouteBase):
    def get(self, id: int):
        """Get user by ID"""
        return {"id": id}

    def put(self, id: int):
        """Update user"""
        return {"id": id, "updated": True}

    def delete(self, id: int):
        """Delete user"""
        return {"id": id, "deleted": True}
```

---

## Lifecycle Hooks

RouteBase supports lifecycle hooks:

```python
class UserRoutes(RouteBase):
    def before_request(self):
        """Run before every request"""
        print("Processing user request")

    def after_request(self, response):
        """Run after every request"""
        print("Request processed")
        return response

    def on_error(self, error):
        """Handle errors"""
        return {"error": str(error)}, 500

    def get(self):
        return {"users": []}
```

---

## Troubleshooting

### Route Not Found (404)

**Check:**
1. File is named `page.py` (not `route.py`)
2. Class inherits from `RouteBase`
3. File is in `app/routes/` directory
4. Server has been restarted

### Path Parameter Not Working

**Check:**
1. Folder name is `[param_name]` with brackets
2. Method signature includes parameter: `def get(self, id: int)`
3. Parameter name matches folder name

### Wrong HTTP Method

**Check:**
1. Method is defined in class (get, post, etc.)
2. Using correct HTTP method in request
3. Method name is lowercase

---

## Next Steps

Now you understand how routing works!

**What's next:**
- [Dynamic Routes](../easy/dynamic-routes.md) - Deep dive into path parameters
- [HTTP Methods](../easy/http-methods.md) - Handle different request types

---

## Summary

You learned:
- File structure maps to URL structure
- `page.py` files become routes
- `RouteBase` class with HTTP method handlers
- Path parameters using `[param]` folders
- Route organization best practices

**Key takeaways:**
- Your folder structure is your API structure
- Use `page.py` for route files
- Class methods handle HTTP methods
- Path parameters use `[param]` folder syntax

Ready to dive deeper? Continue to [Dynamic Routes](../easy/dynamic-routes.md)!
