"""
User List and Create Routes

Demonstrates:
- Query parameter injection (limit, offset, search, sort_by)
- Body parameter injection (UserCreate model)
- Header parameter injection (Authorization)
"""

from reroute import RouteBase
from reroute.params import Query, Body, Header
from app.models.user import UserCreate, UserResponse
from typing import List


# In-memory database for demo purposes
users_db = [
    {"id": 1, "name": "Alice Smith", "description": "Software Engineer", "is_active": True,
     "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00"},
    {"id": 2, "name": "Bob Johnson", "description": "Product Manager", "is_active": True,
     "created_at": "2024-01-02T00:00:00", "updated_at": "2024-01-02T00:00:00"},
    {"id": 3, "name": "Charlie Brown", "description": "Designer", "is_active": False,
     "created_at": "2024-01-03T00:00:00", "updated_at": "2024-01-03T00:00:00"},
]
next_id = 4


class UsersRoutes(RouteBase):
    """
    Routes for user list and creation operations.
    """

    def get(self,
            limit: int = Query(10, description="Maximum number of results to return", ge=1, le=100),
            offset: int = Query(0, description="Number of results to skip for pagination", ge=0),
            search: str = Query(None, description="Search term to filter users by name"),
            sort_by: str = Query("id", description="Field to sort by (id, name, created_at)"),
            is_active: bool = Query(None, description="Filter by active status")):
        """
        List users with pagination and filtering.

        This endpoint demonstrates:
        - Query parameter injection with defaults
        - Parameter validation (ge, le for numeric constraints)
        - Optional parameters (search can be None)
        - Multiple query parameters
        """
        # Filter users
        filtered_users = users_db

        # Apply search filter
        if search:
            filtered_users = [
                user for user in filtered_users
                if search.lower() in user["name"].lower() or
                   (user["description"] and search.lower() in user["description"].lower())
            ]

        # Apply is_active filter
        if is_active is not None:
            filtered_users = [user for user in filtered_users if user["is_active"] == is_active]

        # Sort users
        if sort_by in ["id", "name", "created_at"]:
            filtered_users = sorted(filtered_users, key=lambda x: x[sort_by])

        # Apply pagination
        paginated_users = filtered_users[offset:offset + limit]

        return {
            "total": len(filtered_users),
            "limit": limit,
            "offset": offset,
            "users": paginated_users
        }

    def post(self,
             user: UserCreate = Body(..., description="User data to create"),
             authorization: str = Header(..., description="Bearer authentication token")):
        """
        Create a new user.

        This endpoint demonstrates:
        - Body parameter injection with Pydantic model
        - Automatic JSON validation and parsing
        - Header parameter injection for authentication
        - Required parameters (using ...)
        """
        global next_id

        # Validate authorization header (simple check for demo)
        if not authorization.startswith("Bearer "):
            return {
                "error": "Invalid authorization header. Use 'Bearer <token>' format",
                "status": 401
            }

        # Create new user (in production, this would insert into a database)
        from datetime import datetime
        new_user = {
            "id": next_id,
            **user.dict(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        users_db.append(new_user)
        next_id += 1

        return {
            "message": "User created successfully",
            "user": new_user
        }
