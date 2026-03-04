# Lifecycle Hooks

Control request/response flow with lifecycle methods.

## before_request

Run before every request:

```python
class MyRoutes(RouteBase):
    def before_request(self):
        # Authentication, logging, etc.
        print("Request received")
        return None  # Continue
```

## after_request

Process responses:

```python
def after_request(self, response):
    response["timestamp"] = "2024-01-15"
    return response
```

## on_error

Handle errors:

```python
def on_error(self, error):
    return {
        "error": str(error),
        "status": 500
    }
```

## Complete Example

```python
from reroute import RouteBase

class SecureRoutes(RouteBase):
    def before_request(self):
        if not self.check_auth():
            raise Unauthorized()
        return None

    def after_request(self, response):
        response["version"] = "1.0"
        return response

    def on_error(self, error):
        return {"error": str(error)}

    def get(self):
        return {"data": "secure"}
```
