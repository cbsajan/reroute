---
difficulty: easy
time: 15 minutes
prerequisites:
  - link: ../../start-here.md
  - link: ../very-easy/hello-world.md
  - link: ../very-easy/understanding-routes.md
  - link: dynamic-routes.md
  - link: http-methods.md
next: ../../medium/crud-app.md
---

# Query Parameters

Learn how to work with query parameters for filtering, sorting, pagination, and optional configuration in your API endpoints.

## What You'll Learn

- What query parameters are and when to use them
- Optional vs required query parameters
- Query parameter validation and type hints
- Multiple query parameters
- Common patterns: pagination, filtering, sorting
- Working with lists, dates, and enums

## Prerequisites

- Completed [HTTP Methods](http-methods.md) tutorial
- Understanding of URL structure
- Working REROUTE project

---

## What are Query Parameters?

Query parameters are optional key-value pairs in the URL after the `?` character:

```
https://api.example.com/users?page=2&limit=10&active=true
                           └─────────────────────┘
                           Query parameters
```

**Structure:** `?key1=value1&key2=value2&key3=value3`

**Common uses:**
- Filtering: `?status=active&category=tech`
- Sorting: `?sort=name&order=asc`
- Pagination: `?page=2&limit=10`
- Search: `?q=python+tutorial`
- Configuration: `?debug=true&verbose=false`

---

## Step 1: Create a Products API with Query Parameters

Let's build a products API that demonstrates common query parameter patterns:

```bash
reroute create route --path /products --name ProductRoutes --methods GET
```

This creates: `app/routes/products/page.py`

---

## Step 2: Basic Query Parameters

Edit `app/routes/products/page.py`:

```python
from typing import List, Optional
from reroute import RouteBase
from reroute.params import Query

class ProductRoutes(RouteBase):
    """Product listing with filtering and pagination."""

    def get(
        self,
        page: int = Query(default=1, ge=1, description="Page number"),
        limit: int = Query(default=10, ge=1, le=100, description="Items per page"),
        search: Optional[str] = Query(default=None, description="Search term")
    ):
        """
        Get products with pagination and search.

        - **page**: Page number (must be >= 1)
        - **limit**: Items per page (1-100)
        - **search**: Optional search term
        """
        # Sample products
        products = [
            {"id": 1, "name": "Laptop", "price": 999.99, "category": "Electronics"},
            {"id": 2, "name": "Mouse", "price": 29.99, "category": "Electronics"},
            {"id": 3, "name": "Desk", "price": 299.99, "category": "Furniture"},
            {"id": 4, "name": "Chair", "price": 199.99, "category": "Furniture"},
            {"id": 5, "name": "Monitor", "price": 399.99, "category": "Electronics"},
            {"id": 6, "name": "Keyboard", "price": 79.99, "category": "Electronics"},
            {"id": 7, "name": "Table", "price": 149.99, "category": "Furniture"},
            {"id": 8, "name": "Headphones", "price": 149.99, "category": "Electronics"},
        ]

        # Apply search filter
        if search:
            products = [
                p for p in products
                if search.lower() in p["name"].lower()
            ]

        # Calculate pagination
        total = len(products)
        start = (page - 1) * limit
        end = start + limit
        paginated = products[start:end]

        return {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit,  # Ceiling division
            "products": paginated
        }
```

### Test Basic Query Parameters

**Default (page 1, limit 10):**
```bash
curl http://localhost:7376/products
```

**Expected Output:**
```json
{
  "page": 1,
  "limit": 10,
  "total": 8,
  "pages": 1,
  "products": [...]
}
```

**Custom pagination:**
```bash
curl "http://localhost:7376/products?page=2&limit=3"
```

**Expected Output:**
```json
{
  "page": 2,
  "limit": 3,
  "total": 8,
  "pages": 3,
  "products": [
    {"id": 4, "name": "Chair", ...},
    {"id": 5, "name": "Monitor", ...},
    {"id": 6, "name": "Keyboard", ...}
  ]
}
```

**Search filtering:**
```bash
curl "http://localhost:7376/products?search=elec"
```

**Expected Output:**
```json
{
  "page": 1,
  "limit": 10,
  "total": 5,
  "pages": 1,
  "products": [
    {"id": 1, "name": "Laptop", "category": "Electronics"},
    {"id": 2, "name": "Mouse", "category": "Electronics"},
    {"id": 5, "name": "Monitor", "category": "Electronics"},
    {"id": 6, "name": "Keyboard", "category": "Electronics"},
    {"id": 8, "name": "Headphones", "category": "Electronics"}
  ]
}
```

