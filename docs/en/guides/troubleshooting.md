# Troubleshooting

Common issues and solutions when using REROUTE.

## Flask Adapter Issues

### Routes Not Appearing in Swagger UI

**Symptoms:**
- Swagger UI loads successfully but shows no API endpoints
- OpenAPI JSON at `/docs/openapi.json` has empty `"paths": {}`
- Routes work correctly when tested with `curl` or browser
- Response schemas appear in OpenAPI spec but no actual routes

**Root Cause:**

This issue was caused by two bugs in the Flask adapter's Spectree integration:

1. **Empty Path Parameter Bug**: When `DOCS_PATH="/docs"` in config, the adapter extracted an empty string (`path=''`) to pass to Spectree. Spectree's route discovery filter then excluded ALL routes because:
   - Filter logic: Skip routes starting with `/{path}` or `/static`
   - When `path=''`, this becomes: Skip routes starting with `/`
   - Since ALL routes start with `/`, ALL routes were excluded from OpenAPI generation

2. **Closure Metadata Bug**: REROUTE's closure-based request handling wrapped handlers in a way that hid Spectree's validation metadata, preventing proper OpenAPI documentation generation.

**Solution (Fixed in v0.1.4):**

The Flask adapter now:

1. **Never uses empty path**: Extracts the first segment from `DOCS_PATH` (e.g., `"/docs"` → `path="docs"`, `"/api/docs"` → `path="api"`), ensuring Spectree's filter doesn't exclude all routes
2. **Validates handlers early**: Applies `spec.validate()` to handlers BEFORE wrapping in REROUTE's closure
3. **Copies metadata correctly**: Transfers all Spectree attributes (`_decorator`, `tags`, `operation_id`, etc.) from validated handler to Flask-facing closure

**Updated Swagger UI Paths:**

Because the path is no longer empty, Swagger UI endpoints are now at:

```
DOCS_PATH in config    →    Swagger UI URL
/docs                  →    /docs/swagger/
/api/docs              →    /api/swagger/
/custom                →    /custom/swagger/
```

**Migration:**

If you were accessing Swagger UI at `/swagger/`, you now need to use `/docs/swagger/` (or whatever your `DOCS_PATH` is configured to).

To keep the old `/swagger/` URL, you can:
1. Update your bookmarks/links to `/docs/swagger/`
2. Or change `DOCS_PATH` in config.py to match your preference

**Example:**

```python
# config.py
class AppConfig(Config):
    class OpenAPI:
        ENABLE = True
        DOCS_PATH = "/docs"           # Swagger UI at /docs/swagger/
        JSON_PATH = "/openapi.json"   # OpenAPI spec at /docs/openapi.json
```

### IndentationError in Generated config.py

**Symptoms:**
```
File "config.py", line 42
  TITLE = "MyProject"
IndentationError: unexpected indent
```

**Root Cause:**

In earlier versions (before v0.1.4), the Jinja2 template had multiple configuration statements on a single line:

```python
REDOC_PATH = None ... JSON_PATH = "/openapi.json"
```

**Solution:**

Fixed in v0.1.4 - each statement is now on its own line with proper indentation.

**For Existing Projects:**

If your project was created before v0.1.4, manually fix your `config.py`:

```python
# BEFORE (WRONG - all on one line):
REDOC_PATH = None              # ReDoc disabled for Flask (broken CDN)    JSON_PATH = "/openapi.json"    # OpenAPI JSON spec endpoint

# AFTER (CORRECT - separate lines):
REDOC_PATH = None              # ReDoc disabled for Flask (broken CDN)
JSON_PATH = "/openapi.json"    # OpenAPI JSON spec endpoint
```

### ModuleNotFoundError: spectree

**Symptoms:**
```
ModuleNotFoundError: No module named 'spectree'
```

**Solution:**

Install all dependencies:

```bash
pip install -r requirements.txt
```

Or install spectree directly:

```bash
pip install spectree
```

### CORS Errors in Browser

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

Install flask-cors:

```bash
pip install flask-cors
```

## General Issues

### Routes Not Being Registered

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

### Port Already in Use

**Symptoms:**
```
OSError: [Errno 98] Address already in use
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

## Need More Help?

If you encounter issues not covered here:

1. Check the [Examples](../examples/index.md) for working code
2. Review the [API Reference](../api/index.md) for detailed documentation
3. Report bugs at [GitHub Issues](https://github.com/anthropics/reroute/issues)
