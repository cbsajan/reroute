# Adapters API

Framework adapter interfaces.

## FastAPIAdapter

Integrate REROUTE with FastAPI.

```python
from reroute.adapters import FastAPIAdapter

adapter = FastAPIAdapter(
    fastapi_app=app,
    app_dir=path,
    config=MyConfig
)
adapter.register_routes()
```

**Parameters:**
- `fastapi_app` (FastAPI): FastAPI application instance
- `app_dir` (Path): Application directory
- `config` (Config): Configuration class

## FlaskAdapter

Integrate REROUTE with Flask. Includes OpenAPI documentation via Spectree.

```python
from reroute.adapters import FlaskAdapter

adapter = FlaskAdapter(
    flask_app=app,
    app_dir=path,
    config=MyConfig
)
adapter.register_routes()
```

**Parameters:**
- `flask_app` (Flask): Flask application instance
- `app_dir` (Path): Application directory
- `config` (Config): Configuration class

## Base Adapter

Create custom adapters by extending `BaseAdapter`.

```python
from reroute.adapters import BaseAdapter

class MyAdapter(BaseAdapter):
    def register_routes(self):
        # Implementation
        pass
```

## Methods

### register_routes()
Register all discovered routes with the framework.

```python
adapter.register_routes()
```

### discover_routes()
Scan and discover route files.

```python
routes = adapter.discover_routes()
```

### run_server()
Start the development server with optional parameter overrides.

```python
# FastAPI
adapter.run_server(port=8080, reload=True)

# Flask
adapter.run_server(port=5000, debug=True)
```

---

## Quick Start Examples

### FastAPI (Recommended for async)

```python
from fastapi import FastAPI
from reroute.adapters import FastAPIAdapter
from pathlib import Path

app = FastAPI(title="My API")

adapter = FastAPIAdapter(
    fastapi_app=app,
    app_dir=Path("./app")
)
adapter.register_routes()
adapter.run_server(port=8000)
```

### Flask (Great for traditional apps)

```python
from flask import Flask
from reroute.adapters import FlaskAdapter
from pathlib import Path

app = Flask(__name__)

adapter = FlaskAdapter(
    flask_app=app,
    app_dir=Path("./app")
)
adapter.register_routes()
adapter.run_server(port=5000)
```

---

## See Also

- [FastAPI Adapter Guide](../adapters/fastapi.md) - Complete FastAPI integration
- [Flask Adapter Guide](../adapters/flask.md) - Complete Flask integration
- [Configuration](config.md) - Adapter configuration options
- [Getting Started](../getting-started/quickstart.md) - First steps with REROUTE
