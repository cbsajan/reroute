# Examples

Real-world examples and patterns for building APIs with REROUTE.

## Framework-Specific Examples

Complete end-to-end examples for each supported framework:

<div class="grid cards" markdown>

-   :material-flask: [**Flask Complete Example**](flask-example.md)

    ---

    Full Flask application with Spectree OpenAPI, validation, and best practices

-   :zap: [**FastAPI Complete Example**](fastapi-example.md)

    ---

    Async FastAPI application with background tasks, caching, and deployment guide

</div>

## Basic Examples

<div class="grid cards" markdown>

-   :material-database: [**Basic CRUD**](basic-crud.md)

    ---

    Create, Read, Update, Delete operations

-   :material-shield-account: [**Authentication**](authentication.md)

    ---

    User authentication and authorization

-   :material-speedometer: [**Rate Limiting**](rate-limiting.md)

    ---

    Protect your API with rate limits

-   :material-cached: [**Caching**](caching.md)

    ---

    Improve performance with caching

-   :material-database-outline: [**Database Integration**](database.md)

    ---

    Connect to databases with SQLAlchemy, Tortoise ORM, and more

</div>

## Patterns

### Simple API

```python
from reroute import RouteBase

class UserRoutes(RouteBase):
    def __init__(self):
        super().__init__()
        self.users = []

    def get(self):
        return {"users": self.users}

    def post(self):
        user = {"id": len(self.users) + 1}
        self.users.append(user)
        return user
```

### With Decorators

```python
from reroute import RouteBase
from reroute.decorators import rate_limit, cache

class ProductRoutes(RouteBase):
    @cache(duration=300)
    def get(self):
        # Cached for 5 minutes
        return {"products": [...]}

    @rate_limit("10/min")
    def post(self):
        # Max 10 requests per minute
        return {"created": True}
```

### With Lifecycle Hooks

```python
from reroute import RouteBase

class SecureRoutes(RouteBase):
    def before_request(self):
        # Check authentication
        if not self.is_authenticated():
            raise Unauthorized("Login required")
        return None

    def after_request(self, response):
        # Add security headers
        response["X-API-Version"] = "1.0"
        return response

    def on_error(self, error):
        # Custom error handling
        return {"error": str(error), "status": 500}
```

## Full Examples

Browse complete example applications:

- [Basic CRUD](basic-crud.md) - User management API
- [Authentication](authentication.md) - JWT authentication
- [Rate Limiting](rate-limiting.md) - API rate limiting patterns
- [Caching](caching.md) - Response caching strategies
- [Database Integration](database.md) - SQL and ORM integration (SQLAlchemy, Tortoise ORM)

## Example Repository

Check out the [examples folder](https://github.com/cbsajan/reroute/tree/main/examples) in the main repository for runnable examples.

## Community Examples

Share your examples with the community! Submit a PR to add your example to this page.
