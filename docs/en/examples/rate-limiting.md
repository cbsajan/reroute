# Rate Limiting Example

Protect your API with rate limiting.

## Basic Rate Limiting

```python
from reroute import RouteBase
from reroute.decorators import rate_limit

class APIRoutes(RouteBase):
    @rate_limit("5/min")
    def post(self):
        """Max 5 requests per minute"""
        return {"created": True}

    @rate_limit("100/hour")
    def get(self):
        """Max 100 requests per hour"""
        return {"data": "..."}
```

## Different Limits per Method

```python
class UserRoutes(RouteBase):
    @rate_limit("100/min")
    def get(self):
        """Generous limit for reads"""
        return {"users": []}

    @rate_limit("10/min")
    def post(self):
        """Stricter limit for writes"""
        return {"created": True}

    @rate_limit("3/min")
    def delete(self):
        """Very strict for deletions"""
        return {"deleted": True}
```

## How Rate Limiting Works

When a rate limit is exceeded, REROUTE automatically returns a `429 Too Many Requests` response:

```json
{
  "error": "Rate limit exceeded",
  "limit": "5/min",
  "retry_after": 42
}
```

The `@rate_limit` decorator tracks requests per IP address and returns the error response automatically - no custom error handling needed!

## Testing

```bash
# Hit endpoint multiple times
for i in {1..10}; do
    curl http://localhost:8000/api
done
```
