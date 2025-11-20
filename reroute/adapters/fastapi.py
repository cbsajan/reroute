"""
FastAPI Adapter for REROUTE

Integrates REROUTE's file-based routing with FastAPI.
"""

import inspect
from pathlib import Path
from typing import Optional, Dict, Any, Type, get_type_hints
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from reroute.core.router import Router
from reroute.config import Config
from reroute.params import Query, Path as PathParam, Header, Body, Cookie, Form, File, ParamBase


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

    async def _extract_request_data(self, request: Request, handler: callable) -> Dict[str, Any]:
        """
        Extract request data based on handler parameter annotations.

        Args:
            request: FastAPI Request object
            handler: The handler function to extract parameters for

        Returns:
            Dictionary of parameter names to extracted values
        """
        extracted_params = {}

        # Get handler signature
        sig = inspect.signature(handler)

        # Get path parameters from request
        path_params = request.path_params

        # Get query parameters
        query_params = dict(request.query_params)

        # Get headers
        headers = dict(request.headers)

        # Get cookies
        cookies = dict(request.cookies)

        # Process each parameter in the handler signature
        for param_name, param in sig.parameters.items():
            # Skip 'self' for class methods
            if param_name == 'self':
                continue

            # Get the default value (which should be our ParamBase instance)
            default_value = param.default

            # Check if this is a REROUTE parameter injection
            if isinstance(default_value, Query):
                # Extract from query parameters
                value = query_params.get(param_name)
                if value is None and default_value.default is not ...:
                    value = default_value.default
                elif value is None and default_value.required:
                    raise ValueError(f"Required query parameter '{param_name}' is missing")
                extracted_params[param_name] = value

            elif isinstance(default_value, PathParam):
                # Extract from path parameters
                value = path_params.get(param_name)
                if value is None and default_value.default is not ...:
                    value = default_value.default
                elif value is None and default_value.required:
                    raise ValueError(f"Required path parameter '{param_name}' is missing")
                extracted_params[param_name] = value

            elif isinstance(default_value, Header):
                # Extract from headers (case-insensitive)
                header_key = param_name.replace('_', '-')
                value = headers.get(header_key.lower())
                if value is None and default_value.default is not ...:
                    value = default_value.default
                elif value is None and default_value.required:
                    raise ValueError(f"Required header '{param_name}' is missing")
                extracted_params[param_name] = value

            elif isinstance(default_value, Cookie):
                # Extract from cookies
                value = cookies.get(param_name)
                if value is None and default_value.default is not ...:
                    value = default_value.default
                elif value is None and default_value.required:
                    raise ValueError(f"Required cookie '{param_name}' is missing")
                extracted_params[param_name] = value

            elif isinstance(default_value, Body):
                # Extract from request body
                try:
                    body_data = await request.json()
                    # Get the type hint for this parameter
                    type_hints = get_type_hints(handler)
                    param_type = type_hints.get(param_name)

                    # If it's a Pydantic model, instantiate it
                    if param_type and hasattr(param_type, 'model_validate'):
                        value = param_type.model_validate(body_data)
                    else:
                        value = body_data

                    extracted_params[param_name] = value
                except Exception as e:
                    if default_value.required:
                        raise ValueError(f"Invalid request body for parameter '{param_name}': {str(e)}")
                    extracted_params[param_name] = default_value.default if default_value.default is not ... else None

            elif isinstance(default_value, Form):
                # Extract from form data
                try:
                    form_data = await request.form()
                    value = form_data.get(param_name)
                    if value is None and default_value.default is not ...:
                        value = default_value.default
                    elif value is None and default_value.required:
                        raise ValueError(f"Required form field '{param_name}' is missing")
                    extracted_params[param_name] = value
                except Exception as e:
                    if default_value.required:
                        raise ValueError(f"Invalid form data for parameter '{param_name}': {str(e)}")

            elif isinstance(default_value, File):
                # Extract file upload
                try:
                    form_data = await request.form()
                    value = form_data.get(param_name)
                    if value is None and default_value.default is not ...:
                        value = default_value.default
                    elif value is None and default_value.required:
                        raise ValueError(f"Required file '{param_name}' is missing")
                    extracted_params[param_name] = value
                except Exception as e:
                    if default_value.required:
                        raise ValueError(f"Invalid file upload for parameter '{param_name}': {str(e)}")

        return extracted_params

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

                # Extract parameters from request based on handler signature
                params = await self._extract_request_data(request, handler)

                # Call the actual handler with extracted parameters
                result = handler(**params)

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
