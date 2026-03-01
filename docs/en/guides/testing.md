# Testing REROUTE Applications

Learn how to test your REROUTE routes, hooks, and decorators to ensure reliability and quality.

---

## Overview

This guide focuses on testing REROUTE-specific features:

- **Unit testing** RouteBase classes
- Testing hooks (before_request, after_request, on_error)
- Testing REROUTE decorators (@rate_limit, @cache, @timeout)
- Testing route parameters
- Testing async route handlers
- Integration testing (HTTP endpoints)
- Database testing
- CI/CD integration

---

## Quick Start

### Install Testing Dependencies

```bash
pip install pytest pytest-asyncio
```

### Project Structure

```
my-app/
├── app/
│   ├── routes/
│   │   └── users/
│   │       └── page.py
│   ├── models/
│   └── database.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_user_routes.py
│   └── test_hooks.py
└── pytest.ini
```

---

## Unit Testing RouteBase Classes

Test your route classes directly without HTTP overhead.

### Basic Route Class Test

```python
# app/routes/users/page.py
from reroute import RouteBase

class UserRoutes(RouteBase):
    def get(self):
        """Get all users."""
        return {"users": self.get_all_users()}

    def post(self, username: str, email: str):
        """Create a user."""
        user = self.create_user(username, email)
        return {"user": user, "created": True}

    def get_all_users(self):
        # Business logic
        return [{"id": 1, "username": "alice"}]

    def create_user(self, username, email):
        # Business logic
        return {"id": 2, "username": username, "email": email}
```

```python
# tests/test_user_routes.py
import pytest
from app.routes.users.page import UserRoutes

def test_get_users():
    """Test GET handler returns user list."""
    route = UserRoutes()
    result = route.get()

    assert "users" in result
    assert isinstance(result["users"], list)
    assert len(result["users"]) > 0

def test_post_user():
    """Test POST handler creates user."""
    route = UserRoutes()
    result = route.post(username="testuser", email="test@example.com")

    assert result["created"] is True
    assert result["user"]["username"] == "testuser"
    assert result["user"]["email"] == "test@example.com"

def test_business_logic():
    """Test business logic methods directly."""
    route = UserRoutes()

    # Test get_all_users
    users = route.get_all_users()
    assert len(users) >= 1

    # Test create_user
    new_user = route.create_user("newuser", "new@example.com")
    assert new_user["username"] == "newuser"
```

---

## Testing Hooks

### Testing before_request Hook

```python
# app/routes/protected/page.py
from reroute import RouteBase

class ProtectedRoutes(RouteBase):
    def before_request(self):
        """Check authentication before processing request."""
        if not hasattr(self, 'auth_token'):
            return {"error": "Missing auth token"}, 401

        if self.auth_token != "valid-token-123":
            return {"error": "Invalid token"}, 401

        # Continue to handler
        return None

    def get(self):
        return {"data": "protected data", "user": "authenticated"}
```

```python
# tests/test_hooks.py
import pytest
from app.routes.protected.page import ProtectedRoutes

def test_before_request_missing_token():
    """Test before_request blocks request without token."""
    route = ProtectedRoutes()
    # Don't set auth_token

    result = route.before_request()

    assert result is not None  # Hook returned early
    response, status_code = result
    assert status_code == 401
    assert "error" in response

def test_before_request_invalid_token():
    """Test before_request blocks request with invalid token."""
    route = ProtectedRoutes()
    route.auth_token = "invalid-token"

    result = route.before_request()

    assert result is not None
    response, status_code = result
    assert status_code == 401
    assert "Invalid token" in response["error"]

def test_before_request_valid_token():
    """Test before_request allows valid token."""
    route = ProtectedRoutes()
    route.auth_token = "valid-token-123"

    result = route.before_request()

    assert result is None  # Hook allows request to continue

def test_get_with_valid_auth():
    """Test GET handler runs after successful before_request."""
    route = ProtectedRoutes()
    route.auth_token = "valid-token-123"

    # before_request would pass
    assert route.before_request() is None

    # Now test handler
    result = route.get()
    assert result["data"] == "protected data"
```

### Testing after_request Hook

```python
# app/routes/api/page.py
from reroute import RouteBase

class APIRoutes(RouteBase):
    def after_request(self, response):
        """Add metadata to all responses."""
        if isinstance(response, dict):
            response["meta"] = {
                "version": "1.0",
                "timestamp": "2025-11-23T10:00:00Z"
            }
        return response

    def get(self):
        return {"data": "some data"}
```

