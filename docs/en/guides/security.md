# Security Guide

Build secure REROUTE applications with comprehensive OWASP-compliant protection out of the box.

---

## Overview

REROUTE provides **comprehensive security headers by default** with environment-specific configurations. Maximum protection in production, developer-friendly in development. This guide covers:

- **Comprehensive Security by Default**: OWASP-compliant security headers applied automatically
- **Environment-Aware Protection**: Development-friendly policies that become strict in production
- **Full Customization**: Configure all aspects through the Config class
- **Advanced Features**: CDN domains, API whitelisting, custom headers
- Input validation and sanitization
- Authentication and authorization
- SQL injection prevention
- XSS protection
- CORS configuration (using REROUTE's built-in settings)
- API security
- Secret management
- Common vulnerabilities

---

## Comprehensive Security Headers (Applied by Default)

REROUTE automatically applies these OWASP-compliant security headers in both FastAPI and Flask adapters:

### Active Headers

| Header | Environment | Value | Purpose |
|--------|------------|-------|---------|
| `Content-Security-Policy` | All | Environment-aware | Prevents XSS, data injection, mixed content |
| `X-Content-Type-Options` | All | `nosniff` | Prevents MIME-type sniffing |
| `X-Frame-Options` | All | `DENY` (Production) / `SAMEORIGIN` (Dev) | Clickjacking protection |
| `Strict-Transport-Security` | Production Only | `max-age=31536000; includeSubDomains` | HTTPS enforcement |
| `X-XSS-Protection` | All | `1; mode=block` | Legacy browser XSS filtering |
| `Referrer-Policy` | All | `strict-origin-when-cross-origin` | Privacy-focused referrer control |
| `Permissions-Policy` | All | Feature-specific | Browser feature access control |

### Environment-Specific Behavior

**Development Environment:**
- Permissive CSP with `unsafe-inline` and `unsafe-eval` for development tools
- HSTS disabled (no HTTPS in development)
- Frame options set to `SAMEORIGIN` for dev tool compatibility
- Maximum flexibility for development workflows

**Production Environment:**
- Strict CSP with no unsafe directives
- HSTS enabled with 1-year max-age and preload support
- Frame options set to `DENY` for maximum protection
- OWASP-comprehensive security configuration

### Implementation Details

**FastAPI Adapter:**
```python
# reroute/adapters/fastapi.py - SecurityHeadersMiddleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, security_config: SecurityHeadersConfig):
        super().__init__(app)
        self.security_config = security_config

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Apply all OWASP-compliant security headers
        security_headers = self.security_config.get_security_headers()
        for header_name, header_value in security_headers.items():
            response.headers[header_name] = header_value
        return response
```

**Flask Adapter:**
```python
# reroute/adapters/flask.py - FlaskSecurityHeadersMiddleware
class FlaskSecurityHeadersMiddleware:
    def __init__(self, app, security_config: SecurityHeadersConfig):
        self.app = app
        self.security_config = security_config
        self.app.after_request(self._add_security_headers)

    def _add_security_headers(self, response):
        security_headers = self.security_config.get_security_headers()
        for header_name, header_value in security_headers.items():
            response.headers[header_name] = header_value
        return response
```

### Configuration

**Basic Configuration (Automatic):**
```python
from reroute import Config

# Security headers are applied automatically - no configuration needed
class MyAppConfig(Config):
    # All security headers work out of the box
    pass
```

**Advanced Configuration:**
```python
class ProductionConfig(Config):
    # CDN domains for your assets
    SECURITY_CDN_DOMAINS = ["https://cdn.example.com", "https://assets.example.com"]

    # API endpoints for your backend
    SECURITY_API_DOMAINS = ["https://api.example.com"]

    # Custom security headers
    SECURITY_CUSTOM_HEADERS = {
        "X-Custom-Security": "value",
        "X-API-Version": "v1"
    }

    # Strict CSP in production
    SECURITY_X_FRAME_OPTIONS = "DENY"
    SECURITY_HSTS_PRELOAD = True
```

### Customization Examples

**Single Page Application (SPA):**
```python
# Using the factory for SPA-specific configuration
from reroute.security import SecurityHeadersFactory

config = SecurityHeadersFactory.create_for_single_page_app()
# Automatically configured for React/Vue/Angular applications
```

```python
# FastAPI middleware example
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS (if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Restrict origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    # Additional security headers for production
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

```python
# Flask example
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)

