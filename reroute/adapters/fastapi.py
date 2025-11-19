"""
FastAPI Adapter for REROUTE

Integrates REROUTE's file-based routing with FastAPI.
"""

from pathlib import Path
from typing import Optional, Dict, Any, Type
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from reroute.core.router import Router
from reroute.config import Config


class FastAPIAdapter:
    """
    Adapter to integrate REROUTE routing with FastAPI.

    This adapter:
    1. Discovers routes using REROUTE's Router
    2. Registers them as FastAPI endpoints
    3. Handles request/response conversion

    Example:
        app = FastAPI()
        adapter = FastAPIAdapter(app, app_dir="./app")
        adapter.register_routes()

        # Now you can run: uvicorn main:app --reload
    """

    def __init__(
        self,
        fastapi_app: FastAPI,
        app_dir: Path = Path("./app"),
        config: Optional[Type[Config]] = None
    ):
        """
        Initialize the FastAPI adapter.

        Args:
            fastapi_app: FastAPI application instance
            app_dir: Path to the app directory containing routes/
            config: REROUTE configuration (optional)
        """
        self.app = fastapi_app
        self.app_dir = Path(app_dir)
        self.config = config or Config
        self.router = Router(self.app_dir, config=self.config)
        self._setup_cors()

    def register_routes(self) -> None:
        """
        Discover and register all REROUTE routes with FastAPI.

        This method:
        1. Discovers routes using REROUTE Router
        2. Loads route handlers
        3. Registers each route with FastAPI
        """
        # Discover and load routes
        self.router.load_routes()

        # Register each route with FastAPI
        for route_path, route_data in self.router.routes.items():
            handlers = route_data["handlers"]
            route_instance = route_data.get("instance")

            # Register each HTTP method for this route
            for method, handler in handlers.items():
                self._register_fastapi_route(
                    route_path,
                    method.upper(),
                    handler,
                    route_instance
                )

        if self.config.VERBOSE_LOGGING:
            print(f"\n[OK] Registered {len(self.router.routes)} REROUTE routes with FastAPI")

    def _register_fastapi_route(
        self,
        path: str,
        method: str,
        handler: callable,
        route_instance: Optional[Any] = None
    ) -> None:
        """
        Register a single route with FastAPI.

        Args:
            path: Route path (e.g., "/user")
            method: HTTP method (GET, POST, etc.)
            handler: The handler function
            route_instance: Route class instance (if class-based)
        """
        # Determine Swagger tag/category
        tag = self._get_route_tag(path, route_instance)
        # Apply base path if configured
        base_path = getattr(self.config, 'API_BASE_PATH', '')
        if base_path:
            # Ensure base path starts with / and doesn't end with /
            base_path = base_path.strip()
            if not base_path.startswith('/'):
                base_path = '/' + base_path
            if base_path.endswith('/'):
                base_path = base_path[:-1]

            # Combine base path with route path
            full_path = base_path + path
        else:
            full_path = path

        async def fastapi_handler(request: Request):
            try:
                # Call before_request hook if exists
                if route_instance and hasattr(route_instance, 'before_request'):
                    before_result = route_instance.before_request()
                    if before_result is not None:
                        return JSONResponse(content=before_result)

                # Call the actual handler
                # TODO: Pass request data to handler (body, params, etc.)
                result = handler()

                # Call after_request hook if exists
                if route_instance and hasattr(route_instance, 'after_request'):
                    result = route_instance.after_request(result)

                return JSONResponse(content=result)

            except Exception as e:
                # Call error hook if exists
                if route_instance and hasattr(route_instance, 'on_error'):
                    error_response = route_instance.on_error(e)
                    return JSONResponse(content=error_response, status_code=500)

                # Default error response
                return JSONResponse(
                    content={"error": str(e), "type": type(e).__name__},
                    status_code=500
                )

        # Copy docstring from original handler to wrapper for FastAPI docs
        if handler.__doc__:
            fastapi_handler.__doc__ = handler.__doc__

        # Extract summary from docstring for FastAPI
        summary = handler.__doc__.strip() if handler.__doc__ else None

        # Register with FastAPI using the appropriate method with summary and tags
        tags = [tag] if tag else None

        if method == "GET":
            self.app.get(full_path, summary=summary, tags=tags)(fastapi_handler)
        elif method == "POST":
            self.app.post(full_path, summary=summary, tags=tags)(fastapi_handler)
        elif method == "PUT":
            self.app.put(full_path, summary=summary, tags=tags)(fastapi_handler)
        elif method == "DELETE":
            self.app.delete(full_path, summary=summary, tags=tags)(fastapi_handler)
        elif method == "PATCH":
            self.app.patch(full_path, summary=summary, tags=tags)(fastapi_handler)
        elif method == "HEAD":
            self.app.head(full_path, summary=summary, tags=tags)(fastapi_handler)
        elif method == "OPTIONS":
            self.app.options(full_path, summary=summary, tags=tags)(fastapi_handler)

        if self.config.VERBOSE_LOGGING:
            print(f"  {method:7} {full_path}")

    def _setup_cors(self) -> None:
        """
        Setup CORS middleware globally based on configuration.
        """
        if getattr(self.config, 'ENABLE_CORS', True):
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=getattr(self.config, 'CORS_ALLOW_ORIGINS', ["*"]),
                allow_credentials=getattr(self.config, 'CORS_ALLOW_CREDENTIALS', False),
                allow_methods=getattr(self.config, 'CORS_ALLOW_METHODS', ["*"]),
                allow_headers=getattr(self.config, 'CORS_ALLOW_HEADERS', ["*"]),
            )

    def _get_route_tag(self, path: str, route_instance: Optional[Any] = None) -> Optional[str]:
        """
        Determine the Swagger tag/category for a route.

        Priority:
        1. Custom tag defined in route class
        2. Route folder name (e.g., /users -> "Users", /api/posts -> "Posts")
        3. None (no tag)

        Args:
            path: Route path
            route_instance: Route class instance

        Returns:
            Tag name or None
        """
        # Check if route has custom tag
        if route_instance and hasattr(route_instance, 'tag') and route_instance.tag:
            return route_instance.tag

        # Use folder-based tag (last meaningful segment)
        path_parts = [p for p in path.strip('/').split('/') if p]
        if path_parts:
            # Use the last part as tag (e.g., /api/users -> "Users")
            return path_parts[-1].capitalize()

        return None

    def add_route_manually(
        self,
        path: str,
        handler: callable,
        methods: list = ["GET"]
    ) -> None:
        """
        Manually add a route to FastAPI (outside of REROUTE's file-based routing).

        Useful for adding custom routes like health checks, webhooks, etc.

        Args:
            path: Route path
            handler: Handler function
            methods: List of HTTP methods

        Example:
            def health():
                return {"status": "healthy"}

            adapter.add_route_manually("/health", health, methods=["GET"])
        """
        for method in methods:
            self._register_fastapi_route(path, method.upper(), handler, None)
