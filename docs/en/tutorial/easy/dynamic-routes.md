---
difficulty: easy
time: 15 minutes
prerequisites:
  - link: ../../start-here.md
  - link: ../very-easy/hello-world.md
  - link: ../very-easy/understanding-routes.md
next: http-methods.md
---

# Dynamic Routes

Learn how to create dynamic routes with path parameters to handle variable URLs like `/users/1`, `/posts/42`, or `/products/any-identifier`.

## What You'll Learn

- How to create dynamic routes with path parameters
- Different types of path parameters (integers, strings, UUIDs)
- Parameter validation and type hints
- Working with multiple path parameters
- Optional vs required parameters

## Prerequisites

- Completed [Hello World](../very-easy/hello-world.md) tutorial
- Completed [Understanding Routes](../very-easy/understanding-routes.md) tutorial
- Basic understanding of URL structure
- Working REROUTE project

---

## What are Dynamic Routes?

Dynamic routes allow you to capture variable parts of the URL path. Instead of creating separate routes for each resource, you create one route that handles all variations.

**Examples:**
- `/users/1` → User with ID 1
- `/users/2` → User with ID 2
- `/posts/my-first-post` → Post with slug "my-first-post"
- `/products/abc-123-xyz` → Product with code "abc-123-xyz"

---

## Step 1: Create a Dynamic Route

Create a new route for handling individual users:

```bash
reroute create route --path /users --name UserRoutes --methods GET
```

This creates: `app/routes/users/page.py`

Now create a subdirectory for individual user routes:

```bash
mkdir -p app/routes/users/[user_id]
touch app/routes/users/[user_id]/page.py
```

!!! important "Folder Naming Convention"
    In REROUTE, dynamic path parameters are denoted by square brackets `[parameter_name]` in folder names:
    - `[user_id]` → Captures user ID from URL
    - `[post_slug]` → Captures post slug from URL
    - `[uuid]` → Captures UUID from URL

---

## Step 2: Implement Dynamic Route with Integer Parameter

Edit `app/routes/users/[user_id]/page.py`:

```python
from reroute import RouteBase
from reroute.params import Path
from fastapi import HTTPException

class UserIdRoutes(RouteBase):
    """Individual user endpoints."""

    def get(self, user_id: int = Path(..., description="User ID")):
        """
        Get a specific user by ID.

        - **user_id**: The unique identifier for the user
        """
        # Simulate fetching user from database
        users = [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
            {"id": 3, "name": "Charlie", "email": "charlie@example.com"}
        ]

        # Find user by ID
        user = next((u for u in users if u["id"] == user_id), None)

        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found"
            )

        return {
            "user": user,
            "requested_id": user_id,
            "type": "integer"
        }
```

### Test Your Dynamic Route

**Test with valid user ID:**
```bash
curl http://localhost:7376/users/1
```

**Expected Output:**
```json
{
  "user": {
    "id": 1,
    "name": "Alice",
    "email": "alice@example.com"
  },
  "requested_id": 1,
  "type": "integer"
}
```

**Test with non-existent user:**
```bash
curl http://localhost:7376/users/999
```

**Expected Output:**
```json
{
  "detail": "User with ID 999 not found"
}
```

**Test with invalid type (non-integer):**
```bash
curl http://localhost:7376/users/abc
```

**Expected Output:**
```json
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["path", "user_id"],
      "msg": "Input should be a valid integer",
      "input": "abc"
    }
  ]
}
```

`★ Insight ─────────────────────────────────────`
**Type Validation Magic**: When you use `user_id: int = Path(...)`, FastAPI automatically validates and converts the path parameter. Invalid types (like "abc" for an integer) are rejected before your code runs, providing clear error messages to API consumers.
`─────────────────────────────────────────────────`

---

## Step 3: String Path Parameters

Create a blog posts route with string slugs:

```bash
mkdir -p app/routes/posts/[slug]
touch app/routes/posts/[slug]/page.py
```

Edit `app/routes/posts/[slug]/page.py`:

```python
from reroute import RouteBase
from reroute.params import Path
from fastapi import HTTPException

class PostSlugRoutes(RouteBase):
    """Individual blog post endpoints by slug."""

    def get(self, slug: str = Path(..., description="Post slug")):
        """
        Get a post by its URL slug.

        - **slug**: URL-friendly identifier (e.g., "my-first-post")
        """
        # Simulate fetching post from database
        posts = {
            "my-first-post": {
                "title": "My First Post",
                "content": "This is my first blog post!",
                "author": "Alice"
            },
            "python-tips": {
                "title": "Python Tips and Tricks",
                "content": "Here are some useful Python tips...",
                "author": "Bob"
            },
            "fastapi-guide": {
                "title": "Complete FastAPI Guide",
                "content": "FastAPI is amazing because...",
                "author": "Charlie"
            }
        }

        if slug not in posts:
            raise HTTPException(
                status_code=404,
                detail=f"Post with slug '{slug}' not found"
            )

        return {
            "post": posts[slug],
            "slug": slug,
            "type": "string"
        }
```

### Test String Parameters

