"""
Test FastAPI Integration

This script tests REROUTE + FastAPI without actually starting the server.
"""

import sys
from pathlib import Path

# Add reroute to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from fastapi import FastAPI
    from reroute.adapters import FastAPIAdapter
    from reroute import DevConfig

    print("="*50)
    print("REROUTE + FastAPI Integration Test")
    print("="*50)

    # Create FastAPI app
    app = FastAPI(title="REROUTE Test")

    # Initialize adapter
    print("\n1. Initializing FastAPI adapter...")
    adapter = FastAPIAdapter(
        fastapi_app=app,
        app_dir=Path(__file__).parent / "app",
        config=DevConfig
    )

    # Register routes
    print("\n2. Registering REROUTE routes...")
    adapter.register_routes()

    # Show registered routes
    print("\n3. FastAPI routes registered:")
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(route.methods)
            print(f"   {methods:20} {route.path}")

    print("\n" + "="*50)
    print("[OK] Integration test completed!")
    print("="*50)

    print("\nTo start the server, run:")
    print("  cd examples")
    print("  python fastapi_app.py")
    print("\nOr with uvicorn directly:")
    print("  uvicorn fastapi_app:app --reload")

except ImportError as e:
    print("="*50)
    print("FastAPI not installed")
    print("="*50)
    print(f"\nError: {e}")
    print("\nTo install FastAPI:")
    print("  pip install fastapi uvicorn")
    print("\nOr install from requirements:")
    print("  pip install -r requirements.txt")
