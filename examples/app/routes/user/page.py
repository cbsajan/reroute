"""
User Route Example

Demonstrates REROUTE features:
- Class-based routes
- Decorators (rate_limit, cache)
- Custom Swagger tags
- Lifecycle hooks
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from reroute import RouteBase, rate_limit, cache


class UserRoutes(RouteBase):
    """
    User management routes

    Showcases decorators and lifecycle hooks
    """

    # Custom Swagger tag/category
    tag = "Users"

    def __init__(self):
        super().__init__()
        # Simulate database
        self.users = [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"}
        ]

    def before_request(self):
        """Run before every request"""
        print(f"[UserRoutes] Processing request...")
        # Add authentication checks here
        return None  # Continue to handler

    @cache(duration=30)  # Cache for 30 seconds
    def get(self):
        """Get all users - with caching"""
        return {
            "users": self.users,
            "count": len(self.users),
            "cached": "This response is cached for 30 seconds"
        }

    @rate_limit("5/min")  # Max 5 requests per minute
    def post(self):
        """Create new user - with rate limiting"""
        # In real app, would parse request body
        new_user = {
            "id": len(self.users) + 1,
            "name": "New User",
            "email": "newuser@example.com"
        }
        self.users.append(new_user)

        return {
            "message": "User created",
            "user": new_user,
            "rate_limit": "5 requests per minute"
        }

    def put(self):
        """Update user"""
        return {
            "message": "User updated",
            "note": "In real app, would update from request body"
        }

    @rate_limit("3/min")  # Stricter limit for deletions
    def delete(self):
        """Delete user - with strict rate limiting"""
        if len(self.users) > 0:
            deleted = self.users.pop()
            return {
                "message": "User deleted",
                "user": deleted
            }
        return {"message": "No users to delete"}

    def after_request(self, response):
        """Run after every successful request"""
        response["timestamp"] = "2024-01-15T10:30:00Z"
        response["api_version"] = "v1"
        return response

    def on_error(self, error: Exception):
        """Handle errors"""
        return {
            "error": str(error),
            "type": type(error).__name__,
            "route": "/user"
        }
