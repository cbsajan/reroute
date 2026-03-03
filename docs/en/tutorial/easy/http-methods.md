---
difficulty: easy
time: 20 minutes
prerequisites:
  - link: ../../start-here.md
  - link: ../very-easy/hello-world.md
  - link: ../very-easy/understanding-routes.md
  - link: dynamic-routes.md
next: query-params.md
---

# HTTP Methods

Learn how to handle different HTTP methods (GET, POST, PUT, DELETE, PATCH) to build full CRUD operations in your API.

## What You'll Learn

- When to use each HTTP method
- Working with request bodies
- Proper HTTP status codes
- Building CRUD operations
- POST vs PUT vs PATCH differences

## Prerequisites

- Completed [Dynamic Routes](dynamic-routes.md) tutorial
- Understanding of REST API concepts
- Working REROUTE project

---

## HTTP Methods Overview

HTTP methods (also called verbs) indicate the action you want to perform on a resource:

| Method | Purpose | Example | Idempotent | Safe |
|--------|---------|---------|------------|------|
| **GET** | Retrieve data | `GET /users` | Yes | Yes |
| **POST** | Create new resource | `POST /users` | No | No |
| **PUT** | Update entire resource | `PUT /users/1` | Yes | No |
| **PATCH** | Partial update | `PATCH /users/1` | No | No |
| **DELETE** | Remove resource | `DELETE /users/1` | Yes | No |

**Key terms:**
- **Safe**: Doesn't modify server state (GET only)
- **Idempotent**: Same result regardless of how many times executed (GET, PUT, DELETE)

---

## Step 1: Create a Complete CRUD Route

Let's build a complete todo items API with all HTTP methods:

```bash
reroute create route --path /todos --name TodoRoutes --methods GET,POST,PUT,PATCH,DELETE
```

This creates: `app/routes/todos/page.py`

---

## Step 2: Implement GET (Retrieve Data)

GET is used to fetch data without modifying anything.

Edit `app/routes/todos/page.py`:

```python
from typing import List, Dict, Optional
from reroute import RouteBase
from reroute.params import Query
from fastapi import HTTPException

# In-memory storage (use database in production)
todos_db: List[Dict] = [
    {"id": 1, "title": "Learn REROUTE", "completed": False},
    {"id": 2, "title": "Build an API", "completed": True},
    {"id": 3, "title": "Deploy to production", "completed": False}
]
next_id = 4

class TodoRoutes(RouteBase):
    """Todo items management endpoints."""

    def get(
        self,
        todo_id: Optional[int] = Query(None, description="Todo ID"),
        completed: Optional[bool] = Query(None, description="Filter by completion status")
    ):
        """
        Get todos (list or specific item).

        - **todo_id**: If provided, returns specific todo
        - **completed**: If provided, filters by completion status
        """
        # Get specific todo
        if todo_id is not None:
            todo = next((t for t in todos_db if t["id"] == todo_id), None)
            if not todo:
                raise HTTPException(
                    status_code=404,
                    detail=f"Todo {todo_id} not found"
                )
            return todo

        # List all todos with optional filter
        result = todos_db
        if completed is not None:
            result = [t for t in todos_db if t["completed"] == completed]

        return {
            "total": len(result),
            "todos": result
        }
```

### Test GET Requests

**List all todos:**
```bash
curl http://localhost:7376/todos
```

**Expected Output:**
```json
{
  "total": 3,
  "todos": [
    {"id": 1, "title": "Learn REROUTE", "completed": false},
    {"id": 2, "title": "Build an API", "completed": true},
    {"id": 3, "title": "Deploy to production", "completed": false}
  ]
}
```

**Get specific todo:**
```bash
curl http://localhost:7376/todos?todo_id=1
```

**Expected Output:**
```json
{
  "id": 1,
  "title": "Learn REROUTE",
  "completed": false
}
```

**Filter completed todos:**
```bash
curl "http://localhost:7376/todos?completed=true"
```

