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
adapter.run_server(port=8080, reload=True)
```

**Parameters:**
- `host` (str): Host to bind (default: from config.HOST)
- `port` (int): Port to bind (default: from config.PORT)
- `reload` (bool): Enable auto-reloader (default: from config.AUTO_RELOAD)
- `log_level` (str): Log level (default: from config.LOG_LEVEL)

---

## Quick Start Example

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

---

## See Also

- [FastAPI Adapter Guide](../adapters/fastapi.md) - Complete FastAPI integration
- [Configuration](config.md) - Adapter configuration options
- [Getting Started](../getting-started/quickstart.md) - First steps with REROUTE