```python
# tests/test_hooks.py
def test_after_request_adds_metadata():
    """Test after_request hook adds metadata."""
    route = APIRoutes()

    # Get original response
    original = route.get()
    assert "meta" not in original

    # Apply after_request hook
    result = route.after_request(original)

    assert "meta" in result
    assert result["meta"]["version"] == "1.0"
    assert "timestamp" in result["meta"]

def test_after_request_preserves_data():
    """Test after_request preserves original data."""
    route = APIRoutes()

    original = {"data": "important data", "id": 123}
    result = route.after_request(original)

    assert result["data"] == "important data"
    assert result["id"] == 123
```

### Testing on_error Hook

```python
# app/routes/users/page.py
from reroute import RouteBase

class UserRoutes(RouteBase):
    def on_error(self, error: Exception):
        """Handle errors with appropriate responses."""
        if isinstance(error, ValueError):
            return {"error": "Invalid input", "message": str(error)}, 400

        elif isinstance(error, KeyError):
            return {"error": "Not found", "message": str(error)}, 404

        else:
            return {"error": "Internal error"}, 500

    def get(self, user_id: int):
        if user_id < 0:
            raise ValueError("User ID must be positive")

        if user_id == 99999:
            raise KeyError("User not found")

        return {"id": user_id, "username": "user"}
```

```python
# tests/test_error_handling.py
import pytest
from app.routes.users.page import UserRoutes

def test_on_error_value_error():
    """Test on_error handles ValueError."""
    route = UserRoutes()
    error = ValueError("Invalid user ID")

    response, status_code = route.on_error(error)

    assert status_code == 400
    assert response["error"] == "Invalid input"
    assert "Invalid user ID" in response["message"]

def test_on_error_key_error():
    """Test on_error handles KeyError."""
    route = UserRoutes()
    error = KeyError("User not found")

    response, status_code = route.on_error(error)

    assert status_code == 404
    assert response["error"] == "Not found"

def test_on_error_generic_exception():
    """Test on_error handles unknown exceptions."""
    route = UserRoutes()
    error = RuntimeError("Unexpected error")

    response, status_code = route.on_error(error)

    assert status_code == 500
    assert response["error"] == "Internal error"

def test_handler_raises_value_error():
    """Test handler raises ValueError for invalid input."""
    route = UserRoutes()

    with pytest.raises(ValueError, match="must be positive"):
        route.get(user_id=-1)

def test_handler_raises_key_error():
    """Test handler raises KeyError for not found."""
    route = UserRoutes()

    with pytest.raises(KeyError, match="not found"):
        route.get(user_id=99999)
```

---

## Testing REROUTE Decorators

### Testing @rate_limit Decorator

```python
# app/routes/api/page.py
from reroute import RouteBase
from reroute.decorators import rate_limit

class APIRoutes(RouteBase):
    @rate_limit("3/min")
    def get(self):
        return {"data": "limited endpoint"}
```

```python
# tests/test_decorators.py
import pytest
import time
from app.routes.api.page import APIRoutes

def test_rate_limit_allows_within_limit():
    """Test rate limiter allows requests within limit."""
    route = APIRoutes()

    # First 3 requests should succeed
    for i in range(3):
        result = route.get()
        assert "data" in result

def test_rate_limit_blocks_over_limit():
    """Test rate limiter blocks requests over limit."""
    route = APIRoutes()

    # Exhaust rate limit
    for i in range(3):
        route.get()

    # 4th request should be rate limited
    result = route.get()

    # Check if it's a tuple (error response with status code)
    if isinstance(result, tuple):
        response, status_code = result
        assert status_code == 429
        assert "rate limit" in response["error"].lower()

def test_rate_limit_resets():
    """Test rate limit resets after window."""
    route = APIRoutes()

    # Exhaust limit
    for i in range(3):
        route.get()

    # Should be blocked
    result = route.get()
    if isinstance(result, tuple):
        assert result[1] == 429

    # Wait for rate limit window to reset
    time.sleep(61)  # Wait > 1 minute

    # Should work again
    result = route.get()
    assert isinstance(result, dict)
    assert "data" in result
```

### Testing @cache Decorator

```python
# app/routes/data/page.py
from reroute import RouteBase
from reroute.decorators import cache

class DataRoutes(RouteBase):
    def __init__(self):
        super().__init__()
        self.call_count = 0

    @cache(duration=60)
    def get(self):
        self.call_count += 1
        return {"data": "expensive computation", "count": self.call_count}
```