`★ Insight ─────────────────────────────────────`
**Query Parameters vs Path Parameters**: In this tutorial, we're using query parameters (`?todo_id=1`) instead of path parameters (`/todos/1`) for the GET method. This is a common pattern when you want one endpoint that can handle both listing and fetching. Later you'll learn to combine both approaches for cleaner APIs.
`─────────────────────────────────────────────────`

---

## Step 3: Implement POST (Create Resource)

POST is used to create new resources. It's **not idempotent** - calling it multiple times creates multiple resources.

Add to `app/routes/todos/page.py`:

```python
from reroute.params import Body
from pydantic import BaseModel, Field

# Pydantic models for validation
class TodoCreate(BaseModel):
    """Schema for creating a new todo."""
    title: str = Field(..., min_length=1, max_length=200)
    completed: bool = Field(default=False)

class TodoUpdate(BaseModel):
    """Schema for updating a todo."""
    title: str = Field(None, min_length=1, max_length=200)
    completed: bool = None

class TodoRoutes(RouteBase):
    # ... (previous get method)

    def post(self, todo: TodoCreate = Body(...)):
        """
        Create a new todo.

        - **title**: Todo title (required, 1-200 characters)
        - **completed**: Completion status (default: false)
        """
        global next_id

        # Create new todo
        new_todo = {
            "id": next_id,
            "title": todo.title,
            "completed": todo.completed
        }
        todos_db.append(new_todo)
        next_id += 1

        # Return 201 Created with new resource
        return new_todo
```

### Test POST Request

**Create a new todo:**
```bash
curl -X POST http://localhost:7376/todos \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Write documentation",
    "completed": false
  }'
```

**Expected Output:** (Status: 200 OK, ideally 201 Created)
```json
{
  "id": 4,
  "title": "Write documentation",
  "completed": false
}
```

**Test validation (missing title):**
```bash
curl -X POST http://localhost:7376/todos \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected Output:** (422 Unprocessable Entity)
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "title"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

**Test validation (title too long):**
```bash
curl -X POST http://localhost:7376/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "This title is way way way too long and exceeds the maximum limit"}'
```

**Expected Output:** (422 Unprocessable Entity)
```json
{
  "detail": [
    {
      "type": "string_too_long",
      "loc": ["body", "title"],
      "msg": "String should have at most 200 characters",
      "input": "..."
    }
  ]
}
```

---

## Step 4: Implement PUT (Complete Update)

PUT replaces the **entire** resource. It's **idempotent** - calling it multiple times with same data has same effect.

Add to `app/routes/todos/page.py`:

```python
class TodoRoutes(RouteBase):
    # ... (previous get and post methods)

    def put(
        self,
        todo_id: int = Query(..., gt=0, description="Todo ID to update"),
        todo: TodoCreate = Body(...)
    ):
        """
        Completely replace a todo.

        - **todo_id**: ID of todo to replace
        - **title**: New title (required)
        - **completed**: New completion status (required)

        Note: This replaces ALL fields. Use PATCH for partial updates.
        """
        # Find todo
        todo_idx = next(
            (i for i, t in enumerate(todos_db) if t["id"] == todo_id),
            None
        )

        if todo_idx is None:
            raise HTTPException(
                status_code=404,
                detail=f"Todo {todo_id} not found"
            )

        # Replace entire todo
        todos_db[todo_idx] = {
            "id": todo_id,
            "title": todo.title,
            "completed": todo.completed
        }

        return todos_db[todo_idx]
```

### Test PUT Request

**Replace entire todo:**
```bash
curl -X PUT "http://localhost:7376/todos?todo_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Learn REROUTE (Updated)",
    "completed": true
  }'