# Add CORS (if needed)
CORS(app, origins=["https://yourdomain.com"])

@app.after_request
def add_security_headers(response):
    # Additional security headers for production
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

!!! note "Add Security When Needed"
    REROUTE provides the foundation - you add security based on your specific requirements. This approach ensures:
    - Development workflows aren't blocked by restrictive policies
    - Production security is tailored to your application's needs
    - You understand exactly what security measures are in place

---

## Additional Security Features Available

While REROUTE provides only basic security by default, you can enhance your application security with these available features:

## Built-in Security Features (v0.2.0+)

REROUTE includes enterprise-grade security features that protect your applications by default.

### 1. Column-Validated Database Queries

The `Model.get_all()` method includes built-in column validation for the `order_by` parameter, ensuring only valid database columns are accepted:

```python
from reroute.db.models import Model
from sqlalchemy import Column, String

class User(Model):
    __tablename__ = 'users'
    name = Column(String(100))
    email = Column(String(100))

# Valid column names work seamlessly
users = User.get_all(session, order_by='name')  # Works
users = User.get_all(session, order_by='created_at')  # Works

# Invalid column names are rejected with helpful errors
users = User.get_all(session, order_by='invalid_column')  # Raises ValueError
```

The error message provides developer guidance:
```
ValueError: Invalid order_by column: 'invalid_column'.
Valid columns are: created_at, email, id, name, updated_at
```

### 2. Input-Validated CLI Commands

All CLI commands include input validation to ensure safe operation:

```bash
# Database migration commands accept validated inputs
reroute db downgrade --steps 1  # Valid (integer 1-100)
reroute db downgrade --steps 5  # Valid

# Invalid inputs are rejected
reroute db downgrade --steps 0    # Error: must be >= 1
reroute db downgrade --steps 101  # Error: max 100 steps
```

### 3. Bounded Cache with LRU Eviction

The `@cache` decorator includes automatic memory management with configurable limits:

```python
from reroute.decorators import cache

@cache(duration=300)
def expensive_operation(key):
    return perform_calculation(key)
```

**Built-in cache management:**
- Maximum size: 1000 entries (prevents unbounded growth)
- Eviction strategy: LRU (Least Recently Used)
- Background cleanup: Every 60 seconds
- Full observability: Errors are logged for monitoring

### 4. Fail-Safe Authorization with @requires

The `@requires` decorator implements a fail-safe authorization pattern - access is denied by default unless explicitly granted:

```python
from reroute.decorators import requires

# Authentication check (returns 401 if fails)
@requires(check_func=lambda self: self.is_authenticated())
def get(self):
    return {"data": "protected"}

# Role-based authorization (returns 403 if fails)
def is_admin(self):
    return self.current_user.get('role') == 'admin'

@requires("admin", check_func=is_admin)
def delete_user(self, user_id: int):
    return {"deleted": True}
```

**Authorization response codes:**
- `401 Unauthorized` - Authentication failed
- `403 Forbidden` - Role/permission check failed
- `500 Internal Server Error` - Misconfigured decorator (fail-safe)

!!! important "Explicit Authorization Required"
    When specifying roles, you must provide a `check_func` that implements your authorization logic. This ensures security is explicitly defined in your application.

---

## Security Logging (OWASP A09)

REROUTE v0.2.0 includes a comprehensive security logging system for monitoring and SIEM integration.

### SecurityLogger

The `SecurityLogger` provides structured JSON logging for security-relevant events:

```python
from reroute.logging import security_logger

# Log authentication events
security_logger.log_auth_success(user="john@example.com", ip_address="192.168.1.1")
security_logger.log_auth_failure(user="unknown", reason="Invalid password", ip_address="192.168.1.1")

# Log authorization events
security_logger.log_authz_failure(
    user="john@example.com",
    resource="/admin/users",
    required_roles=["admin"],
    ip_address="192.168.1.1"
)

# Log rate limiting
security_logger.log_rate_limit(endpoint="/api/login", ip_address="10.0.0.1", limit="5/min")

# Log validation failures
security_logger.log_validation_failure(endpoint="/api/users", errors=["Invalid email format"])

# Log suspicious activity
security_logger.log_suspicious(description="Unusual request pattern detected", ip_address="10.0.0.1")
```