```python
# tests/test_cache.py
import pytest
from app.routes.data.page import DataRoutes

def test_cache_caches_result():
    """Test cache decorator caches results."""
    route = DataRoutes()

    # First call
    result1 = route.get()
    assert result1["count"] == 1

    # Second call should be cached (count should still be 1)
    result2 = route.get()
    assert result2["count"] == 1  # Cached, no re-execution

def test_cache_expires():
    """Test cache expires after duration."""
    import time

    route = DataRoutes()

    # First call
    result1 = route.get()
    count1 = result1["count"]

    # Wait for cache to expire (use short duration in real tests)
    # In actual test, use @cache(duration=1) for faster testing
    time.sleep(2)

    # Should execute again
    result2 = route.get()
    assert result2["count"] > count1
```

### Testing @timeout Decorator

```python
# app/routes/slow/page.py
from reroute import RouteBase
from reroute.decorators import timeout
import time

class SlowRoutes(RouteBase):
    @timeout(seconds=2)
    def get(self, delay: int = 0):
        time.sleep(delay)
        return {"completed": True}
```

```python
# tests/test_timeout.py
import pytest
from app.routes.slow.page import SlowRoutes

def test_timeout_allows_fast_requests():
    """Test timeout allows requests that complete in time."""
    route = SlowRoutes()

    result = route.get(delay=1)  # 1 second (under 2 second limit)

    assert result["completed"] is True

def test_timeout_blocks_slow_requests():
    """Test timeout blocks requests that exceed limit."""
    route = SlowRoutes()

    result = route.get(delay=3)  # 3 seconds (over 2 second limit)

    # Should return timeout error
    if isinstance(result, tuple):
        response, status_code = result
        assert status_code == 408
        assert "timeout" in response["error"].lower()
```

---

## Testing Async Route Handlers

```python
# app/routes/async_users/page.py
from reroute import RouteBase
import asyncio

class AsyncUserRoutes(RouteBase):
    async def get(self):
        """Async GET handler."""
        await asyncio.sleep(0.1)  # Simulate async operation
        return {"users": await self.fetch_users()}

    async def fetch_users(self):
        await asyncio.sleep(0.05)
        return [{"id": 1, "name": "Alice"}]
```

```python
# tests/test_async_routes.py
import pytest
import asyncio
from app.routes.async_users.page import AsyncUserRoutes

@pytest.mark.asyncio
async def test_async_get_handler():
    """Test async GET handler."""
    route = AsyncUserRoutes()

    result = await route.get()

    assert "users" in result
    assert len(result["users"]) > 0

@pytest.mark.asyncio
async def test_async_fetch_users():
    """Test async fetch_users method."""
    route = AsyncUserRoutes()

    users = await route.fetch_users()

    assert isinstance(users, list)
    assert users[0]["name"] == "Alice"
```

---

## Testing with Mock Data

### Mocking External Dependencies

```python
# app/routes/external/page.py
from reroute import RouteBase
import httpx

class ExternalAPIRoutes(RouteBase):
    async def get(self):
        data = await self.fetch_external_data()
        return {"external_data": data}

    async def fetch_external_data(self):
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.example.com/data")
            return response.json()
```

```python
# tests/test_external_api.py
import pytest
from unittest.mock import AsyncMock, patch
from app.routes.external.page import ExternalAPIRoutes

@pytest.mark.asyncio
async def test_fetch_external_data_success():
    """Test external API call with mocked response."""
    route = ExternalAPIRoutes()

    # Mock the httpx client
    mock_response = AsyncMock()
    mock_response.json.return_value = {"result": "mocked data"}

    with patch('httpx.AsyncClient.get', return_value=mock_response):
        result = await route.fetch_external_data()

        assert result["result"] == "mocked data"

@pytest.mark.asyncio
async def test_get_with_mocked_data():
    """Test GET handler with mocked external call."""
    route = ExternalAPIRoutes()

    # Mock the fetch method
    route.fetch_external_data = AsyncMock(return_value={"mocked": True})

    result = await route.get()

    assert result["external_data"]["mocked"] is True
```

---

## Testing with Database

### Using Test Database

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base

TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_session():
    """Create fresh database for each test."""
    engine = create_engine(TEST_DB_URL)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()
    Base.metadata.drop_all(engine)
```

```python
# app/routes/users/page.py
from reroute import RouteBase
from models import User

class UserRoutes(RouteBase):
    def __init__(self, db_session=None):
        super().__init__()
        self.db = db_session

    def get(self):
        users = self.db.query(User).all()
        return {"users": [u.to_dict() for u in users]}

    def post(self, username: str, email: str):
        user = User(username=username, email=email)
        self.db.add(user)
        self.db.commit()
        return {"user": user.to_dict()}