```

**Expected Output:**
```json
{
  "id": 1,
  "title": "Learn REROUTE (Updated)",
  "completed": true
}
```

**Verify replacement:**
```bash
curl http://localhost:7376/todos?todo_id=1
```

All fields should be updated. Old data is completely replaced.

---

## Step 5: Implement PATCH (Partial Update)

PATCH updates **specific fields** of a resource without replacing everything.

Add to `app/routes/todos/page.py`:

```python
class TodoRoutes(RouteBase):
    # ... (previous get, post, and put methods)

    def patch(
        self,
        todo_id: int = Query(..., gt=0, description="Todo ID to update"),
        todo: TodoUpdate = Body(...)
    ):
        """
        Partially update a todo.

        - **todo_id**: ID of todo to update
        - **title**: New title (optional)
        - **completed**: New completion status (optional)

        Only provided fields are updated.
        """
        # Find todo
        todo_idx = next(
            (i for i, t in enumerate(todos_db) if t["id"] == todo_id),
            None
        )

        if todo_idx is None:
            raise HTTPException(
                status_code=404,
                detail=f"Todo {todo_id} not found"
            )

        # Update only provided fields
        if todo.title is not None:
            todos_db[todo_idx]["title"] = todo.title
        if todo.completed is not None:
            todos_db[todo_idx]["completed"] = todo.completed

        return todos_db[todo_idx]
```

### Test PATCH Request

**Update only completion status:**
```bash
curl -X PATCH "http://localhost:7376/todos?todo_id=2" \
  -H "Content-Type: application/json" \
  -d '{
    "completed": false
  }'
```

**Expected Output:**
```json
{
  "id": 2,
  "title": "Build an API",
  "completed": false
}
```

Notice that `title` remains unchanged - only `completed` was updated.

**Update only title:**
```bash
curl -X PATCH "http://localhost:7376/todos?todo_id=3" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Deploy to production servers"
  }'
```

**Expected Output:**
```json
{
  "id": 3,
  "title": "Deploy to production servers",
  "completed": false
}
```

Now `completed` stays false, only `title` changed.

`★ Insight ─────────────────────────────────────`
**PUT vs PATCH**: Use PUT when you need to replace entire resources (clearing old data). Use PATCH for partial updates (modifying specific fields). PUT is idempotent (same result each time), PATCH might not be (if toggling boolean values). Choose based on your use case!
`─────────────────────────────────────────────────`

---

## Step 6: Implement DELETE (Remove Resource)

DELETE removes a resource. It's **idempotent** - deleting something twice has same result as deleting once (resource is gone).

Add to `app/routes/todos/page.py`:

```python
class TodoRoutes(RouteBase):
    # ... (all previous methods)

    def delete(self, todo_id: int = Query(..., gt=0, description="Todo ID to delete")):
        """
        Delete a todo.

        - **todo_id**: ID of todo to delete

        Returns the deleted todo for confirmation.
        """
        # Find todo
        todo_idx = next(
            (i for i, t in enumerate(todos_db) if t["id"] == todo_id),
            None
        )

        if todo_idx is None:
            raise HTTPException(
                status_code=404,
                detail=f"Todo {todo_id} not found"
            )

        # Remove and return deleted todo
        deleted_todo = todos_db.pop(todo_idx)

        return {
            "message": "Todo deleted successfully",
            "deleted": deleted_todo
        }
```

### Test DELETE Request

**Delete a todo:**
```bash
curl -X DELETE "http://localhost:7376/todos?todo_id=1"
```

**Expected Output:**
```json
{
  "message": "Todo deleted successfully",
  "deleted": {
    "id": 1,
    "title": "Learn REROUTE (Updated)",
    "completed": true
  }
}
```

**Verify deletion:**
```bash
curl http://localhost:7376/todos?todo_id=1
```

**Expected Output:** (404 Not Found)
```json
{
  "detail": "Todo 1 not found"
}
```

**Idempotency test - delete again:**
```bash
curl -X DELETE "http://localhost:7376/todos?todo_id=1"
```

Same 404 error - idempotent behavior!

---

## Complete TodoRoutes Example

Here's the complete implementation with all methods:

```python
from typing import List, Dict, Optional
from reroute import RouteBase
from reroute.params import Query, Body
from fastapi import HTTPException
from pydantic import BaseModel, Field

# Pydantic models
class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    completed: bool = Field(default=False)

class TodoUpdate(BaseModel):
    title: str = Field(None, min_length=1, max_length=200)
    completed: bool = None

# In-memory storage
todos_db: List[Dict] = [
    {"id": 1, "title": "Learn REROUTE", "completed": False},
    {"id": 2, "title": "Build an API", "completed": True},
]
next_id = 3