`★ Insight ─────────────────────────────────────`
**Validation in Query Parameters**: Notice how we used `ge=1` (greater than or equal to 1) for `page` and `le=100` (less than or equal to 100) for `limit`. FastAPI automatically validates these constraints and returns clear 422 errors if violated - no manual validation needed in your code!
`─────────────────────────────────────────────────`

---

## Step 3: Multiple Query Parameters

Add filtering and sorting capabilities:

```python
class ProductRoutes(RouteBase):
    def get(
        self,
        page: int = Query(default=1, ge=1),
        limit: int = Query(default=10, ge=1, le=100),
        search: Optional[str] = Query(default=None),
        category: Optional[str] = Query(default=None, description="Filter by category"),
        min_price: Optional[float] = Query(default=None, ge=0, description="Minimum price"),
        max_price: Optional[float] = Query(default=None, ge=0, description="Maximum price"),
        sort_by: str = Query(default="id", description="Field to sort by"),
        order: str = Query(default="asc", regex="^(asc|desc)$", description="Sort order")
    ):
        """
        Get products with advanced filtering and sorting.

        - **category**: Filter by category (Electronics, Furniture)
        - **min_price**: Minimum price filter
        - **max_price**: Maximum price filter
        - **sort_by**: Field to sort (id, name, price)
        - **order**: asc or desc
        """
        products = [
            {"id": 1, "name": "Laptop", "price": 999.99, "category": "Electronics"},
            {"id": 2, "name": "Mouse", "price": 29.99, "category": "Electronics"},
            {"id": 3, "name": "Desk", "price": 299.99, "category": "Furniture"},
            {"id": 4, "name": "Chair", "price": 199.99, "category": "Furniture"},
            {"id": 5, "name": "Monitor", "price": 399.99, "category": "Electronics"},
        ]

        # Apply filters
        if category:
            products = [p for p in products if p["category"] == category]
        if min_price is not None:
            products = [p for p in products if p["price"] >= min_price]
        if max_price is not None:
            products = [p for p in products if p["price"] <= max_price]

        # Apply sorting
        reverse = order == "desc"
        if sort_by in ["id", "price"]:
            products.sort(key=lambda x: x[sort_by], reverse=reverse)
        elif sort_by == "name":
            products.sort(key=lambda x: x["name"].lower(), reverse=reverse)

        # Paginate
        total = len(products)
        start = (page - 1) * limit
        end = start + limit
        paginated = products[start:end]

        return {
            "filters": {
                "category": category,
                "min_price": min_price,
                "max_price": max_price,
                "sort_by": sort_by,
                "order": order
            },
            "page": page,
            "limit": limit,
            "total": total,
            "products": paginated
        }
```

### Test Multiple Query Parameters

**Filter by category:**
```bash
curl "http://localhost:7376/products?category=Electronics"
```

**Filter by price range:**
```bash
curl "http://localhost:7376/products?min_price=100&max_price=400"
```

**Sort by price descending:**
```bash
curl "http://localhost:7376/products?sort_by=price&order=desc"
```

**Combine multiple filters:**
```bash
curl "http://localhost:7376/products?category=Electronics&min_price=50&max_price=500&sort_by=price&order=asc"
```

**Expected Output:**
```json
{
  "filters": {
    "category": "Electronics",
    "min_price": 50.0,
    "max_price": 500.0,
    "sort_by": "price",
    "order": "asc"
  },
  "page": 1,
  "limit": 10,
  "total": 3,
  "products": [
    {"id": 2, "name": "Mouse", "price": 29.99, "category": "Electronics"},
    {"id": 5, "name": "Monitor", "price": 399.99, "category": "Electronics"}
  ]
}
```

---

## Step 4: Boolean Query Parameters

Boolean parameters are useful for toggles and flags:

