# RouteBase API

Base class for all REROUTE routes.

## Class Definition

```python
from reroute import RouteBase

class MyRoutes(RouteBase):
    pass
```

## Class Attributes

### tag
Optional Swagger/OpenAPI tag for grouping routes.

```python
class UserRoutes(RouteBase):
    tag = "User Management"
```

## HTTP Methods

### get()
Handle GET requests.

```python
def get(self):
    return {"data": "..."}
```

### post()
Handle POST requests.

```python
def post(self):
    return {"created": True}
```

### put()
Handle PUT requests.

```python
def put(self):
    return {"updated": True}
```

### delete()
Handle DELETE requests.

```python
def delete(self):
    return {"deleted": True}
```

### patch()
Handle PATCH requests.

```python
def patch(self):
    return {"patched": True}
```

## Lifecycle Methods

### before_request()
Called before every request.

```python
def before_request(self):
    # Authentication, logging
    return None  # Continue to handler
```

### after_request(response)
Called after successful request.

```python
def after_request(self, response):
    response["timestamp"] = "..."
    return response
```

### on_error(error)
Called when an error occurs.

```python
def on_error(self, error: Exception):
    return {"error": str(error)}
```