class TodoRoutes(RouteBase):
    """Complete CRUD operations for todos."""

    tag = "Todos"

    def get(
        self,
        todo_id: Optional[int] = Query(None),
        completed: Optional[bool] = Query(None)
    ):
        """GET: Retrieve todos (list or specific)."""
        if todo_id is not None:
            todo = next((t for t in todos_db if t["id"] == todo_id), None)
            if not todo:
                raise HTTPException(status_code=404, detail="Not found")
            return todo

        result = todos_db
        if completed is not None:
            result = [t for t in todos_db if t["completed"] == completed]

        return {"total": len(result), "todos": result}

    def post(self, todo: TodoCreate = Body(...)):
        """POST: Create new todo."""
        global next_id
        new_todo = {"id": next_id, "title": todo.title, "completed": todo.completed}
        todos_db.append(new_todo)
        next_id += 1
        return new_todo

    def put(self, todo_id: int = Query(..., gt=0), todo: TodoCreate = Body(...)):
        """PUT: Completely replace todo."""
        todo_idx = next((i for i, t in enumerate(todos_db) if t["id"] == todo_id), None)
        if todo_idx is None:
            raise HTTPException(status_code=404, detail="Not found")
        todos_db[todo_idx] = {"id": todo_id, "title": todo.title, "completed": todo.completed}
        return todos_db[todo_idx]

    def patch(self, todo_id: int = Query(..., gt=0), todo: TodoUpdate = Body(...)):
        """PATCH: Partially update todo."""
        todo_idx = next((i for i, t in enumerate(todos_db) if t["id"] == todo_id), None)
        if todo_idx is None:
            raise HTTPException(status_code=404, detail="Not found")
        if todo.title is not None:
            todos_db[todo_idx]["title"] = todo.title
        if todo.completed is not None:
            todos_db[todo_idx]["completed"] = todo.completed
        return todos_db[todo_idx]

    def delete(self, todo_id: int = Query(..., gt=0)):
        """DELETE: Remove todo."""
        todo_idx = next((i for i, t in enumerate(todos_db) if t["id"] == todo_id), None)
        if todo_idx is None:
            raise HTTPException(status_code=404, detail="Not found")
        deleted = todos_db.pop(todo_idx)
        return {"message": "Deleted", "deleted": deleted}
```

---

## HTTP Status Code Best Practices

Use appropriate status codes for responses:

| Status | Meaning | Use Case |
|--------|---------|----------|
| **200 OK** | Success | GET, PUT, PATCH success |
| **201 Created** | Resource created | POST success |
| **204 No Content** | Success with no body | DELETE success |
| **400 Bad Request** | Invalid input | Validation failed |
| **404 Not Found** | Resource missing | ID doesn't exist |
| **422 Unprocessable Entity** | Semantic error | Wrong data type |
| **500 Internal Server Error** | Server error | Unexpected error |

### Setting Status Codes in FastAPI

```python
from fastapi import status

class TodoRoutes(RouteBase):
    def post(self, todo: TodoCreate = Body(...)):
        # Create todo...
        return new_todo  # Default 200

    # Better - return 201 Created
    def post(self, todo: TodoCreate = Body(...)):
        # Create todo...
        return new_todo, status.HTTP_201_CREATED

    # Or use tuple return
    def post(self, todo: TodoCreate = Body(...)):
        # Create todo...
        return new_todo, 201
```

!!! note "Status Code Return Values"
    In FastAPI, you can return status codes as tuples or use `status.HTTP_201_CREATED` constants. REROUTE supports both conventions.

---

## Testing All HTTP Methods

### Using Interactive Documentation

FastAPI provides interactive docs at **http://localhost:7376/docs**:

1. Open http://localhost:7376/docs in your browser
2. Find the `/todos` endpoint
3. Expand it to see all methods
4. Click "Try it out" for each method
5. Fill in parameters and execute

### Using .http Files

Create `tests/todos.http`:

```http
### List all todos
GET http://localhost:7376/todos

### Create new todo
POST http://localhost:7376/todos
Content-Type: application/json

{
  "title": "Test todo with HTTP file",
  "completed": false
}

