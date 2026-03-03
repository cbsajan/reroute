# Troubleshooting

Common issues and solutions when using REROUTE.

## Import Errors

### Adapter Import Error

**Symptoms:**
```
ImportError: cannot import name 'FlaskAdapter' from 'reroute'
ImportError: Flask adapter is not available
```

**Root Cause:**

REROUTE now focuses exclusively on FastAPI. Other framework adapters are not available.

**Solution:**

Use `FastAPIAdapter` instead:

```python
# Correct usage:
from reroute import FastAPIAdapter

from fastapi import FastAPI
from config import AppConfig

app = FastAPI(title="My API")
adapter = FastAPIAdapter(app, app_dir="./app", config=AppConfig)
adapter.register_routes()
```

If you're migrating from another framework, see [FastAPI Integration](../adapters/fastapi.md) for guidance.

---

## Routes Not Being Registered

**Symptoms:**
- Routes return 404 errors
- Route files exist but aren't accessible

**Common Causes:**

1. **Incorrect file structure**: Route files must be in `app/routes/<route-name>/page.py`
2. **Missing RouteBase**: Route class must inherit from `RouteBase`
3. **No HTTP methods**: Class must have at least one method (get, post, put, delete)

**Solution:**

Ensure proper structure:

```
app/
  routes/
    hello/
      page.py    # Contains HelloRoutes class
```

```python
# page.py
from reroute import RouteBase

class HelloRoutes(RouteBase):
    def get(self):
        return {"message": "Hello"}
```

---

## Port Already in Use

**Symptoms:**
```
OSError: [Errno 98] Address already in use
OSError: [Errno 48] Address already in use
```

**Solution:**

Change the port in `config.py`:

```python
class AppConfig(Config):
    PORT = 8080  # Use different port
```

Or kill the process using the port:

```bash
# Windows
netstat -ano | findstr :7376
taskkill /PID <process_id> /F

# Linux/Mac
lsof -ti:7376 | xargs kill -9
```

---

## Routes Not Appearing in Swagger UI

**Symptoms:**
- Swagger UI loads successfully but shows no API endpoints
- OpenAPI JSON at `/docs/openapi.json` has empty `"paths": {}`
- Routes work correctly when tested with `curl` or browser

**Common Causes:**

1. **OpenAPI disabled**: Check if `OpenAPI.ENABLE = True` in config
2. **Wrong port**: Ensure you're accessing the correct port
3. **Routes not registered**: Verify `adapter.register_routes()` is called

**Solution:**

```python
# config.py
class AppConfig(Config):
    class OpenAPI:
        ENABLE = True                    # Enable OpenAPI docs
        DOCS_PATH = "/docs"              # Swagger UI endpoint
        JSON_PATH = "/openapi.json"      # OpenAPI spec endpoint

# main.py
adapter.register_routes()  # Don't forget this!
```

---

## ModuleNotFoundError

**Symptoms:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**

Install all dependencies:

```bash
pip install -r requirements.txt
```

Or install FastAPI directly:

```bash
pip install fastapi uvicorn
```

---

## Configuration Issues

### IndentationError in Generated config.py

**Symptoms:**
```
File "config.py", line 42
  TITLE = "MyProject"
IndentationError: unexpected indent
```

**Root Cause:**

In earlier versions (before v0.1.4), the Jinja2 template had multiple configuration statements on a single line.

**Solution:**

Fixed in v0.1.4+. If you have an old project, manually fix your `config.py`:

```python
# BEFORE (WRONG):
REDOC_PATH = None ... JSON_PATH = "/openapi.json"

# AFTER (CORRECT):
REDOC_PATH = None
JSON_PATH = "/openapi.json"
```

---

## CORS Errors in Browser

**Symptoms:**
- Browser console shows CORS errors
- API works with curl but fails from web frontend

**Solution:**

Enable and configure CORS in your `config.py`:

```python
class AppConfig(Config):
    ENABLE_CORS = True
    CORS_ALLOW_ORIGINS = ["http://localhost:3000"]  # Your frontend URL
    CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    CORS_ALLOW_HEADERS = ["*"]
    CORS_ALLOW_CREDENTIALS = True
```

---

## Performance Issues

### Slow Route Discovery

**Symptoms:**
- Application takes a long time to start
- Many route files

**Solution:**

REROUTE caches discovered routes. If you have performance issues:

1. Reduce the number of nested route folders
2. Use class-based routes instead of many small files
3. Check for circular imports in route files

### Memory Issues

**Symptoms:**
- Application uses too much memory
- Memory usage grows over time

**Solution:**

The `@cache` decorator has built-in LRU eviction with bounded storage (1000 entries max). If you need more control:

```python
from reroute.decorators import cache

# Configure cache limits
@cache(max_entries=500, duration=60)  # Keep only 500 entries
def get_data():
    return expensive_operation()
```

---

## Need More Help?

If you encounter issues not covered here:

1. Check the [Installation Troubleshooting](../troubleshooting/installation.md) for setup issues
2. Review the [Examples](../examples/index.md) for working code
3. Check the [API Reference](../api/index.md) for detailed documentation
4. Report bugs at [GitHub Issues](https://github.com/cbsajan/reroute/issues)
