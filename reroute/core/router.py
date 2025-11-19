"""
Router Module

Discovers and registers routes from the app/routes directory structure.
"""

from pathlib import Path
from typing import Dict, List, Callable, Optional, Any
import inspect
from reroute.core.loader import RouteLoader
from reroute.core.base import RouteBase
from reroute.config import Config


class Router:
    """
    Main routing engine for REROUTE.

    Discovers routes from folder structure and maps them to HTTP handlers.
    Minimal version: flat folder structure only, no nested routes.
    """

    def __init__(self, app_dir: Path, config: Optional[Config]  = None):
        """
        Initialize the Router.

        Args:
            app_dir: Path to the app directory containing routes/ folder
            config: Configuration object (defaults to Config)
        """
        self.app_dir = Path(app_dir)
        self.config = config or Config
        self.routes_dir = self.app_dir / self.config.ROUTES_DIR_NAME
        self.loader = RouteLoader(self.routes_dir)
        self.routes: Dict[str, Dict[str, Callable]] = {}

    def discover_routes(self) -> List[str]:
        """
        Discover all route folders in the routes directory.

        For minimal version: scans only top-level folders in routes/
        Each folder represents a route endpoint.

        Returns:
            List of discovered route paths

        Example:
            routes/
                user/page.py    -> /user
                product/page.py -> /product
        """
        discovered_routes = []

        # Check if routes directory exists
        if not self.routes_dir.exists():
            return discovered_routes

        # Step 1: Loop through everything in the routes/ folder
        for item in self.routes_dir.iterdir():

            # Step 2: Check if it's a folder (not a file) and not ignored
            if item.is_dir() and item.name not in self.config.IGNORE_FOLDERS:

                # Step 3: Check if this folder has the route file inside
                page_file = item / self.config.ROUTE_FILE_NAME
                if page_file.exists():

                    # Step 4: Convert folder name to route path
                    # Example: "user" folder becomes "/user" route
                    route_path = f"/{item.name}"
                    discovered_routes.append(route_path)

        return discovered_routes

    def load_routes(self) -> None:
        """
        Load all discovered routes and extract their HTTP method handlers.

        For each route, load the page.py module and extract methods like:
        - get() -> HTTP GET
        - post() -> HTTP POST
        - put() -> HTTP PUT
        - delete() -> HTTP DELETE
        """
        discovered = self.discover_routes()

        for route_path in discovered:
            # Convert route path back to folder name
            # "/user" -> "user"
            folder_name = route_path.lstrip("/")
            page_file = self.routes_dir / folder_name / "page.py"

            # Load the module using our secure loader
            module = self.loader.load_module(page_file)

            if module is None:
                print(f"Warning: Could not load route {route_path}")
                continue

            # Extract HTTP method handlers from the module
            route_handlers = {}
            route_instance = None

            # Check if module has a class-based route
            # Look for classes that inherit from RouteBase or end with "Routes"
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Skip imported classes (like RouteBase itself)
                if obj.__module__ != module.__name__:
                    continue

                # Check if it's a route class
                is_route_class = False
                try:
                    is_route_class = issubclass(obj, RouteBase)
                except TypeError:
                    pass

                if is_route_class or name.endswith("Routes"):
                    # Instantiate the route class
                    route_instance = obj()

                    # Extract methods from the class instance
                    for method in self.config.SUPPORTED_HTTP_METHODS:
                        if hasattr(route_instance, method):
                            handler = getattr(route_instance, method)
                            if callable(handler):
                                route_handlers[method] = handler
                    break  # Use the first matching class

            # If no class found, look for standalone functions (backward compatibility)
            if not route_handlers:
                for method in self.config.SUPPORTED_HTTP_METHODS:
                    if hasattr(module, method):
                        handler = getattr(module, method)
                        if callable(handler):
                            route_handlers[method] = handler

            # Store the handlers for this route
            if route_handlers:
                self.routes[route_path] = {
                    "handlers": route_handlers,
                    "instance": route_instance  # Store instance for lifecycle hooks
                }
                if self.config.VERBOSE_LOGGING:
                    route_type = "class-based" if route_instance else "function-based"
                    print(f"Registered {route_type} route: {route_path} with methods: {list(route_handlers.keys())}")

    def get_route_handler(self, path: str, method: str) -> Callable:
        """
        Get the handler function for a specific route and HTTP method.

        Args:
            path: Route path (e.g., "/user")
            method: HTTP method (e.g., "GET")

        Returns:
            Handler function for the route

        Raises:
            KeyError: If route or method not found
        """
        if path not in self.routes:
            raise KeyError(f"Route not found: {path}")

        route_data = self.routes[path]
        handlers = route_data["handlers"]

        if method.lower() not in handlers:
            raise KeyError(f"Method {method} not found for route {path}")

        return handlers[method.lower()]
