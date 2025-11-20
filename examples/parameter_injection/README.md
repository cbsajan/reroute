# Parameter Injection Example

This example demonstrates REROUTE's FastAPI-style parameter injection system.

## Features Demonstrated

- **Query Parameters**: Filtering, pagination, sorting
- **Path Parameters**: Resource IDs from URL paths
- **Body Parameters**: Request body validation with Pydantic models
- **Header Parameters**: Authentication and custom headers
- **Cookie Parameters**: Session management
- **Form Parameters**: Form data handling

## Project Structure

```
parameter_injection/
├── app/
│   ├── models/
│   │   └── user.py          # Pydantic models for User
│   └── routes/
│       ├── users/
│       │   └── page.py       # User list and create
│       └── users/[id]/
│           └── page.py       # User detail, update, delete
├── main.py                   # FastAPI app with REROUTE
└── test.http                 # HTTP test file
```

## Setup

1. Install dependencies:
```bash
pip install reroute fastapi uvicorn pydantic
```

2. Run the server:
```bash
python main.py
```

3. Test the API:
- Open http://localhost:7376/docs for Swagger UI
- Use the `test.http` file for quick testing

## API Endpoints

### GET /users
List users with pagination and filtering.

**Query Parameters:**
- `limit` (int): Maximum number of results (default: 10)
- `offset` (int): Number of results to skip (default: 0)
- `search` (str, optional): Search term for filtering
- `sort_by` (str, optional): Field to sort by

**Example:**
```
GET /users?limit=20&offset=0&search=john&sort_by=name
```

### POST /users
Create a new user.

**Body:** UserCreate model (JSON)
**Headers:**
- `Authorization`: Bearer token (required)

**Example:**
```json
{
  "name": "John Doe",
  "description": "Software Engineer",
  "is_active": true
}
```

### GET /users/{id}
Get user by ID.

**Path Parameters:**
- `id` (int): User ID

**Example:**
```
GET /users/123
```

### PUT /users/{id}
Update user by ID.

**Path Parameters:**
- `id` (int): User ID

**Body:** UserUpdate model (JSON)
**Headers:**
- `Authorization`: Bearer token (required)

### DELETE /users/{id}
Delete user by ID.

**Path Parameters:**
- `id` (int): User ID

**Headers:**
- `Authorization`: Bearer token (required)

## Key Concepts

### Parameter Injection

Parameters are automatically extracted and validated from the request:

```python
from reroute import RouteBase
from reroute.params import Query, Path, Body, Header

class UsersRoutes(RouteBase):
    def get(self,
            limit: int = Query(10, description="Maximum results"),
            offset: int = Query(0, description="Skip results"),
            search: str = Query(None, description="Search term")):
        return {"limit": limit, "offset": offset, "search": search}
```

### Pydantic Models

Models provide automatic validation and documentation:

```python
from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    name: str = Field(..., description="User name")
    email: EmailStr = Field(..., description="Email address")
```

### Type Safety

REROUTE provides full type safety with parameter extraction:
- Required parameters: `Query(...)`
- Optional parameters: `Query(None)` or `Query(default_value)`
- Type coercion: Automatic conversion to annotated types
- Validation: Pydantic validators for complex rules

## Learn More

- [Parameter Injection Docs](../../docs/api/params.md)
- [Models Guide](../../docs/guides/models.md)
- [Route Handlers](../../docs/guides/routes.md)
