"""
REROUTE - The Modern Python Backend Framework

A lightweight Python backend framework inspired by Angular CLI (generation),
Next.js (folder routing), and FastAPI/Flask (underlying HTTP).

Minimal Quick Start (FastAPI):
    from fastapi import FastAPI
    from reroute import FastAPIAdapter
    from config import AppConfig

    app = FastAPI(title="My API")
    adapter = FastAPIAdapter(app, app_dir="./app", config=AppConfig)
    adapter.register_routes()

    if __name__ == "__main__":
        adapter.run_server()  # Auto-detects project name from app.title

Minimal Quick Start (Flask):
    from flask import Flask
    from reroute import FlaskAdapter
    from config import AppConfig

    app = Flask(__name__)
    adapter = FlaskAdapter(app, app_dir="./app", config=AppConfig)
    adapter.register_routes()

    if __name__ == "__main__":
        adapter.run_server()  # Auto-detects project name from app.name

Full Import Guide:
    # Core - minimal essentials
    from reroute import RouteBase, Config, FastAPIAdapter, FlaskAdapter, run_server

    # Parameter injection
    from reroute.params import Query, Body, Header, Path

    # Decorators
    from reroute.decorators import rate_limit, cache, requires

    # Logging
    from reroute.logging import get_logger
"""

__version__ = "0.2.5"


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

# Security utilities (lazy import to avoid requiring optional dependencies)
def __security_import__(name: str):
    """Lazy import security utilities."""
    try:
        if name == "hash_password":
            from reroute.security.crypto import hash_password
            return hash_password
        elif name == "verify_password":
            from reroute.security.crypto import verify_password
            return verify_password
        elif name == "generate_jwt_token":
            from reroute.security.crypto import generate_jwt_token
            return generate_jwt_token
        elif name == "verify_jwt_token":
            from reroute.security.crypto import verify_jwt_token
            return verify_jwt_token
        elif name == "decode_jwt_token":
            from reroute.security.crypto import decode_jwt_token
            return decode_jwt_token
        elif name == "generate_secret_key":
            from reroute.security.crypto import generate_secret_key
            return generate_secret_key
        elif name == "generate_reset_token":
            from reroute.security.crypto import generate_reset_token
            return generate_reset_token
        elif name == "generate_api_key":
            from reroute.security.crypto import generate_api_key
            return generate_api_key
        elif name == "generate_session_id":
            from reroute.security.crypto import generate_session_id
            return generate_session_id
        elif name == "validate_email":
            from reroute.security.validation import validate_email
            return validate_email
        elif name == "validate_url":
            from reroute.security.validation import validate_url
            return validate_url
        elif name == "sanitize_html":
            from reroute.security.validation import sanitize_html
            return sanitize_html
        elif name == "sanitize_filename":
            from reroute.security.validation import sanitize_filename
            return sanitize_filename
        elif name == "check_password_strength":
            from reroute.security.validation import check_password_strength
            return check_password_strength
    except ImportError:
        # Security dependencies not installed
        pass
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


original_getattr = __getattr__


def __getattr__(name: str):
    """Lazy import for adapters and security utilities."""
    # Try security imports first
    try:
        return __security_import__(name)
    except AttributeError:
        pass
    # Fall back to original adapter imports
    return original_getattr(name)


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
    # Security utilities
    "hash_password",
    "verify_password",
    "generate_jwt_token",
    "verify_jwt_token",
    "decode_jwt_token",
    "generate_secret_key",
    "generate_reset_token",
    "generate_api_key",
    "generate_session_id",
    "validate_email",
    "validate_url",
    "sanitize_html",
    "sanitize_filename",
    "check_password_strength",
    # Version
    "__version__",
]
