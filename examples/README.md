# REROUTE Examples

Example applications demonstrating REROUTE features.

## FastAPI Example

### Features Demonstrated

- ✅ File-based routing
- ✅ Class-based routes
- ✅ Decorators (`@rate_limit`, `@cache`)
- ✅ Custom Swagger tags
- ✅ Global CORS configuration
- ✅ API base path (`/api/v1`)
- ✅ Lifecycle hooks (`before_request`, `after_request`, `on_error`)
- ✅ Custom configuration
- ✅ `run_server()` utility

### Project Structure

```
examples/
├── fastapi_app.py          # Main FastAPI application
├── app/
│   └── routes/
│       └── user/
│           └── page.py     # User routes with decorators
├── test_fastapi.py        # Test cases
└── README.md              # This file
```

### Running the Example

1. **Install dependencies:**
   ```bash
   cd examples
   pip install fastapi uvicorn
   ```

2. **Run the server:**
   ```bash
   python fastapi_app.py
   ```

3. **Visit:**
   - API Docs: http://localhost:7376/docs
   - Root: http://localhost:7376/
   - Health: http://localhost:7376/health
   - Users: http://localhost:7376/api/v1/user

### Try the Features

#### 1. Rate Limiting
```bash
# Try POST more than 5 times in a minute
curl -X POST http://localhost:7376/api/v1/user
```

#### 2. Caching
```bash
# GET requests are cached for 30 seconds
curl http://localhost:7376/api/v1/user
```

#### 3. CRUD Operations
```bash
# GET all users
curl http://localhost:7376/api/v1/user

# POST new user
curl -X POST http://localhost:7376/api/v1/user

# PUT update user
curl -X PUT http://localhost:7376/api/v1/user

# DELETE user
curl -X DELETE http://localhost:7376/api/v1/user
```

### Code Highlights

**Custom Configuration:**
```python
class ExampleConfig(Config):
    PORT = 7376
    API_BASE_PATH = "/api/v1"
    ENABLE_CORS = True
```

**Decorators in Action:**
```python
@cache(duration=30)
def get(self):
    return {"users": [...]}

@rate_limit("5/min")
def post(self):
    return {"created": True}
```

**Lifecycle Hooks:**
```python
def before_request(self):
    # Authentication, logging
    return None

def after_request(self, response):
    # Add timestamp, headers
    return response
```

## Running Tests

```bash
pytest test_fastapi.py
```

## What's Next?

Check out the [full documentation](https://github.com/cbsajan/reroute-docs) for more examples and tutorials!
