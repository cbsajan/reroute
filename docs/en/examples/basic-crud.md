# Basic CRUD Example

Complete example of CRUD operations with REROUTE.

## Route File

`app/routes/user/page.py`:

```python
from reroute import RouteBase
from reroute.decorators import rate_limit, cache

class UserRoutes(RouteBase):
    """User CRUD operations"""

    tag = "Users"

    def __init__(self):
        super().__init__()
        self.users = [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"}
        ]

    @cache(duration=60)
    def get(self):
        """Get all users"""
        return {
            "users": self.users,
            "count": len(self.users)
        }

    @rate_limit("10/min")
    def post(self):
        """Create a new user"""
        new_user = {
            "id": len(self.users) + 1,
            "name": "New User",
            "email": "newuser@example.com"
        }
        self.users.append(new_user)
        return {"created": new_user}

    def put(self):
        """Update a user"""
        if self.users:
            self.users[0]["name"] = "Updated Name"
            return {"updated": self.users[0]}
        return {"error": "No users to update"}

    @rate_limit("5/min")
    def delete(self):
        """Delete a user"""
        if self.users:
            deleted = self.users.pop()
            return {"deleted": deleted}
        return {"error": "No users to delete"}
```

## Main Application

`main.py`:

```python
from fastapi import FastAPI
from reroute.adapters import FastAPIAdapter
from pathlib import Path

app = FastAPI(title="User CRUD API")

adapter = FastAPIAdapter(
    fastapi_app=app,
    app_dir=Path(__file__).parent / "app"
)
adapter.register_routes()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Testing

```bash
# Get all users
curl http://localhost:8000/user

# Create user
curl -X POST http://localhost:8000/user

# Update user
curl -X PUT http://localhost:8000/user

# Delete user
curl -X DELETE http://localhost:8000/user
```

## API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.