```python
from reroute import RouteBase
from reroute.params import Query

class ProductRoutes(RouteBase):
    def get(
        self,
        page: int = Query(default=1, ge=1),
        limit: int = Query(default=10, ge=1, le=100),
        available_only: bool = Query(default=False, description="Show only available items"),
        featured: bool = Query(default=False, description="Show only featured items"),
        verbose: bool = Query(default=False, description="Include extra details")
    ):
        """
        Get products with boolean filters.

        - **available_only**: Only show in-stock items
        - **featured**: Only show featured items
        - **verbose**: Include additional metadata
        """
        products = [
            {"id": 1, "name": "Laptop", "available": True, "featured": True},
            {"id": 2, "name": "Mouse", "available": True, "featured": False},
            {"id": 3, "name": "Desk", "available": False, "featured": True},
        ]

        # Apply boolean filters
        if available_only:
            products = [p for p in products if p["available"]]
        if featured:
            products = [p for p in products if p["featured"]]

        # Add verbose details if requested
        if verbose:
            for p in products:
                p["meta"] = {
                    "timestamp": "2025-01-01T00:00:00Z",
                    "version": "1.0"
                }

        return {
            "available_only": available_only,
            "featured": featured,
            "verbose": verbose,
            "count": len(products),
            "products": products
        }
```

### Test Boolean Parameters

**Boolean values are automatically parsed:**
```bash
# True values: 1, true, yes, on
curl "http://localhost:7376/products?available_only=true"

# False values: 0, false, no, off
curl "http://localhost:7376/products?featured=no"

# Multiple boolean flags
curl "http://localhost:7376/products?available_only=1&verbose=yes"
```

**Expected Output:**
```json
{
  "available_only": true,
  "featured": false,
  "verbose": true,
  "count": 2,
  "products": [
    {
      "id": 1,
      "name": "Laptop",
      "available": true,
      "featured": true,
      "meta": {"timestamp": "2025-01-01T00:00:00Z", "version": "1.0"}
    },
    {
      "id": 2,
      "name": "Mouse",
      "available": true,
      "featured": false,
      "meta": {"timestamp": "2025-01-01T00:00:00Z", "version": "1.0"}
    }
  ]
}
```

---

## Step 5: List Query Parameters

Accept multiple values for a single parameter (e.g., multiple categories):

```python
from typing import List
from reroute import RouteBase
from reroute.params import Query

class ProductRoutes(RouteBase):
    def get(
        self,
        categories: List[str] = Query(default=[], description="List of categories")
    ):
        """
        Get products by multiple categories.

        - **categories**: Comma-separated list or repeat parameter

        Examples:
            ?categories=Electronics&categories=Furniture
            ?categories=Electronics,Furniture
        """
        products = [
            {"id": 1, "name": "Laptop", "category": "Electronics"},
            {"id": 2, "name": "Desk", "category": "Furniture"},
            {"id": 3, "name": "Mouse", "category": "Electronics"},
            {"id": 4, "name": "Chair", "category": "Furniture"},
        ]

        # Filter by multiple categories
        if categories:
            products = [p for p in products if p["category"] in categories]

        return {
            "categories": categories,
            "count": len(products),
            "products": products
        }
```

### Test List Parameters

**Multiple values with repeated parameter:**
```bash
curl "http://localhost:7376/products?categories=Electronics&categories=Furniture"
```

**Or comma-separated:**
```bash
curl "http://localhost:7376/products?categories=Electronics,Furniture"
```

**Expected Output:**
```json
{
  "categories": ["Electronics", "Furniture"],
  "count": 4,
  "products": [...]
}
```

---

## Step 6: Date and Time Query Parameters

Work with dates for filtering by time periods:

```python
from datetime import datetime, date
from typing import Optional
from reroute import RouteBase
from reroute.params import Query

class EventRoutes(RouteBase):
    """Event listing with date filtering."""

    def get(
        self,
        start_date: Optional[date] = Query(
            default=None,
            description="Filter events from this date (YYYY-MM-DD)"
        ),
        end_date: Optional[date] = Query(
            default=None,
            description="Filter events until this date (YYYY-MM-DD)"
        )
    ):
        """
        Get events within date range.

        - **start_date**: Only events on or after this date
        - **end_date**: Only events on or before this date
        """
        events = [
            {"id": 1, "name": "Python Conference", "date": "2025-03-15"},
            {"id": 2, "name": "API Workshop", "date": "2025-04-20"},
            {"id": 3, "name": "Tech Meetup", "date": "2025-05-10"},
        ]

        # Convert to date objects for comparison
        events_with_dates = []
        for event in events:
            event_date = datetime.strptime(event["date"], "%Y-%m-%d").date()
            events_with_dates.append({**event, "date_obj": event_date})

        # Apply date filters
        if start_date:
            events_with_dates = [
                e for e in events_with_dates
                if e["date_obj"] >= start_date
            ]
        if end_date:
            events_with_dates = [
                e for e in events_with_dates
                if e["date_obj"] <= end_date
            ]

        # Remove internal date_obj
        result = [
            {"id": e["id"], "name": e["name"], "date": e["date"]}
            for e in events_with_dates
        ]

        return {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "count": len(result),
            "events": result
        }
```

