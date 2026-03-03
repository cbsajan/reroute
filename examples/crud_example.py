# CRUD API Route Example
# Copy to: test_app/routes/api/users/page.py

from reroute import RouteBase, Query, Body, Param
from typing import Optional, List
from pydantic import BaseModel, Field


# Request/Response Models
class UserCreate(BaseModel):
    """User creation request model."""
    name: str = Field(..., description="User name", min_length=1)
    email: str = Field(..., description="User email")
    age: Optional[int] = Field(None, description="User age")


class UserUpdate(BaseModel):
    """User update request model."""
    name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None


class UserResponse(BaseModel):
    """User response model."""
    id: str
    name: str
    email: str
    age: Optional[int] = None


# In-memory storage (replace with actual database)
_users_db: Dict[str, dict] = {
    "1": {"id": "1", "name": "Alice", "email": "alice@example.com", "age": 30},
    "2": {"id": "2", "name": "Bob", "email": "bob@example.com", "age": 25},
}
_user_id_counter = 3


class UsersRoute(RouteBase):
    """CRUD operations for users."""

    tag = "Users"
    summary = "User management API"

    def get(self, limit: int = Query(10, description="Max users to return"), skip: int = Query(0)) -> List[UserResponse]:
        """List all users with pagination."""
        users = list(_users_db.values())
        users = users[skip:skip + limit]
        return [UserResponse(**user) for user in users]

    def post(self, user: UserCreate = Body(...)) -> UserResponse:
        """Create a new user."""
        global _user_id_counter

        user_id = str(_user_id_counter)
        _user_id_counter += 1

        new_user = {
            "id": user_id,
            "name": user.name,
            "email": user.email,
            "age": user.age
        }
        _users_db[user_id] = new_user

        return UserResponse(**new_user)


class UserDetailRoute(RouteBase):
    """Individual user operations."""

    tag = "Users"

    def get(self, id: str = Param(..., description="User ID")) -> UserResponse:
        """Get user by ID."""
        if id not in _users_db:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse(**_users_db[id])

    def put(self, id: str, user: UserUpdate) -> UserResponse:
        """Update user by ID."""
        if id not in _users_db:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="User not found")

        existing = _users_db[id]
        update_data = user.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if value is not None:
                existing[field] = value

        return UserResponse(**existing)

    def delete(self, id: str) -> dict:
        """Delete user by ID."""
        if id not in _users_db:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="User not found")

        del _users_db[id]
        return {"message": "User deleted", "id": id}
