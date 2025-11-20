"""
User Detail Routes

Demonstrates:
- Query parameter for user ID (until dynamic path segments are supported)
- Body parameter injection (UserUpdate model)
- Header parameter injection (Authorization)
- Different HTTP methods on the same endpoint
"""

from reroute import RouteBase
from reroute.params import Query, Body, Header
from app.models.user import UserUpdate, UserResponse


# Access the shared users_db from the parent module
def get_users_db():
    """Import users_db from parent module"""
    import sys
    from pathlib import Path
    # Add parent directory to sys.path
    parent_dir = str(Path(__file__).parent.parent)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from page import users_db
    return users_db


class UserDetailRoutes(RouteBase):
    """
    Routes for individual user operations.

    Note: Dynamic path segments (e.g., /users/{id}) will be supported in a future update.
    For now, we use query parameters.
    """

    def get(self,
            id: int = Query(..., description="User ID to retrieve", gt=0)):
        """
        Get user by ID.

        This endpoint demonstrates:
        - Required query parameter (using ...)
        - Parameter validation (gt=0 ensures positive integer)
        """
        users_db = get_users_db()

        # Find user by ID
        user = next((u for u in users_db if u["id"] == id), None)

        if not user:
            return {
                "error": f"User with ID {id} not found",
                "status": 404
            }

        return {"user": user}

    def put(self,
            id: int = Query(..., description="User ID to update", gt=0),
            user: UserUpdate = Body(..., description="User data to update"),
            authorization: str = Header(..., description="Bearer authentication token")):
        """
        Update user by ID.

        This endpoint demonstrates:
        - Combining Query, Body, and Header parameters
        - Optional fields in Pydantic model (UserUpdate has all optional fields)
        - Authentication with headers
        """
        users_db = get_users_db()

        # Validate authorization
        if not authorization.startswith("Bearer "):
            return {
                "error": "Invalid authorization header. Use 'Bearer <token>' format",
                "status": 401
            }

        # Find user by ID
        user_index = next((i for i, u in enumerate(users_db) if u["id"] == id), None)

        if user_index is None:
            return {
                "error": f"User with ID {id} not found",
                "status": 404
            }

        # Update user fields (only update provided fields)
        from datetime import datetime
        update_data = user.dict(exclude_unset=True)
        for field, value in update_data.items():
            users_db[user_index][field] = value

        # Update timestamp
        users_db[user_index]["updated_at"] = datetime.now().isoformat()

        return {
            "message": "User updated successfully",
            "user": users_db[user_index]
        }

    def delete(self,
               id: int = Query(..., description="User ID to delete", gt=0),
               authorization: str = Header(..., description="Bearer authentication token")):
        """
        Delete user by ID.

        This endpoint demonstrates:
        - Destructive operation with authentication
        - Simple parameter validation
        """
        users_db = get_users_db()

        # Validate authorization
        if not authorization.startswith("Bearer "):
            return {
                "error": "Invalid authorization header. Use 'Bearer <token>' format",
                "status": 401
            }

        # Find user by ID
        user_index = next((i for i, u in enumerate(users_db) if u["id"] == id), None)

        if user_index is None:
            return {
                "error": f"User with ID {id} not found",
                "status": 404
            }

        # Remove user
        deleted_user = users_db.pop(user_index)

        return {
            "message": "User deleted successfully",
            "user": deleted_user
        }
