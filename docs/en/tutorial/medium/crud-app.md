---
difficulty: medium
time: 30 minutes
prerequisites:
  - link: ../../start-here.md
  - link: ../easy/dynamic-routes.md
  - link: ../easy/http-methods.md
  - link: ../easy/query-params.md
next: decorators-intro.md
---

# CRUD Application

Build a complete Create, Read, Update, Delete (CRUD) application with REROUTE, combining all the concepts you've learned so far.

## What You'll Learn

- Building a complete CRUD API
- Combining dynamic routes with HTTP methods
- Working with multiple related resources
- Data validation and error handling
- Building production-ready APIs
- Testing with .http files

## Prerequisites

- Completed all Easy tutorials
- Understanding of HTTP methods
- Familiarity with query parameters
- Working REROUTE project

---

## What is a CRUD Application?

CRUD stands for the four basic operations of persistent storage:

| Operation | HTTP Method | Description | SQL Equivalent |
|-----------|-------------|-------------|----------------|
| **Create** | POST | Add new data | INSERT |
| **Read** | GET | Retrieve data | SELECT |
| **Update** | PUT/PATCH | Modify existing data | UPDATE |
| **Delete** | DELETE | Remove data | DELETE |

We'll build a **Task Management API** where users can manage their tasks with categories.

---

## Project Structure

After completion, your project will have:

```
task-manager/
├── app/
│   ├── routes/
│   │   ├── tasks/
│   │   │   ├── page.py              # List & create tasks
│   │   │   └── [task_id]/
│   │   │       └── page.py          # Get/update/delete specific task
│   │   └── categories/
│   │       ├── page.py              # List & create categories
│   │       └── [category_id]/
│   │           └── page.py          # Category operations
│   └── models/
│       └── task.py                  # Pydantic schemas
├── tests/
│   └── tasks.http                   # API tests
├── config.py
├── main.py
└── requirements.txt
```

---

## Step 1: Create Project

```bash
reroute init task-manager --framework fastapi
```

Answer the prompts:
- Framework: fastapi
- Include tests: Yes

Navigate to the project:

```bash
cd task-manager
```

---

## Step 2: Create Pydantic Models

Create the models directory and schemas:

```bash
mkdir -p app/models
touch app/models/__init__.py
touch app/models/task.py
```