```

```python
# tests/test_database_routes.py
import pytest
from app.routes.users.page import UserRoutes
from models import User

def test_get_users_empty(db_session):
    """Test GET returns empty list initially."""
    route = UserRoutes(db_session=db_session)

    result = route.get()

    assert result["users"] == []

def test_post_creates_user(db_session):
    """Test POST creates user in database."""
    route = UserRoutes(db_session=db_session)

    result = route.post(username="testuser", email="test@example.com")

    # Verify in response
    assert result["user"]["username"] == "testuser"

    # Verify in database
    user = db_session.query(User).filter_by(username="testuser").first()
    assert user is not None
    assert user.email == "test@example.com"

def test_get_users_returns_created(db_session):
    """Test GET returns created users."""
    route = UserRoutes(db_session=db_session)

    # Create users
    route.post(username="user1", email="user1@example.com")
    route.post(username="user2", email="user2@example.com")

    # Get users
    result = route.get()

    assert len(result["users"]) == 2
    assert result["users"][0]["username"] == "user1"
    assert result["users"][1]["username"] == "user2"
```

---

## Integration Testing (HTTP Endpoints)

For testing the full HTTP layer, use framework test clients:

### FastAPI Integration Tests

```python
# tests/test_integration.py
import pytest
from fastapi.testclient import TestClient
from main import app  # Your REROUTE app

client = TestClient(app)

def test_get_users_endpoint():
    """Test GET /users HTTP endpoint."""
    response = client.get("/users")

    assert response.status_code == 200
    assert "users" in response.json()

def test_post_user_endpoint():
    """Test POST /users HTTP endpoint."""
    response = client.post("/users", json={
        "username": "newuser",
        "email": "new@example.com"
    })

    assert response.status_code == 201
    assert response.json()["username"] == "newuser"
```

### Flask Integration Tests

```python
# tests/test_integration.py
import pytest
from main import app  # Your REROUTE app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_users_endpoint(client):
    response = client.get('/users')

    assert response.status_code == 200
    assert 'users' in response.get_json()
```

---

## Test Configuration

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*

markers =
    slow: slow tests
    asyncio: async tests
    integration: integration tests

addopts =
    --verbose
    --cov=app
    --cov-report=term-missing
    --cov-report=html
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific file
pytest tests/test_user_routes.py

# Run specific test
pytest tests/test_user_routes.py::test_get_users

# Run with coverage
pytest --cov=app --cov-report=html

# Run only unit tests (exclude integration)
pytest -m "not integration"

# Run async tests
pytest -m asyncio

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

---

## Best Practices

### 1. Test RouteBase Classes Directly

```python
# Good - Direct unit test
def test_business_logic():
    route = UserRoutes()
    result = route.create_user("test", "test@example.com")
    assert result["username"] == "test"

# Avoid - Unnecessary HTTP overhead for unit test
def test_business_logic_http(client):
    response = client.post("/users", json={"username": "test"})
    assert response.status_code == 200
```

### 2. Test Hooks in Isolation

```python
def test_before_request_logic():
    """Test before_request independently."""
    route = ProtectedRoutes()
    route.auth_token = "invalid"

    result = route.before_request()

    assert result[1] == 401  # Direct assertion on hook result
```

### 3. Use Fixtures for Route Instances

```python
@pytest.fixture
def user_route(db_session):
    """Create UserRoutes instance with test database."""
    return UserRoutes(db_session=db_session)

def test_with_fixture(user_route):
    result = user_route.get()
    assert "users" in result
```

### 4. Test One Thing Per Test

```python
# Good
def test_get_returns_users():
    route = UserRoutes()
    result = route.get()
    assert "users" in result

def test_get_returns_list():
    route = UserRoutes()
    result = route.get()
    assert isinstance(result["users"], list)

# Avoid
def test_get_everything():
    route = UserRoutes()
    result = route.get()
    assert "users" in result
    assert isinstance(result["users"], list)
    assert len(result["users"]) >= 0
    # Too many assertions
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-cov pytest-asyncio

      - name: Run tests
        run: pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Next Steps

- [Error Handling](error-handling.md) - Test error scenarios
- [Security](security.md) - Test authentication and authorization
- [Lifecycle Hooks](lifecycle-hooks.md) - Learn more about REROUTE hooks
- [Decorators](decorators.md) - Learn more about REROUTE decorators