**Test with valid slug:**
```bash
curl http://localhost:7376/posts/my-first-post
```

**Expected Output:**
```json
{
  "post": {
    "title": "My First Post",
    "content": "This is my first blog post!",
    "author": "Alice"
  },
  "slug": "my-first-post",
  "type": "string"
}
```

---

## Step 4: Multiple Path Parameters

You can combine multiple path parameters in a single route:

```bash
mkdir -p app/routes/categories/[category_id]/products/[product_id]
touch app/routes/categories/[category_id]/products/[product_id]/page.py
```

Edit `app/routes/categories/[category_id]/products/[product_id]/page.py`:

```python
from reroute import RouteBase
from reroute.params import Path

class CategoryProductRoutes(RouteBase):
    """Product within a category endpoints."""

    def get(
        self,
        category_id: int = Path(..., description="Category ID"),
        product_id: int = Path(..., description="Product ID")
    ):
        """
        Get a specific product within a category.

        - **category_id**: The category identifier
        - **product_id**: The product identifier
        """
        return {
            "category_id": category_id,
            "product_id": product_id,
            "url": f"/categories/{category_id}/products/{product_id}",
            "message": f"Product {product_id} in category {category_id}"
        }
```

### Test Multiple Parameters

```bash
curl http://localhost:7376/categories/5/products/42
```

**Expected Output:**
```json
{
  "category_id": 5,
  "product_id": 42,
  "url": "/categories/5/products/42",
  "message": "Product 42 in category 5"
}
```

`★ Insight ─────────────────────────────────────`
**Nested Route Organization**: REROUTE's file system mirrors your URL structure exactly. This makes it easy to understand your API structure just by looking at folders - no complex routing configuration needed. The path `/categories/5/products/42` maps directly to `categories/[category_id]/products/[product_id]/page.py`.
`─────────────────────────────────────────────────`

---

## Step 5: UUID Path Parameters

For working with UUIDs (common in database systems):

```bash
mkdir -p app/routes/documents/[uuid]
touch app/routes/documents/[uuid]/page.py
```

Edit `app/routes/documents/[uuid]/page.py`:

```python
from reroute import RouteBase
from reroute.params import Path
from fastapi import HTTPException
from uuid import UUID

class DocumentUuidRoutes(RouteBase):
    """Document endpoints by UUID."""

    def get(self, uuid: UUID = Path(..., description="Document UUID")):
        """
        Get a document by its UUID.

        - **uuid**: Universally unique identifier
        """
        # Simulate fetching document
        documents = {
            "a1b2c3d4-e5f6-7890-abcd-ef1234567890": {
                "title": "Important Document",
                "content": "Secret content here..."
            }
        }

        uuid_str = str(uuid)
        if uuid_str not in documents:
            raise HTTPException(
                status_code=404,
                detail=f"Document with UUID {uuid_str} not found"
            )

        return {
            "document": documents[uuid_str],
            "uuid": uuid_str,
            "version": uuid.version
        }
```

### Test UUID Parameters

**Test with valid UUID:**
```bash
curl http://localhost:7376/documents/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Expected Output:**
```json
{
  "document": {
    "title": "Important Document",
    "content": "Secret content here..."
  },
  "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "version": 4
}
```

**Test with invalid UUID:**
```bash
curl http://localhost:7376/documents/not-a-uuid
```

**Expected Output:** (422 Unprocessable Entity)
```json
{
  "detail": [
    {
      "type": "uuid_parsing",
      "loc": ["path", "uuid"],
      "msg": "Input should be a valid UUID",
      "input": "not-a-uuid"
    }
  ]
}
```

---

## Parameter Validation with Constraints

You can add validation constraints to path parameters:

```python
from reroute import RouteBase
from reroute.params import Path
from fastapi import HTTPException

class ItemRoutes(RouteBase):
    """Item endpoints with validation."""

    def get(
        self,
        item_id: int = Path(
            ...,
            description="Item ID",
            gt=0,      # Must be greater than 0
            le=1000    # Must be less than or equal to 1000
        )
    ):
        """
        Get an item with constrained ID.

        - **item_id**: ID between 1 and 1000
        """
        return {
            "item_id": item_id,
            "valid_range": "1-1000"
        }
```

### Test Validation

**Test with valid ID:**
```bash
curl http://localhost:7376/items/500
```

**Expected Output:**
```json
{
  "item_id": 500,
  "valid_range": "1-1000"
}
```

**Test with invalid ID (too large):**
```bash
curl http://localhost:7376/items/2000
```

**Expected Output:** (422 Unprocessable Entity)
```json
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": ["path", "item_id"],
      "msg": "Input should be less than or equal to 1000",
      "input": "2000",
      "ctx": {"le": 1000}
    }
  ]
}
```

### Common Validation Constraints

```python
from reroute.params import Path

# Integer constraints
user_id: int = Path(..., gt=0)           # Greater than 0
age: int = Path(..., ge=0, le=150)       # Between 0 and 150
rating: int = Path(..., ge=1, le=5)      # Between 1 and 5