### Test Date Parameters

**Filter by date range:**
```bash
curl "http://localhost:7376/events?start_date=2025-03-01&end_date=2025-04-30"
```

**Expected Output:**
```json
{
  "start_date": "2025-03-01",
  "end_date": "2025-04-30",
  "count": 2,
  "events": [
    {"id": 1, "name": "Python Conference", "date": "2025-03-15"},
    {"id": 2, "name": "API Workshop", "date": "2025-04-20"}
  ]
}
```

**Invalid date format returns 422:**
```bash
curl "http://localhost:7376/events?start_date=invalid-date"
```

---

## Common Query Parameter Patterns

### Pattern 1: Pagination

```python
def get(
    self,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100)
):
    start = (page - 1) * per_page
    end = start + per_page

    return {
        "page": page,
        "per_page": per_page,
        "total": len(items),
        "data": items[start:end],
        "has_next": end < len(items),
        "has_prev": page > 1
    }
```

### Pattern 2: Search with Pagination

```python
def get(
    self,
    q: Optional[str] = Query(None, min_length=2, description="Search query"),
    page: int = Query(1, ge=1)
):
    # First filter, then paginate
    results = search(q) if q else all_items
    paginated = paginate(results, page)

    return {
        "query": q,
        "page": page,
        "total_results": len(results),
        "results": paginated
    }
```

### Pattern 3: Fields Selection

```python
from typing import List, Set

def get(
    self,
    fields: Set[str] = Query({"id", "name"}, description="Fields to return")
):
    """
    Return only specified fields.

    Example: ?fields=id,name,price
    """
    items = [{"id": 1, "name": "Item", "price": 10, "description": "..."}]

    # Filter fields
    filtered = [{k: v for k, v in item.items() if k in fields} for item in items]

    return {"fields": list(fields), "items": filtered}
```

### Pattern 4: Sorting

```python
def get(
    self,
    sort: str = Query("id", description="Field to sort by"),
    order: str = Query("asc", regex="^(asc|desc)$")
):
    items = get_items()

    # Validate sort field
    valid_fields = {"id", "name", "created_at"}
    if sort not in valid_fields:
        raise HTTPException(400, f"Invalid sort field. Valid: {valid_fields}")

    # Sort
    reverse = order == "desc"
    items.sort(key=lambda x: x[sort], reverse=reverse)

    return {"sort": sort, "order": order, "items": items}
```

---

## Query Parameter Validation

### Required Query Parameters

Make a parameter required by omitting `default`:

```python
def get(
    self,
    search: str = Query(..., min_length=2, description="Search query (required)")
):
    # search is required - will return 422 if missing
    return {"query": search}
```

### Type Validation

FastAPI automatically validates types:

```python
def get(
    self,
    count: int = Query(...),  # Must be integer
    price: float = Query(...),  # Must be number
    active: bool = Query(...),  # Must be boolean
    tags: List[str] = Query(...)  # Must be list of strings
):
    pass
```

### Custom Validation with Regex

```python
def get(
    self,
    sku: str = Query(
        ...,
        regex=r"^[A-Z]{2}-\d{4}$",  # XX-1234 format
        description="Stock Keeping Unit (e.g., AB-1234)"
    )
):
    return {"sku": sku}
```

### Range Validation

```python
def get(
    self,
    age: int = Query(..., ge=0, le=150),  # 0-150
    rating: float = Query(..., gt=0, lt=5),  # 0 < rating < 5
    name: str = Query(..., min_length=2, max_length=50)  # 2-50 chars
):
    pass
```

---

## Aliases for Query Parameters

Use different names in code vs URL:

```python
def get(
    self,
    api_key: str = Query(
        ...,
        alias="api-key",  # URL uses hyphen
        description="API key"
    )
):
    """
    URL: ?api-key=secret
    Code: api_key variable
    """
    return {"key": api_key}
```

This allows Pythonic variable names (`api_key`) while using URL-friendly names (`api-key`).

---

## Deprecated Query Parameters

Mark parameters as deprecated while maintaining backward compatibility:

