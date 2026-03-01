# Caching Example

Improve performance with response caching.

## Basic Caching

```python
from reroute import RouteBase
from reroute.decorators import cache

class ProductRoutes(RouteBase):
    @cache(duration=300)
    def get(self):
        """Cached for 5 minutes"""
        # Expensive operation
        products = self.fetch_from_database()
        return {"products": products}
```

## Different Cache Durations

```python
class DataRoutes(RouteBase):
    @cache(duration=60)
    def get_recent(self):
        """Cache for 1 minute"""
        return {"data": "recent"}

    @cache(duration=3600)
    def get_static(self):
        """Cache for 1 hour"""
        return {"data": "static"}
```

## Conditional Caching

```python
from reroute import RouteBase
from reroute.decorators import cache
from reroute.params import Query

class SmartCache(RouteBase):
    def __init__(self):
        super().__init__()
        self.data = {"data": "cached"}

    @cache(duration=60)
    def get(self, no_cache: bool = Query(False)):
        """Cache can be bypassed with ?no_cache=true"""
        if no_cache:
            # Bypass cache - decorator won't cache this response
            return {"data": "fresh", "cached": False}
        return {"data": "cached", "cached": True}

    def fresh_data(self):
        """Helper to fetch fresh data"""
        return {"data": "fresh from source"}
```

## Cache with Manual Control

```python
from reroute import RouteBase
from reroute.decorators import cache

class UserRoutes(RouteBase):
    def __init__(self):
        super().__init__()
        self.users = []

    @cache(duration=300)
    def get(self):
        """Cached user list"""
        return {"users": self.users}

    def post(self):
        """Creating user - cache will auto-expire after 5 minutes"""
        new_user = {"id": len(self.users) + 1, "name": "New User"}
        self.users.append(new_user)
        # Note: Cache automatically expires after duration
        # For immediate invalidation, use cache keys or external cache service
        return {"created": new_user}
```

## Testing

```bash
# First request - slow (cache miss)
time curl http://localhost:8000/products

# Second request - fast (cache hit)
time curl http://localhost:8000/products
```