# String constraints
slug: str = Path(..., min_length=3, max_length=50)
name: str = Path(..., pattern="^[a-zA-Z0-9-]+$")  # Alphanumeric and hyphens
```

---

## Complete Dynamic Routes Example

Here's a comprehensive example showing all concepts:

```bash
mkdir -p app/routes/api/[version]/users/[user_id]
touch app/routes/api/[version]/users/[user_id]/page.py
```

Edit `app/routes/api/[version]/users/[user_id]/page.py`:

```python
from reroute import RouteBase
from reroute.params import Path, Query
from fastapi import HTTPException

class ApiVersionUserRoutes(RouteBase):
    """API versioned user endpoints."""

    def get(
        self,
        version: str = Path(..., description="API version (v1, v2)"),
        user_id: int = Path(..., gt=0, description="User ID"),
        details: bool = Query(False, description="Include extra details")
    ):
        """
        Get a user with API versioning.

        - **version**: API version
        - **user_id**: User ID (must be positive)
        - **details**: Include additional details
        """
        # Simulate version-specific logic
        response = {
            "api_version": version,
            "user_id": user_id,
            "name": f"User {user_id}"
        }

        # Add extra details if requested
        if details:
            response.update({
                "email": f"user{user_id}@example.com",
                "created_at": "2025-01-01T00:00:00Z",
                "version_features": f"Features for {version}"
            })

        return response
```

### Test Complete Example

```bash
# Basic request
curl http://localhost:7376/api/v1/users/42

# With details
curl http://localhost:7376/api/v1/users/42?details=true

# Different version
curl http://localhost:7376/api/v2/users/42?details=true
```

---

## Troubleshooting

### Problem 1: Parameter Not Captured

**Symptom:** URL parameter is always None or wrong value

**Solution:**
- Check folder name uses square brackets: `[user_id]` not `user_id`
- Verify parameter name in `Path()` matches folder name
- Ensure `page.py` is in the correct nested folder

### Problem 2: Type Validation Not Working

**Symptom:** String "abc" accepted when integer expected

**Solution:**
```python
# Correct
def get(self, user_id: int = Path(...)):  # Type hint before Path()

# Wrong
def get(self, user_id = Path(...)):  # Missing type hint
```

### Problem 3: 404 on Valid Parameter

**Symptom:** Route returns 404 even with correct parameter

**Possible Causes:**
1. Parameter validation failed (e.g., `gt=0` but passed 0)
2. File is not named exactly `page.py`
3. Server not restarted after adding new route

**Solution:**
```bash
# Check the actual error in server logs
# Or use interactive docs at http://localhost:7376/docs
```

### Problem 4: Folder Structure Confusion

**Common mistake:**
```
app/routes/
    ├── users/
    │   ├── [user_id]/page.py     # Wrong - don't name folder with parameter
    └── users/[user_id]/page.py   # Wrong - duplicate users folder
```

**Correct structure:**
```
app/routes/
    ├── page.py                   # → /users (list users)
    └── [user_id]/                # → /users/{id} (specific user)
        └── page.py
```

---

## Best Practices

### 1. Use Descriptive Parameter Names

```python
# Good
[user_id]/page.py
[post_slug]/page.py
[order_uuid]/page.py

# Avoid
[id]/page.py
[x]/page.py
[param]/page.py
```

### 2. Add Type Hints Always

```python
# Good
def get(self, user_id: int = Path(...)):
    pass

# Avoid
def get(self, user_id = Path(...)):
    pass
```

### 3. Add Validation Constraints

```python
# Good
def get(self, user_id: int = Path(..., gt=0, le=1000000)):
    pass

# Acceptable but less safe
def get(self, user_id: int = Path(...)):
    pass
```

### 4. Provide Clear Error Messages

```python
# Good
if not user:
    raise HTTPException(
        status_code=404,
        detail=f"User {user_id} not found. "
               f"Valid IDs: 1-100"
    )

# Less helpful
if not user:
    raise HTTPException(status_code=404)
```

---

## Summary

In this tutorial, you learned:

- **Dynamic Routes**: Use `[parameter_name]` folder naming
- **Type Validation**: Automatic validation with type hints (`int`, `str`, `UUID`)
- **Multiple Parameters**: Combine path parameters for nested routes
- **Validation Constraints**: Use `gt`, `ge`, `lt`, `le`, `min_length`, `max_length`
- **Error Handling**: Return helpful 404 messages for missing resources

**Key concepts:**
- Folder structure = URL structure
- `Path()` parameters extract values from URL
- Type hints enable automatic validation
- FastAPI provides clear error messages for invalid input

---

## Next Steps

**Continue learning:**
- [HTTP Methods](http-methods.md) - Learn POST, PUT, DELETE operations
- [Query Parameters](query-params.md) - Work with query strings and optional parameters
- [CRUD Application](../medium/crud-app.md) - Build a complete CRUD application

**Practice ideas:**
- Create a blog API with `/posts/[slug]` routes
- Build an e-commerce API with category/product nesting
- Implement API versioning with `/api/v[version]/...`

---

**Ready to handle different HTTP methods?** Continue to [HTTP Methods](http-methods.md)!
