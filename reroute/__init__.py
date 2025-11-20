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

__version__ = "0.1.0"

# Core essentials for minimal usage
from reroute.core.base import RouteBase
from reroute.config import Config, DevConfig, ProdConfig
from reroute.utils import run_server
from reroute.adapters import FastAPIAdapter

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
