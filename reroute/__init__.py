"""
REROUTE - The Modern Python Backend Framework

A lightweight Python backend framework inspired by Angular CLI (generation),
Next.js (folder routing), and FastAPI/Flask (underlying HTTP).

Minimal Quick Start:
    from fastapi import FastAPI
    from reroute import RouteBase, FastAPIAdapter

    app = FastAPI()
    adapter = FastAPIAdapter(app, app_dir="./app")
    adapter.register_routes()

Full Import Guide:
    # Core - minimal essentials
    from reroute import RouteBase, Config, FastAPIAdapter, run_server

    # Parameter injection
    from reroute.params import Query, Body, Header, Path

    # Decorators
    from reroute.decorators import rate_limit, cache, requires

    # Logging
    from reroute.logging import get_logger
"""

__version__ = "0.1.2"

# Core essentials for minimal usage
from reroute.core.base import RouteBase
from reroute.config import Config, DevConfig, ProdConfig
from reroute.utils import run_server

# Lazy import for adapters (requires optional dependencies)
def __getattr__(name: str):
    """Lazy import adapters to avoid requiring optional dependencies."""
    if name == "FastAPIAdapter":
        from reroute.adapters import FastAPIAdapter
        return FastAPIAdapter

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    # Core
    "RouteBase",
    "Config",
    "DevConfig",
    "ProdConfig",
    # Adapters (for minimal setup)
    "FastAPIAdapter",
    # Utils (for minimal setup)
    "run_server",
    # Version
    "__version__",
]
