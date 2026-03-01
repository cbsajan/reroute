# Authentication Example

Implement authentication with REROUTE.

## Secure Route

```python
from reroute import RouteBase
from reroute.params import Header
from fastapi import HTTPException

class SecureRoutes(RouteBase):
    tag = "Secure Endpoints"

    def before_request(self):
        """Check authentication before each request"""
        # Authentication is handled via Header parameter in route methods
        return None

    def verify_token(self, token: str) -> bool:
        """Verify JWT token"""
        # Implementation here
        return token == "valid_token"

    def delete(self, authorization: str = Header(None)):
        """Admin-only endpoint - requires valid token"""
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing authentication")

        token = authorization.replace("Bearer ", "")
        if not self.verify_token(token):
            raise HTTPException(status_code=401, detail="Invalid token")

        # Additional admin role check would go here
        return {"deleted": True}

    def get(self, authorization: str = Header(None)):
        """Authenticated endpoint"""
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing authentication")

        token = authorization.replace("Bearer ", "")
        if not self.verify_token(token):
            raise HTTPException(status_code=401, detail="Invalid token")

        return {"data": "secure"}
```

## JWT Example

```python
import jwt
from datetime import datetime, timedelta

class AuthRoutes(RouteBase):
    def post(self):
        """Login endpoint"""
        # Verify credentials
        token = jwt.encode({
            "user_id": 1,
            "exp": datetime.utcnow() + timedelta(hours=24)
        }, "secret_key", algorithm="HS256")

        return {"token": token}
```

## Usage

```bash
# Login
curl -X POST http://localhost:8000/auth

# Access secure endpoint
curl -H "Authorization: Bearer <token>" http://localhost:8000/secure
```