### Get specific todo
GET http://localhost:7376/todos?todo_id=1

### Replace entire todo (PUT)
PUT http://localhost:7376/todos?todo_id=1
Content-Type: application/json

{
  "title": "Updated todo (PUT)",
  "completed": true
}

### Partial update (PATCH)
PATCH http://localhost:7376/todos?todo_id=1
Content-Type: application/json

{
  "completed": false
}

### Delete todo
DELETE http://localhost:7376/todos?todo_id=1
```

---

## Common Mistakes

### Mistake 1: Using GET for Data Modification

```python
# WRONG - Don't modify data in GET
def get(self, user_id: int):
    # Creates user - this is WRONG!
    create_user(user_id)
    return {"user": user_id}

# CORRECT - Use POST for creation
def post(self, user: UserCreate = Body(...)):
    create_user(user)
    return user
```

### Mistake 2: Not Validating Request Bodies

```python
# WRONG - No validation
def post(self, todo: dict = Body(...)):
    # What if title is missing or invalid?
    todos_db.append(todo)
    return todo

# CORRECT - Use Pydantic for validation
class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1)
    completed: bool = False

def post(self, todo: TodoCreate = Body(...)):
    # Pydantic validates automatically
    todos_db.append(todo.dict())
    return todo
```

### Mistake 3: Confusing PUT and PATCH

```python
# PUT - Replaces ENTIRE resource
def put(self, todo_id: int, todo: TodoCreate):
    # All fields required - replaces existing data
    todos_db[todo_id] = {"id": todo_id, **todo.dict()}

# PATCH - Updates PARTIAL resource
def patch(self, todo_id: int, todo: TodoUpdate):
    # Only updates provided fields
    if todo.title:
        todos_db[todo_id]["title"] = todo.title
    if todo.completed is not None:
        todos_db[todo_id]["completed"] = todo.completed
```

---

## Troubleshooting

### Problem 1: 405 Method Not Allowed

**Symptom:** `{"detail": "Method Not Allowed"}`

**Cause:** Method not implemented in route class

**Solution:**
```python
class TodoRoutes(RouteBase):
    def get(self):  # GET implemented
        pass

    # Missing post() - POST will return 405
    def post(self):  # Add this
        pass
```

### Problem 2: Request Body Not Received

**Symptom:** Body parameter is None or empty

**Cause:** Missing `Content-Type: application/json` header

**Solution:**
```bash
# Add Content-Type header
curl -X POST http://localhost:7376/todos \
  -H "Content-Type: application/json" \  # Add this!
  -d '{"title": "Test"}'
```

### Problem 3: Validation Not Working

**Symptom:** Invalid data accepted without error

**Cause:** Not using Pydantic model with Field validation

**Solution:**
```python
# Use Pydantic with Field constraints
from pydantic import BaseModel, Field

class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    completed: bool = False

def post(self, todo: TodoCreate = Body(...)):
    # Validation automatic
    pass
```

---

## Summary

In this tutorial, you learned:

- **GET**: Retrieve data (safe, idempotent)
- **POST**: Create new resources (not idempotent)
- **PUT**: Complete replacement (idempotent)
- **PATCH**: Partial updates (not always idempotent)
- **DELETE**: Remove resources (idempotent)
- **Status Codes**: Use appropriate codes (200, 201, 404, 422)
- **Pydantic Validation**: Automatic request/response validation
- **CRUD Operations**: Complete Create, Read, Update, Delete workflow

**Key takeaways:**
- Each HTTP method has specific purpose and semantics
- Pydantic models provide automatic validation
- PUT replaces, PATCH updates partially
- Status codes communicate outcome clearly
- Interactive docs make testing easy

---

## Next Steps

**Continue learning:**
- [Query Parameters](query-params.md) - Work with query strings and optional parameters
- [CRUD Application](../medium/crud-app.md) - Advanced CRUD patterns
- [Error Handling](../medium/error-handling.md) - Custom error responses

**Practice ideas:**
- Build a blog API with posts and comments
- Create user management system
- Implement shopping cart with items

---

**Ready to work with query parameters?** Continue to [Query Parameters](query-params.md)!