### Security Event Types

| Event Type | Severity | Use Case |
|------------|----------|----------|
| `AUTH_SUCCESS` | INFO | Successful login |
| `AUTH_FAILURE` | MEDIUM | Failed login attempt |
| `AUTHZ_FAILURE` | MEDIUM | Permission denied |
| `RATE_LIMIT_EXCEEDED` | MEDIUM | Rate limit hit |
| `VALIDATION_FAILURE` | LOW | Invalid input |
| `SUSPICIOUS_REQUEST` | HIGH | Anomaly detected |

### Automatic Sensitive Data Redaction

The security logger automatically redacts sensitive fields from logs:

```python
# These fields are automatically redacted
SENSITIVE_FIELDS = {
    'password', 'secret', 'token', 'api_key', 'credit_card',
    'ssn', 'private_key', 'connection_string', ...
}

# Example: password is automatically redacted
security_logger.log_auth_failure(user="john", password="secret123")
# Output: {"user": "john", "password": "[REDACTED]", ...}
```

### JSON Output for SIEM Integration

All security events are logged in JSON format for easy integration with security tools:

```json
{
  "timestamp": "2025-11-28T10:30:00.000Z",
  "event_type": "auth_failure",
  "severity": "MEDIUM",
  "message": "Authentication failed: Invalid password",
  "details": {
    "user": "john@example.com",
    "ip_address": "192.168.1.100",
    "reason": "Invalid password"
  }
}
```

### Integration with Decorators

Security logging is automatically integrated with REROUTE decorators:

```python
from reroute.decorators import rate_limit, requires

# Rate limit events are automatically logged
@rate_limit("5/min", per_ip=True)
def post(self):
    return {"created": True}
# When limit exceeded: security_logger.log_rate_limit() is called

# Authorization failures are automatically logged
@requires("admin", check_func=is_admin)
def delete(self):
    return {"deleted": True}
# When denied: security_logger.log_authz_failure() is called
```

---

## Input Validation

### Always Validate User Input

❌ **Dangerous**:
```python
from reroute import RouteBase

class UserRoutes(RouteBase):
    def get(self, user_id: int):
        # Direct database query - SQL injection risk!
        query = f"SELECT * FROM users WHERE id = {user_id}"
        result = db.execute(query)
        return result
```

✅ **Safe**:
```python
from reroute import RouteBase
from reroute.params import Query
from pydantic import BaseModel, Field, field_validator

class UserQuery(BaseModel):
    user_id: int = Field(..., ge=1, le=999999)

    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if v < 0:
            raise ValueError('User ID must be positive')
        return v

class UserRoutes(RouteBase):
    def get(self, query: UserQuery = Query()):
        # Parameterized query - safe from SQL injection
        result = db.execute(
            "SELECT * FROM users WHERE id = :id",
            {"id": query.user_id}
        )
        return result
```

### Pydantic Validation

```python
from pydantic import BaseModel, Field, field_validator, EmailStr
from reroute import RouteBase
from reroute.params import Body

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    email: EmailStr
    password: str = Field(..., min_length=8)
    age: int = Field(..., ge=13, le=120)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain number')
        return v

class UserRoutes(RouteBase):
    def post(self, user: UserCreate = Body()):
        # Input is validated automatically
        hashed_password = self.hash_password(user.password)
        return self.create_user(user.username, user.email, hashed_password)
```

---

## SQL Injection Prevention

### Use Parameterized Queries

❌ **Vulnerable**:
```python
def search(self, query: str):
    # NEVER do this!
    sql = f"SELECT * FROM products WHERE name LIKE '%{query}%'"
    return db.execute(sql)
```

✅ **Safe - SQLAlchemy**:
```python
from sqlalchemy import text

def search(self, query: str):
    # Parameterized query
    sql = text("SELECT * FROM products WHERE name LIKE :query")
    return db.execute(sql, {"query": f"%{query}%"})
```