```python
def get(
    self,
    page: int = Query(default=1, ge=1),
    new_param: str = Query(default="default", description="Use this instead"),
    old_param: str = Query(
        default=None,
        deprecated=True,
        description="[DEPRECATED] Use new_param instead"
    )
):
    """
    old_param is shown as deprecated in Swagger UI.
    Still works for backward compatibility.
    """
    if old_param:
        # Handle old clients
        new_param = old_param

    return {"param": new_param}
```

---

## Troubleshooting

### Problem 1: Query Parameter Always None

**Symptom:** Parameter value is None despite being provided

**Cause:** Mismatch in parameter name

**Solution:**
```python
# URL: ?search_term=python
# Wrong:
def get(self, search: str = Query(...)):  # Different name

# Correct:
def get(self, search_term: str = Query(...)):  # Same name
```

### Problem 2: Type Conversion Error

**Symptom:** 422 error with "type=integer_parsing"

**Cause:** Sending non-numeric value to integer parameter

**Solution:**
```bash
# Wrong:
curl "http://localhost:7376/products?page=two"

# Correct:
curl "http://localhost:7376/products?page=2"
```

### Problem 3: Boolean Parameter Not Working

**Symptom:** Boolean always False

**Cause:** Invalid boolean value

**Solution:** Use valid boolean values:
```
True:  1, true, yes, on
False: 0, false, no, off, (empty)
```

### Problem 4: List Parameter Empty

**Symptom:** List parameter always `[]`

**Cause:** Not repeating parameter or using comma separator

**Solution:**
```bash
# Wrong:
curl "http://localhost:7376/products?categories=Electronics,Furniture"

# Correct (repeat parameter):
curl "http://localhost:7376/products?categories=Electronics&categories=Furniture"

# Or use Query with custom parsing
```

---

## Best Practices

### 1. Use Descriptive Parameter Names

```python
# Good
def get(self, page_size: int = Query(20)):
    pass

# Avoid
def get(self, n: int = Query(20)):
    pass
```

### 2. Provide Default Values

```python
# Good - has sensible defaults
def get(self, page: int = Query(1), per_page: int = Query(20)):
    pass

# Less user-friendly - no defaults
def get(self, page: int = Query(...), per_page: int = Query(...)):
    pass
```

### 3. Add Validation Constraints

```python
# Good - prevents invalid input
def get(self, age: int = Query(..., ge=0, le=150)):
    pass

# Less safe - no validation
def get(self, age: int = Query(...)):
    pass
```

### 4. Use Aliases for URL-Friendly Names

```python
# Good - URL uses hyphens, code uses underscores
def get(self, api_key: str = Query(..., alias="api-key")):
    pass

# URL: ?api-key=secret
# Code: api_key variable
```

### 5. Document Required vs Optional

```python
# Good - clear what's optional
def get(
    self,
    required_param: str = Query(...),  # Required
    optional_param: str = Query(default="default")  # Optional
):
    pass
```

---

## Summary

In this tutorial, you learned:

- **Query Parameters**: Optional URL parameters after `?`
- **Multiple Parameters**: Combine filters, sorting, pagination
- **Type Validation**: Automatic type checking with type hints
- **Validation Constraints**: Use `ge`, `le`, `min_length`, `max_length`, `regex`
- **Boolean Parameters**: Toggle flags and options
- **List Parameters**: Accept multiple values
- **Date Parameters**: Filter by date ranges
- **Common Patterns**: Pagination, filtering, sorting, field selection
- **Aliases**: Pythonic names in code, URL-friendly names in API
- **Deprecation**: Mark old parameters as deprecated

**Key takeaways:**
- Query parameters modify GET requests without changing URL path
- Use for filtering, sorting, pagination, search
- Type hints enable automatic validation
- Provide sensible defaults for better UX
- Document parameters with descriptions for Swagger UI

---

## Next Steps

**Continue learning:**
- [CRUD Application](../medium/crud-app.md) - Build complete CRUD app
- [Decorators](../medium/decorators-intro.md) - Add rate limiting and caching
- [Configuration Guide](../../guides/configuration.md) - Configure your REROUTE app

**Practice ideas:**
- Build a blog API with filtering, sorting, and pagination
- Create e-commerce product catalog with advanced filters
- Implement search with autocomplete suggestions

---

**Ready to build a complete CRUD application?** Continue to [CRUD App](../medium/crud-app.md)!
