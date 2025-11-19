"""
REROUTE - The Modern Python Backend Framework

A lightweight Python backend framework inspired by Angular CLI (generation),
Next.js (folder routing), and FastAPI/Flask (underlying HTTP).
"""

__version__ = "0.1.0"

from reroute.core.router import Router
from reroute.core.loader import RouteLoader
from reroute.core.base import RouteBase
from reroute.config import Config, DevConfig, ProdConfig
from reroute.utils import run_server
from reroute.decorators import (
    rate_limit,
    cache,
    requires,
    validate,
    timeout,
    log_requests,
    clear_cache,
    clear_rate_limits,
    get_cache_stats,
)
from reroute.logging import get_logger, setup_logging, reroute_logger
from reroute.cli.commands import cli

__all__ = [
    "Router",
    "RouteLoader",
    "RouteBase",
    "Config",
    "DevConfig",
    "ProdConfig",
    "run_server",
    "rate_limit",
    "cache",
    "requires",
    "validate",
    "timeout",
    "log_requests",
    "clear_cache",
    "clear_rate_limits",
    "get_cache_stats",
    "get_logger",
    "setup_logging",
    "reroute_logger",
    "cli",
]