✅ **Safe - Raw SQL with psycopg2**:
```python
import psycopg2

def search(self, query: str):
    cursor = conn.cursor()
    # Parameterized query
    cursor.execute(
        "SELECT * FROM products WHERE name LIKE %s",
        (f"%{query}%",)
    )
    return cursor.fetchall()
```

### ORM Best Practices

```python
from sqlalchemy.orm import Session
from models import User

class UserRoutes(RouteBase):
    def get(self, username: str, db: Session):
        # ORM handles parameterization
        user = db.query(User).filter(User.username == username).first()
        return user
```

---

## XSS (Cross-Site Scripting) Prevention

### Sanitize HTML Input

```python
import bleach
from reroute import RouteBase
from reroute.params import Body

ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'a']
ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}

class PostRoutes(RouteBase):
    def post(self, content: str = Body()):
        # Sanitize HTML content
        clean_content = bleach.clean(
            content,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            strip=True
        )

        return self.create_post(clean_content)
```

### Escape User Content

```python
import html

class CommentRoutes(RouteBase):
    def post(self, comment: str = Body()):
        # Escape HTML entities
        safe_comment = html.escape(comment)
        return self.create_comment(safe_comment)
```

---

## CORS Configuration

### Using REROUTE's Built-in CORS Settings

REROUTE provides built-in CORS configuration through the `Config` class.

❌ **Insecure Default**:
```python
# config.py
from reroute import Config

class AppConfig(Config):
    # Default CORS settings - INSECURE for production!
    ENABLE_CORS = True
    CORS_ALLOW_ORIGINS = ["*"]  # Allows ALL origins!
    CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    CORS_ALLOW_HEADERS = ["*"]
    CORS_ALLOW_CREDENTIALS = False
```

✅ **Secure Production Configuration**:
```python
# config.py
from reroute import Config

class AppConfig(Config):
    # Secure CORS for production
    ENABLE_CORS = True
    CORS_ALLOW_ORIGINS = [
        "https://yourdomain.com",
        "https://app.yourdomain.com"
    ]
    CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE"]
    CORS_ALLOW_HEADERS = ["Authorization", "Content-Type"]
    CORS_ALLOW_CREDENTIALS = True  # Allow cookies/auth headers
```

### Environment-Specific CORS

```python
# config.py
from reroute import Config
import os

class AppConfig(Config):
    # Load CORS origins from environment variable
    CORS_ALLOW_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000"  # Default for development
    ).split(",")

    CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE"]
    CORS_ALLOW_HEADERS = ["Authorization", "Content-Type"]
    CORS_ALLOW_CREDENTIALS = True
```

### .env File

```bash
# .env.production
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# .env.development
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

### Disable CORS (Internal APIs)

```python
class InternalAPIConfig(Config):
    # Disable CORS for internal-only APIs
    ENABLE_CORS = False
```

!!! warning "Security Risk"
    **NEVER use `CORS_ALLOW_ORIGINS = ["*"]` with `CORS_ALLOW_CREDENTIALS = True` in production!**
    This allows any website to make authenticated requests to your API.

---

## Authentication

### JWT Authentication

```python
import jwt
from datetime import datetime, timedelta
from reroute import RouteBase
from reroute.params import Header
from fastapi import HTTPException

SECRET_KEY = "your-secret-key"  # Load from environment!
ALGORITHM = "HS256"

