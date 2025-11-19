"""
Example FastAPI Application using REROUTE

This demonstrates how to integrate REROUTE with FastAPI.
Showcases: File-based routing, decorators, CORS, and custom configuration.
"""

import sys
from pathlib import Path

# Add reroute to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from reroute.adapters import FastAPIAdapter
from reroute import Config, run_server


# Custom configuration for this example
class ExampleConfig(Config):
    """Example configuration with custom settings"""
    HOST = "0.0.0.0"
    PORT = 7376
    VERBOSE_LOGGING = True
    AUTO_RELOAD = True
    API_BASE_PATH = "/api/v1"  # All REROUTE routes will be under /api/v1

    # CORS Configuration
    ENABLE_CORS = True
    CORS_ALLOW_ORIGINS = ["*"]
    CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    CORS_ALLOW_HEADERS = ["*"]


# Create FastAPI app
app = FastAPI(
    title="REROUTE + FastAPI Demo",
    description="File-based routing with FastAPI, featuring decorators and CORS",
    version="0.1.0"
)

# Initialize REROUTE adapter
adapter = FastAPIAdapter(
    fastapi_app=app,
    app_dir=Path(__file__).parent / "app",
    config=ExampleConfig
)

# Register all REROUTE routes with FastAPI
adapter.register_routes()

# Optional: Add custom routes outside of REROUTE
@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Welcome to REROUTE + FastAPI",
        "framework": "REROUTE v0.1.0",
        "docs": "/docs",
        "routes": {
            "/api/v1/user": "REROUTE file-based route with base path"
        },
        "features": [
            "File-based routing",
            "Decorators (rate_limit, cache, etc.)",
            "Global CORS",
            "Swagger tags",
            "Logging utilities"
        ]
    }

@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy", "port": 7376}


if __name__ == "__main__":
    # Using REROUTE's run_server utility
    run_server("fastapi_app:app", config=ExampleConfig, project_name="REROUTE Example")
