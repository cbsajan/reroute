"""
REROUTE Adapters

Framework adapters for FastAPI, Flask, etc.

Adapters are loaded lazily to avoid requiring all frameworks to be installed.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from reroute.adapters.fastapi import FastAPIAdapter

def __getattr__(name: str):
    """Lazy import adapters only when accessed."""
    if name == "FastAPIAdapter":
        try:
            from reroute.adapters.fastapi import FastAPIAdapter
            return FastAPIAdapter
        except ImportError as e:
            raise ImportError(
                f"FastAPI is not installed. Install it with: pip install reroute[fastapi]"
            ) from e

    elif name == "FlaskAdapter":
        raise ImportError(
            "Flask adapter is not available. REROUTE now focuses exclusively on FastAPI. "
            "Please use FastAPIAdapter instead. FastAPI provides better async support, "
            "automatic OpenAPI documentation, and is actively maintained. "
            "See https://fastapi.tiangolo.com for more information."
        )

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["FastAPIAdapter"]