class AuthRoutes(RouteBase):
    def post(self, username: str, password: str):
        """Login endpoint."""
        # Verify credentials
        user = self.authenticate_user(username, password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Create JWT token
        payload = {
            "user_id": user.id,
            "username": user.username,
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        return {"access_token": token, "token_type": "bearer"}

class ProtectedRoutes(RouteBase):
    """Routes requiring authentication."""

    def before_request(self):
        """Verify JWT token before processing request."""
        token = self.get_auth_token()

        if not token:
            return {"error": "Missing authentication token"}, 401

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            self.current_user = payload
            return None  # Continue to handler

        except jwt.ExpiredSignatureError:
            return {"error": "Token expired"}, 401

        except jwt.InvalidTokenError:
            return {"error": "Invalid token"}, 401

    def get_auth_token(self):
        """Extract token from Authorization header."""
        from flask import request
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            return auth_header[7:]
        return None

    def get(self):
        # Access authenticated user
        return {"user": self.current_user}
```

### Password Hashing

```python
import bcrypt

class UserRoutes(RouteBase):
    def post(self, username: str, password: str):
        # Hash password before storing
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

        user = self.create_user(username, hashed.decode('utf-8'))
        return {"id": user.id, "username": user.username}

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
```

---

## Authorization

### Role-Based Access Control (RBAC)

```python
from functools import wraps
from fastapi import HTTPException

def require_role(role: str):
    """Decorator to require specific role."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, 'current_user'):
                raise HTTPException(status_code=401, detail="Not authenticated")

            user_roles = self.current_user.get('roles', [])
            if role not in user_roles:
                raise HTTPException(
                    status_code=403,
                    detail=f"Requires {role} role"
                )

            return func(self, *args, **kwargs)
        return wrapper
    return decorator

class AdminRoutes(RouteBase):
    @require_role('admin')
    def delete(self, user_id: int):
        """Only admins can delete users."""
        self.delete_user(user_id)
        return {"deleted": True}

    @require_role('moderator')
    def put(self, user_id: int, banned: bool):
        """Moderators can ban users."""
        self.update_user(user_id, banned=banned)
        return {"updated": True}
```

### Permission Checks

```python
class ResourceRoutes(RouteBase):
    def get(self, resource_id: int):
        resource = self.find_resource(resource_id)

        # Check ownership
        if resource.owner_id != self.current_user['user_id']:
            raise HTTPException(status_code=403, detail="Access denied")

        return resource

    def put(self, resource_id: int, data: dict):
        resource = self.find_resource(resource_id)

        # Check if user can edit
        if not self.can_user_edit(self.current_user, resource):
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to edit this resource"
            )

        return self.update_resource(resource_id, data)
```

---

## API Security

### Rate Limiting

Use REROUTE's built-in `@rate_limit` decorator:

```python
from reroute.decorators import rate_limit

class APIRoutes(RouteBase):
    @rate_limit("100/hour")
    def get(self):
        """Limit to 100 requests per hour per IP."""
        return {"data": "..."}

    @rate_limit("5/min")
    def post(self):
        """Limit POST to 5 requests per minute."""
        return {"created": True}
```

### API Key Authentication

```python
import secrets

class APIKeyRoutes(RouteBase):
    VALID_API_KEYS = {
        "key_prod_xxx": {"name": "Production App", "rate_limit": "1000/hour"},
        "key_dev_yyy": {"name": "Development", "rate_limit": "100/hour"}
    }

    def before_request(self):
        """Verify API key."""
        api_key = self.get_api_key()

        if not api_key or api_key not in self.VALID_API_KEYS:
            return {"error": "Invalid API key"}, 401

        # Store API key info for rate limiting
        self.api_key_info = self.VALID_API_KEYS[api_key]
        return None

    def get_api_key(self):
        from flask import request
        return request.headers.get('X-API-Key')

    def get(self):
        return {
            "data": "...",
            "api_key": self.api_key_info['name']
        }
```

### Generate Secure API Keys

```python
def generate_api_key() -> str:
    """Generate cryptographically secure API key."""
    return f"key_{secrets.token_urlsafe(32)}"
```

---

## Secret Management

### Environment Variables

❌ **Never hardcode secrets**:
```python
SECRET_KEY = "my-secret-key-123"  # NEVER!
DATABASE_URL = "postgresql://user:pass@localhost/db"  # NEVER!
```

✅ **Use environment variables**:
```python
import os

SECRET_KEY = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable not set")
```

### Using python-dotenv

```python
# .env file (DO NOT commit to git!)
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost/mydb
JWT_SECRET=another-secret-key

# main.py
from dotenv import load_dotenv
import os

load_dotenv()  # Load .env file

SECRET_KEY = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
```

### .gitignore

```
# .gitignore
.env
.env.local
.env.production
*.key
*.pem
secrets/
```

---

## HTTPS/TLS

### Force HTTPS in Production

```python
from fastapi import Request
from fastapi.responses import RedirectResponse
import os

async def https_redirect_middleware(request: Request, call_next):
    """Redirect HTTP to HTTPS in production."""
    if os.getenv("ENV") == "production":
        if request.url.scheme != "https":
            url = request.url.replace(scheme="https")
            return RedirectResponse(url, status_code=301)

    return await call_next(request)

app.middleware("http")(https_redirect_middleware)
```

### HSTS Headers

```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    # Strict-Transport-Security
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # Additional security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    return response
```

---

## Common Vulnerabilities

### 1. Mass Assignment

❌ **Vulnerable**:
```python
def put(self, user_id: int, data: dict):
    # User can set any field, including is_admin!
    user = User.query.get(user_id)
    for key, value in data.items():
        setattr(user, key, value)
    db.session.commit()
```

✅ **Safe**:
```python
from pydantic import BaseModel

class UserUpdate(BaseModel):
    username: str
    email: str
    # is_admin is NOT in this model

def put(self, user_id: int, data: UserUpdate):
    user = User.query.get(user_id)
    user.username = data.username
    user.email = data.email
    # is_admin cannot be modified
    db.session.commit()
```

### 2. Insecure Direct Object References (IDOR)

❌ **Vulnerable**:
```python
def get(self, order_id: int):
    # Any user can access any order!
    return Order.query.get(order_id)
```

✅ **Safe**:
```python
def get(self, order_id: int):
    order = Order.query.get(order_id)

    # Verify ownership
    if order.user_id != self.current_user['user_id']:
        raise HTTPException(status_code=403, detail="Access denied")

    return order
```

### 3. Server-Side Request Forgery (SSRF)

❌ **Vulnerable**:
```python
import requests

def fetch(self, url: str):
    # Can access internal services!
    response = requests.get(url)
    return response.text
```

✅ **Safe**:
```python
import requests
from urllib.parse import urlparse

ALLOWED_DOMAINS = ["api.example.com", "cdn.example.com"]

def fetch(self, url: str):
    parsed = urlparse(url)

    # Check scheme
    if parsed.scheme not in ["http", "https"]:
        raise ValueError("Invalid URL scheme")

    # Check domain whitelist
    if parsed.netloc not in ALLOWED_DOMAINS:
        raise ValueError("Domain not allowed")

    # Prevent internal network access
    if parsed.hostname in ["localhost", "127.0.0.1"] or \
       parsed.hostname.startswith("192.168.") or \
       parsed.hostname.startswith("10."):
        raise ValueError("Cannot access internal network")

    response = requests.get(url, timeout=5)
    return response.text
```

---

## Security Checklist

### Before Production

- [ ] All secrets in environment variables (not hardcoded)
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS protection (sanitize HTML)
- [ ] **CORS configured correctly** (use REROUTE's `Config.CORS_ALLOW_ORIGINS`)
- [ ] **No `CORS_ALLOW_ORIGINS = ["*"]` in production**
- [ ] HTTPS enforced
- [ ] Rate limiting on sensitive endpoints (use `@rate_limit`)
- [ ] Authentication implemented
- [ ] Authorization checks on protected resources
- [ ] Password hashing (bcrypt/argon2)
- [ ] CSRF protection (if using cookies)
- [ ] Security headers configured
- [ ] Error messages don't expose internal details
- [ ] Logging configured (but don't log sensitive data)
- [ ] Dependencies up to date (`pip list --outdated`)
- [ ] Security audit run (`bandit`, `safety check`)

### Regular Maintenance

- [ ] Update dependencies monthly
- [ ] Rotate secrets/API keys quarterly
- [ ] Review access logs for suspicious activity
- [ ] Test backup/restore procedures
- [ ] Review and update CORS origins
- [ ] Audit user permissions
- [ ] Check for security advisories

---

## Security Tools

### Bandit (Security Linter)

```bash
pip install bandit

# Scan your code
bandit -r app/

# Generate report
bandit -r app/ -f html -o security-report.html
```

### Safety (Dependency Scanner)

```bash
pip install safety

# Check for known vulnerabilities
safety check

# Check requirements file
safety check -r requirements.txt
```

---

## Next Steps

- [Configuration](../api/config.md) - REROUTE's built-in security settings
- [Error Handling](error-handling.md) - Handle security errors properly
- [Testing](testing.md) - Test security features
- [Deployment](../deployment/production.md) - Secure production deployment
