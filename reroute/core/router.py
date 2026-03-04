"""
Router Module

Discovers and registers routes from the app/routes directory structure.
"""

from pathlib import Path
from typing import Dict, List, Callable, Optional, Any
import inspect
import logging
from reroute.core.loader import RouteLoader
from reroute.core.base import RouteBase
from reroute.core.websocket import WebSocketRoute
from reroute.config import Config

logger = logging.getLogger(__name__)


class Router:
    """
    Main routing engine for REROUTE.

    Discovers routes from folder structure and maps them to HTTP handlers.
    Supports nested routes with unlimited depth.
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
        self.routes_dir = self.app_dir / self.config.Internal.ROUTES_DIR_NAME
        self.loader = RouteLoader(self.routes_dir)
        self.routes: Dict[str, Dict[str, Callable]] = {}

    def discover_routes(self) -> List[tuple]:
        """
        Discover all route folders in the routes directory.

        Recursively scans the routes directory to find all page.py files.
        Supports nested routes with unlimited depth.

        Returns:
            List of tuples: [(folder_path, url_path), ...]

        Example:
            routes/
                user/page.py           -> ("", "/")
                product/page.py        -> ("product", "/product")
                user/profile/page.py   -> ("user/profile", "/user/profile")
                api/v1/users/page.py   -> ("api/v1/users", "/api/v1/users")
                api/users/_id/page.py  -> ("api/users/_id", "/api/users/{id}")
        """
        discovered_routes = []

        # Check if routes directory exists
        if not self.routes_dir.exists():
            return discovered_routes

        # Recursively find all page.py files
        for page_file in self.routes_dir.rglob(self.config.Internal.ROUTE_FILE_NAME):
            # Get the route path by removing routes_dir and page.py
            relative_path = page_file.parent.relative_to(self.routes_dir)

            # Skip if any parent folder is in IGNORE_FOLDERS
            if any(part in self.config.Internal.IGNORE_FOLDERS for part in relative_path.parts):
                continue

            # Get the original folder path (for file loading)
            if str(relative_path) == ".":
                # Root level route
                folder_path = ""
            else:
                # Security: Normalize and sanitize the path
                # - Replace backslashes with forward slashes
                # - Remove any ".." or "." components
                # - Collapse multiple slashes
                import posixpath
                import re
                raw_path = str(relative_path).replace("\\", "/")
                folder_path = posixpath.normpath(raw_path)
                # Ensure no path traversal attempts remain
                if ".." in folder_path or folder_path.startswith("/"):
                    logger.warning(f"Suspicious route path detected: {relative_path}")
                    continue

            # Convert to URL path (for FastAPI registration)
            # Support two patterns for dynamic path parameters:
            # 1. Underscore prefix: _id -> {id}, _user_id -> {user_id} (private/explicit)
            # 2. Bracket notation: [id] -> {id}, [user_id] -> {user_id} (Next.js style)
            if folder_path == "":
                url_path = "/"
            else:
                path_parts = folder_path.split("/")
                converted_parts = []
                for part in path_parts:
                    # Pattern 1: Underscore prefix (_id, _user_id, _slug)
                    if part.startswith("_") and len(part) > 1:
                        param_name = part[1:]  # Remove underscore
                        converted_parts.append(f"{{{param_name}}}")
                    # Pattern 2: Bracket notation ([id], [user_id], [slug])
                    elif part.startswith("[") and part.endswith("]"):
                        param_name = part[1:-1]  # Remove brackets
                        converted_parts.append(f"{{{param_name}}}")
                    else:
                        converted_parts.append(part)
                url_path = "/" + "/".join(converted_parts)

            discovered_routes.append((folder_path, url_path))

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

        for folder_path, url_path in discovered:
            # Build page file path using the original folder path
            if folder_path:
                page_file = self.routes_dir / folder_path / "page.py"
            else:
                page_file = self.routes_dir / "page.py"

            # Load the module using our secure loader
            module = self.loader.load_module(page_file)

            if module is None:
                continue

            # Extract HTTP method handlers from the module
            route_handlers = {}
            route_instance = None

            # Check if module has a class-based route
            # Look for classes that inherit from RouteBase or WebSocketRoute
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Skip imported classes (like RouteBase itself)
                if obj.__module__ != module.__name__:
                    continue

                # Check if it's a WebSocket route class
                is_websocket_class = False
                try:
                    is_websocket_class = issubclass(obj, WebSocketRoute)
                except TypeError:
                    pass

                if is_websocket_class:
                    # Instantiate the WebSocket route class
                    route_instance = obj()

                    # Store WebSocket routes without HTTP handlers
                    self.routes[url_path] = {
                        "handlers": {},  # Empty handlers dict for WebSocket
                        "instance": route_instance,
                        "type": "websocket"
                    }
                    if self.config.VERBOSE_LOGGING:
                        logger.info(f"Registered WebSocket route: {url_path}")
                    break  # Use the first matching class

                # Check if it's an HTTP route class
                is_route_class = False
                try:
                    is_route_class = issubclass(obj, RouteBase)
                except TypeError:
                    pass

                if is_route_class or name.endswith("Routes"):
                    # Instantiate the route class
                    route_instance = obj()

                    # Extract methods from the class instance
                    for method in self.config.Internal.SUPPORTED_HTTP_METHODS:
                        if hasattr(route_instance, method):
                            handler = getattr(route_instance, method)
                            if callable(handler):
                                route_handlers[method] = handler
                    break  # Use the first matching class

            # If no class found, look for standalone functions (backward compatibility)
            if not route_handlers and route_instance is None:
                for method in self.config.Internal.SUPPORTED_HTTP_METHODS:
                    if hasattr(module, method):
                        handler = getattr(module, method)
                        if callable(handler):
                            route_handlers[method] = handler

            # Store the handlers for this route (only for HTTP routes)
            if route_handlers:
                self.routes[url_path] = {
                    "handlers": route_handlers,
                    "instance": route_instance,  # Store instance for lifecycle hooks
                    "type": "http"
                }
                if self.config.VERBOSE_LOGGING:
                    route_type = "class-based" if route_instance else "function-based"
                    logger.info(f"Registered {route_type} route: {url_path} with methods: {list(route_handlers.keys())}")

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
