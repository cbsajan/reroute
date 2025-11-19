"""
Test script to demonstrate REROUTE routing system
"""

import sys
from pathlib import Path

# Add reroute package to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from reroute import Router, DevConfig


def main():
    print("=" * 50)
    print("REROUTE Framework - Router Test")
    print("=" * 50)

    # Initialize router with example app directory
    app_dir = Path(__file__).parent / "app"
    router = Router(app_dir, config=DevConfig)

    # Discover and load routes
    print("\n1. Discovering routes...")
    routes = router.discover_routes()
    print(f"   Found {len(routes)} route(s): {routes}")

    print("\n2. Loading route handlers...")
    router.load_routes()

    print("\n3. Testing route handlers...")
    # Test GET /user
    try:
        handler = router.get_route_handler("/user", "GET")
        result = handler()
        print(f"\n   GET /user response:")
        print(f"   {result}")
    except KeyError as e:
        print(f"   Error: {e}")

    # Test POST /user
    try:
        handler = router.get_route_handler("/user", "POST")
        result = handler()
        print(f"\n   POST /user response:")
        print(f"   {result}")
    except KeyError as e:
        print(f"   Error: {e}")

    print("\n" + "=" * 50)
    print("Test completed!")
    print("=" * 50)


if __name__ == "__main__":
    main()