Edit `app/models/task.py`:

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class Priority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Status(str, Enum):
    """Task status values."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ARCHIVED = "archived"

class TaskBase(BaseModel):
    """Base task schema with common fields."""
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    priority: Priority = Field(default=Priority.MEDIUM)
    status: Status = Field(default=Status.TODO)
    category_id: Optional[int] = Field(None, gt=0)
    due_date: Optional[datetime] = None

    @validator('title')
    def title_must_not_be_blank(cls, v):
        """Ensure title is not just whitespace."""
        if not v.strip():
            raise ValueError('Title cannot be blank')
        return v.strip()

class TaskCreate(TaskBase):
    """Schema for creating a new task."""
    pass

class TaskUpdate(BaseModel):
    """Schema for updating a task (all fields optional)."""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    priority: Optional[Priority] = None
    status: Optional[Status] = None
    category_id: Optional[int] = Field(None, gt=0)
    due_date: Optional[datetime] = None

    @validator('title')
    def title_must_not_be_blank(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Title cannot be blank')
        return v.strip() if v else v

class TaskResponse(TaskBase):
    """Schema for task responses (includes id and timestamps)."""
    id: int
    created_at: datetime
    updated_at: datetime
    category: Optional[str] = None  # Populated from category lookup

    class Config:
        from_attributes = True

class CategoryBase(BaseModel):
    """Base category schema."""
    name: str = Field(..., min_length=2, max_length=100)
    color: str = Field(default="#007bff", regex=r"^#[0-9A-Fa-f]{6}$")
    description: Optional[str] = Field(None, max_length=500)

class CategoryCreate(CategoryBase):
    """Schema for creating a category."""
    pass

class CategoryResponse(CategoryBase):
    """Schema for category responses."""
    id: int
    created_at: datetime
    task_count: int = 0  # Number of tasks in this category

    class Config:
        from_attributes = True
```

`★ Insight ─────────────────────────────────────`
**Pydantic Validation Power**: Notice how we're using Pydantic's powerful validation features:
- `Field()` with constraints (min_length, max_length, regex)
- Custom validators with `@validator` decorator
- Enum classes for fixed values (Priority, Status)
- Optional fields for partial updates

This validation happens automatically before your route code runs, ensuring data integrity.
`─────────────────────────────────────────────────`

---

## Step 3: Create Category Routes

First, create the category management endpoints:

```bash
reroute create route --path /categories --name CategoryRoutes --methods GET,POST,PUT,DELETE
```

Edit `app/routes/categories/page.py`:

```python
from typing import List, Dict, Optional
from datetime import datetime
from reroute import RouteBase
from reroute.params import Query, Body
from fastapi import HTTPException, status
from app.models.task import CategoryCreate, CategoryResponse, CategoryBase

# In-memory storage (use database in production)
categories_db: List[Dict] = [
    {"id": 1, "name": "Work", "color": "#dc3545", "description": "Work-related tasks", "created_at": datetime.now()},
    {"id": 2, "name": "Personal", "color": "#28a745", "description": "Personal tasks", "created_at": datetime.now()},
    {"id": 3, "name": "Shopping", "color": "#ffc107", "description": "Shopping lists", "created_at": datetime.now()}
]
next_category_id = 4

class CategoryRoutes(RouteBase):
    """Category management endpoints."""
    tag = "Categories"

    def get(
        self,
        category_id: Optional[int] = Query(None, gt=0, description="Category ID"),
        search: Optional[str] = Query(None, min_length=2, description="Search term")
    ):
        """
        Get categories (list or specific).

        - **category_id**: If provided, returns specific category
        - **search**: Filter categories by name
        """
        # Get specific category
        if category_id is not None:
            category = next((c for c in categories_db if c["id"] == category_id), None)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category {category_id} not found"
                )
            return category

        # List all categories with optional search
        result = categories_db
        if search:
            result = [c for c in categories_db if search.lower() in c["name"].lower()]

        return {
            "total": len(result),
            "categories": result
        }

    def post(self, category: CategoryCreate = Body(...)):
        """
        Create a new category.

        - **name**: Category name (required)
        - **color**: Hex color code (default: #007bff)
        - **description**: Optional description
        """
        global next_category_id

        # Check for duplicate name
        if any(c["name"].lower() == category.name.lower() for c in categories_db):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{category.name}' already exists"
            )

        # Create new category
        new_category = {
            "id": next_category_id,
            "name": category.name,
            "color": category.color,
            "description": category.description,
            "created_at": datetime.now()
        }
        categories_db.append(new_category)
        next_category_id += 1

        return new_category, status.HTTP_201_CREATED

    def put(
        self,
        category_id: int = Query(..., gt=0),
        category: CategoryCreate = Body(...)
    ):
        """
        Completely replace a category.

        - **category_id**: ID of category to replace
        - All fields required (replaces entire category)
        """
        # Find category
        category_idx = next(
            (i for i, c in enumerate(categories_db) if c["id"] == category_id),
            None
        )

        if category_idx is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category {category_id} not found"
            )

        # Replace category
        categories_db[category_idx] = {
            "id": category_id,
            "name": category.name,
            "color": category.color,
            "description": category.description,
            "created_at": categories_db[category_idx]["created_at"]
        }

        return categories_db[category_idx]

    def delete(self, category_id: int = Query(..., gt=0)):
        """
        Delete a category.

        - **category_id**: ID of category to delete
        """
        # Find category
        category_idx = next(
            (i for i, c in enumerate(categories_db) if c["id"] == category_id),
            None
        )

        if category_idx is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category {category_id} not found"
            )

        # Check if category has tasks (in real app, you'd check tasks table)
        # For now, we'll allow deletion

        deleted = categories_db.pop(category_idx)
        return {
            "message": "Category deleted successfully",
            "deleted": deleted
        }
```

---

## Step 4: Create Task Routes (List and Create)

```bash
reroute create route --path /tasks --name TaskRoutes --methods GET,POST
```

Edit `app/routes/tasks/page.py`:

```python
from typing import List, Dict, Optional
from datetime import datetime
from reroute import RouteBase
from reroute.params import Query, Body
from fastapi import HTTPException, status
from app.models.task import TaskCreate, TaskUpdate, TaskResponse, Priority, Status

# In-memory storage
tasks_db: List[Dict] = [
    {
        "id": 1,
        "title": "Complete project proposal",
        "description": "Write and submit the Q1 project proposal",
        "priority": "high",
        "status": "in_progress",
        "category_id": 1,
        "due_date": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    {
        "id": 2,
        "title": "Buy groceries",
        "description": "Milk, eggs, bread, vegetables",
        "priority": "medium",
        "status": "todo",
        "category_id": 3,
        "due_date": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
]
next_task_id = 3

class TaskRoutes(RouteBase):
    """Task list and create endpoints."""
    tag = "Tasks"

    def get(
        self,
        status: Optional[Status] = Query(None, description="Filter by status"),
        priority: Optional[Priority] = Query(None, description="Filter by priority"),
        category_id: Optional[int] = Query(None, gt=0, description="Filter by category"),
        search: Optional[str] = Query(None, min_length=2, description="Search in title/description"),
        sort_by: str = Query("created_at", description="Field to sort by"),
        order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
        page: int = Query(1, ge=1, description="Page number"),
        limit: int = Query(10, ge=1, le=100, description="Items per page")
    ):
        """
        Get tasks with filtering, sorting, and pagination.

        - **status**: Filter by task status
        - **priority**: Filter by priority level
        - **category_id**: Filter by category
        - **search**: Search in title and description
        - **sort_by**: Field to sort (created_at, due_date, priority)
        - **order**: asc or desc
        - **page**: Page number (starts at 1)
        - **limit**: Items per page
        """
        # Start with all tasks
        result = tasks_db.copy()

        # Apply filters
        if status:
            result = [t for t in result if t["status"] == status.value]
        if priority:
            result = [t for t in result if t["priority"] == priority.value]
        if category_id:
            result = [t for t in result if t["category_id"] == category_id]
        if search:
            search_lower = search.lower()
            result = [
                t for t in result
                if search_lower in t["title"].lower() or
                   (t.get("description") and search_lower in t["description"].lower())
            ]

        # Apply sorting
        if sort_by == "created_at":
            result.sort(key=lambda x: x["created_at"], reverse=(order == "desc"))
        elif sort_by == "due_date":
            # Sort by due_date (None values last)
            result.sort(
                key=lambda x: (x["due_date"] is None, x["due_date"]),
                reverse=(order == "desc")
            )
        elif sort_by == "priority":
            # Priority order: urgent, high, medium, low
            priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
            result.sort(
                key=lambda x: priority_order.get(x["priority"], 99),
                reverse=(order == "asc")
            )

        # Calculate pagination
        total = len(result)
        start = (page - 1) * limit
        end = start + limit
        paginated = result[start:end]

        return {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit,
            "filters": {
                "status": status.value if status else None,
                "priority": priority.value if priority else None,
                "category_id": category_id,
                "search": search
            },
            "tasks": paginated
        }

    def post(self, task: TaskCreate = Body(...)):
        """
        Create a new task.

        - **title**: Task title (required, 3-200 characters)
        - **description**: Optional description
        - **priority**: low, medium, high, or urgent
        - **status**: todo, in_progress, done, or archived
        - **category_id**: Optional category ID
        - **due_date**: Optional due date
        """
        global next_task_id

        # Validate category exists if provided
        if task.category_id:
            # In real app, check database
            pass

        # Create new task
        new_task = {
            "id": next_task_id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority.value,
            "status": task.status.value,
            "category_id": task.category_id,
            "due_date": task.due_date,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        tasks_db.append(new_task)
        next_task_id += 1

        return new_task, status.HTTP_201_CREATED
```

---

## Step 5: Create Individual Task Routes

```bash
mkdir -p app/routes/tasks/[task_id]
touch app/routes/tasks/[task_id]/page.py
```

Edit `app/routes/tasks/[task_id]/page.py`:

```python
from reroute import RouteBase
from reroute.params import Path, Body
from fastapi import HTTPException, status
from app.models.task import TaskUpdate
from datetime import datetime

# Import shared database
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from routes.tasks.page import tasks_db

class TaskIdRoutes(RouteBase):
    """Individual task endpoints."""
    tag = "Tasks"

    def get(self, task_id: int = Path(..., gt=0, description="Task ID")):
        """
        Get a specific task by ID.

        - **task_id**: The task identifier
        """
        task = next((t for t in tasks_db if t["id"] == task_id), None)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        return task

    def patch(
        self,
        task_id: int = Path(..., gt=0),
        task: TaskUpdate = Body(...)
    ):
        """
        Partially update a task.

        - **task_id**: ID of task to update
        - Only provided fields are updated
        """
        # Find task
        task_idx = next(
            (i for i, t in enumerate(tasks_db) if t["id"] == task_id),
            None
        )

        if task_idx is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        # Update only provided fields
        if task.title is not None:
            tasks_db[task_idx]["title"] = task.title
        if task.description is not None:
            tasks_db[task_idx]["description"] = task.description
        if task.priority is not None:
            tasks_db[task_idx]["priority"] = task.priority.value
        if task.status is not None:
            tasks_db[task_idx]["status"] = task.status.value
        if task.category_id is not None:
            tasks_db[task_idx]["category_id"] = task.category_id
        if task.due_date is not None:
            tasks_db[task_idx]["due_date"] = task.due_date

        # Update timestamp
        tasks_db[task_idx]["updated_at"] = datetime.now()

        return tasks_db[task_idx]

    def put(
        self,
        task_id: int = Path(..., gt=0),
        task: TaskUpdate = Body(...)
    ):
        """
        Completely replace a task.

        - **task_id**: ID of task to replace
        - All fields replaced except id and timestamps
        """
        # Find task
        task_idx = next(
            (i for i, t in enumerate(tasks_db) if t["id"] == task_id),
            None
        )

        if task_idx is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        # Get current values for defaults
        current = tasks_db[task_idx]

        # Replace task (use provided values or current)
        tasks_db[task_idx] = {
            "id": task_id,
            "title": task.title if task.title is not None else current["title"],
            "description": task.description,
            "priority": task.priority.value if task.priority else current["priority"],
            "status": task.status.value if task.status else current["status"],
            "category_id": task.category_id,
            "due_date": task.due_date,
            "created_at": current["created_at"],
            "updated_at": datetime.now()
        }

        return tasks_db[task_idx]

    def delete(self, task_id: int = Path(..., gt=0)):
        """
        Delete a task.

        - **task_id**: ID of task to delete
        """
        # Find task
        task_idx = next(
            (i for i, t in enumerate(tasks_db) if t["id"] == task_id),
            None
        )

        if task_idx is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        deleted = tasks_db.pop(task_idx)
        return {
            "message": "Task deleted successfully",
            "deleted": deleted
        }
```

---

## Step 6: Create HTTP Test File

Create `tests/tasks.http` for testing your API:

```http
### ===================================================
### CATEGORIES
### ===================================================

### List all categories
GET http://localhost:7376/categories

### Create a new category
POST http://localhost:7376/categories
Content-Type: application/json

{
  "name": "Health",
  "color": "#28a745",
  "description": "Health and fitness tasks"
}

### Get specific category
GET http://localhost:7376/categories?category_id=1

### Update category (PUT)
PUT http://localhost:7376/categories?category_id=1
Content-Type: application/json

{
  "name": "Work Projects",
  "color": "#dc3545",
  "description": "All work-related projects"
}

### Delete category
DELETE http://localhost:7376/categories?category_id=3

### ===================================================
### TASKS - List and Create
### ===================================================

### List all tasks
GET http://localhost:7376/tasks

### List with pagination
GET http://localhost:7376/tasks?page=1&limit=5

### Filter by status
GET http://localhost:7376/tasks?status=in_progress

### Filter by priority
GET http://localhost:7376/tasks?priority=high

### Filter by category
GET http://localhost:7376/tasks?category_id=1

### Search tasks
GET http://localhost:7376/tasks?search=project

### Sort by due date
GET http://localhost:7376/tasks?sort_by=due_date&order=asc

### Create a new task
POST http://localhost:7376/tasks
Content-Type: application/json

{
  "title": "Learn REROUTE framework",
  "description": "Complete all tutorials and build a project",
  "priority": "high",
  "status": "in_progress",
  "category_id": 1
}

### Create urgent task with due date
POST http://localhost:7376/tasks
Content-Type: application/json

{
  "title": "Submit quarterly report",
  "description": "Q4 2025 financial report due",
  "priority": "urgent",
  "status": "todo",
  "category_id": 1,
  "due_date": "2025-04-15T17:00:00Z"
}

### ===================================================
### INDIVIDUAL TASKS
### ===================================================

### Get specific task
GET http://localhost:7376/tasks/1

### Partial update (PATCH) - change status only
PATCH http://localhost:7376/tasks/1
Content-Type: application/json

{
  "status": "done"
}

### Partial update - change priority
PATCH http://localhost:7376/tasks/2
Content-Type: application/json

{
  "priority": "high"
}

### Complete update (PUT) - replace all fields
PUT http://localhost:7376/tasks/1
Content-Type: application/json

{
  "title": "Complete REROUTE tutorial series",
  "description": "Finish all tutorials and deploy app",
  "priority": "urgent",
  "status": "in_progress"
}

### Delete task
DELETE http://localhost:7376/tasks/3
```

---

## Step 7: Test Your CRUD API

Start the server:

```bash
python main.py
```

Open http://localhost:7376/docs for interactive testing.

### Test Sequence

**1. Create a category:**
```bash
curl -X POST http://localhost:7376/categories \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Learning",
    "color": "#6f42c1",
    "description": "Learning and development"
  }'
```

**2. Create a task:**
```bash
curl -X POST http://localhost:7376/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Build CRUD app with REROUTE",
    "description": "Complete the CRUD tutorial",
    "priority": "high",
    "status": "in_progress",
    "category_id": 4
  }'
```

**3. List tasks with filters:**
```bash
curl "http://localhost:7376/tasks?status=in_progress&priority=high"
```

**4. Update task status:**
```bash
curl -X PATCH http://localhost:7376/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'
```

**5. Delete completed task:**
```bash
curl -X DELETE http://localhost:7376/tasks/1
```

---

## Advanced Features

### 1. Bulk Operations

Add bulk task creation in `app/routes/tasks/page.py`:

```python
class TaskBulkCreate(BaseModel):
    """Schema for bulk task creation."""
    tasks: List[TaskCreate]
    Field(..., min_items=1, max_items=50)

def post_bulk(self, bulk: TaskBulkCreate = Body(...)):
    """Create multiple tasks at once."""
    global next_task_id
    created_tasks = []

    for task_data in bulk.tasks:
        new_task = {
            "id": next_task_id,
            "title": task_data.title,
            "description": task_data.description,
            "priority": task_data.priority.value,
            "status": task_data.status.value,
            "category_id": task_data.category_id,
            "due_date": task_data.due_date,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        tasks_db.append(new_task)
        created_tasks.append(new_task)
        next_task_id += 1

    return {
        "created": len(created_tasks),
        "tasks": created_tasks
    }, status.HTTP_201_CREATED
```

### 2. Statistics Endpoint

Add a statistics endpoint:

```python
def get_stats(self):
    """Get task statistics."""
    total = len(tasks_db)
    by_status = {}
    by_priority = {}

    for task in tasks_db:
        # Count by status
        status = task["status"]
        by_status[status] = by_status.get(status, 0) + 1

        # Count by priority
        priority = task["priority"]
        by_priority[priority] = by_priority.get(priority, 0) + 1

    return {
        "total": total,
        "by_status": by_status,
        "by_priority": by_priority,
        "completion_rate": round(
            (by_status.get("done", 0) / total * 100) if total > 0 else 0,
            2
        )
    }
```

### 3. Search Autocomplete

Add autocomplete for task titles:

```python
def get_autocomplete(self, q: str = Query(..., min_length=2)):
    """Get autocomplete suggestions for task titles."""
    matches = [
        {"id": t["id"], "title": t["title"]}
        for t in tasks_db
        if q.lower() in t["title"].lower()
    ]
    return {"suggestions": matches[:10]}
```

---

## Common Patterns

### Pattern 1: Soft Delete

Instead of actually deleting, mark as deleted:

```python
def delete(self, task_id: int):
    """Soft delete - mark as archived."""
    task_idx = next((i for i, t in enumerate(tasks_db) if t["id"] == task_id), None)
    if task_idx is None:
        raise HTTPException(404, "Not found")

    tasks_db[task_idx]["status"] = "archived"
    tasks_db[task_idx]["deleted_at"] = datetime.now()

    return {"message": "Task archived", "task": tasks_db[task_idx]}
```

### Pattern 2: Timestamps Track

Track who made changes:

```python
class TaskCreate(BaseModel):
    # ... existing fields
    created_by: Optional[str] = None

class TaskUpdate(BaseModel):
    # ... existing fields
    updated_by: Optional[str] = None

def post(self, task: TaskCreate = Body(...), user: str = Header("default")):
    new_task["created_by"] = user
    # ...

def patch(self, task_id: int, task: TaskUpdate, user: str = Header("default")):
    tasks_db[task_idx]["updated_by"] = user
    # ...
```

### Pattern 3: Validation with Dependencies

Ensure category exists when creating task:

```python
from fastapi import Depends

def get_category(category_id: int):
    """Dependency to validate category exists."""
    category = next((c for c in categories_db if c["id"] == category_id), None)
    if not category:
        raise HTTPException(400, f"Category {category_id} doesn't exist")
    return category

def post(
    self,
    task: TaskCreate = Body(...),
    category: dict = Depends(get_category)
):
    # Category is validated, proceed with creation
    pass
```

---

## Troubleshooting

### Problem 1: Task Not Found

**Symptom:** 404 error for valid task ID

**Cause:** Task might be in wrong database list or ID mismatch

**Solution:**
```python
# Debug: print all task IDs
print([t["id"] for t in tasks_db])

# Verify the correct list is imported
from routes.tasks.page import tasks_db  # Make sure this is correct
```

### Problem 2: Status/Priority Not Validating

**Symptom:** Invalid values accepted

**Cause:** Not using Enum values correctly

**Solution:**
```python
# Wrong
"status": "In_Progress"  # Case sensitive

# Correct
"status": "in_progress"  # Use enum value
```

### Problem 3. Patch Updating Everything

**Symptom:** PATCH replaces all fields instead of partial update

**Cause:** Not checking for None

**Solution:**
```python
# Correct - only update if not None
if task.title is not None:
    tasks_db[task_idx]["title"] = task.title

# Wrong - updates even if None
tasks_db[task_idx]["title"] = task.title or current["title"]
```

---

## Best Practices

### 1. Use Appropriate Status Codes

```python
# 200 OK - Successful GET, PUT, PATCH
return task

# 201 Created - Successful POST
return new_task, status.HTTP_201_CREATED

# 204 No Content - Successful DELETE (no body)
return "", status.HTTP_204_NO_CONTENT

# 400 Bad Request - Validation error
raise HTTPException(400, "Invalid data")

# 404 Not Found - Resource doesn't exist
raise HTTPException(404, "Task not found")

# 422 Unprocessable Entity - Semantic error
raise HTTPException(422, "Category doesn't exist")
```

### 2. Validate Input Thoroughly

```python
# Good - Pydantic validates automatically
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    priority: Priority = Field(default=Priority.MEDIUM)

# Also check business logic
if any(t["title"] == task.title for t in tasks_db):
    raise HTTPException(400, "Task with this title exists")
```

### 3. Return Helpful Error Messages

```python
# Good
raise HTTPException(
    status_code=404,
    detail=f"Task {task_id} not found. Valid IDs: {[t['id'] for t in tasks_db]}"
)

# Less helpful
raise HTTPException(404, "Not found")
```

### 4. Use Consistent Response Formats

```python
# List endpoint
{
  "page": 1,
  "limit": 10,
  "total": 50,
  "items": [...]
}

# Single item
{
  "id": 1,
  "name": "...",
  ...
}

# Error
{
  "detail": "Error message"
}

# Created
{
  "id": 1,
  ...
}, 201
```

---

## Summary

In this tutorial, you built a complete CRUD application with:

✅ **Pydantic Models**: Comprehensive schemas with validation
✅ **Category Management**: Full CRUD for categories
✅ **Task Management**: Full CRUD with filtering, sorting, pagination
✅ **Dynamic Routes**: Using `[task_id]` for individual tasks
✅ **HTTP Methods**: GET, POST, PUT, PATCH, DELETE
✅ **Query Parameters**: Filtering, searching, sorting
✅ **Error Handling**: Proper status codes and error messages
✅ **Testing**: .http file for easy testing

**Key concepts mastered:**
- Combining all Easy tutorial concepts
- Building production-ready APIs
- Data validation with Pydantic
- RESTful API design patterns
- Testing with .http files and Swagger UI

---

## Next Steps

**Continue learning:**
- [Decorators Introduction](decorators-intro.md) - Add rate limiting and caching
- [Error Handling](error-handling.md) - Advanced error management
- [Database Integration](../../examples/database.md) - Connect to real databases

**Practice ideas:**
- Add user authentication
- Implement task comments/notes
- Build task dependencies (task B requires task A)
- Add file attachments to tasks

---

**Ready to enhance your API with decorators?** Continue to [Decorators Introduction](decorators-intro.md)!
