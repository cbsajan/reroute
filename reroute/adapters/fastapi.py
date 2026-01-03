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
from starlette.middleware.base import BaseHTTPMiddleware

from reroute.core.router import Router
from reroute.config import Config
from reroute.params import Query, Path as PathParam, Header, Body, Cookie, Form, File, ParamBase
from reroute.security import SecurityHeadersConfig, SecurityHeadersFactory, detect_environment


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for adding comprehensive security headers.

    This middleware adds OWASP-compliant security headers to all HTTP responses
    to protect against client-side attacks including XSS, clickjacking, and
    content injection attacks.
    """

    def __init__(self, app, security_config: SecurityHeadersConfig):
        """
        Initialize the security headers middleware.

        Args:
            app: FastAPI application instance
            security_config: Security headers configuration
        """
        super().__init__(app)
        self.security_config = security_config

    async def dispatch(self, request: Request, call_next):
        """
        Process request and add security headers to response.

        Args:
            request: Incoming request
            call_next: Next middleware in the chain

        Returns:
            Response with security headers added
        """
        # Call the next middleware in the chain
        response = await call_next(request)

        # Get security headers from configuration
        security_headers = self.security_config.get_security_headers()

        # Add security headers to response
        for header_name, header_value in security_headers.items():
            response.headers[header_name] = header_value

        return response


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

        # Apply OpenAPI configuration
        self._setup_openapi_paths()

        # Setup security headers (before CORS to ensure proper ordering)
        self._setup_security_headers()

        # Setup CORS
        self._setup_cors()

        # Setup request size limiting
        self._setup_request_size_limits()

        # Setup health check endpoint
        self._setup_health_check()

    def _setup_security_headers(self) -> None:
        """
        COMPREHENSIVE SECURITY HEADERS - OWASP-compliant protection.

        REROUTE provides comprehensive security headers by default with environment-specific
        configurations. Maximum protection in production, developer-friendly in development.
        """
        # Check if security headers are explicitly disabled
        security_enabled = getattr(self.config, 'SECURITY_HEADERS_ENABLED', True)
        if not security_enabled:
            return

        # Auto-detect environment for appropriate security level
        environment = detect_environment()

        # Create comprehensive security configuration
        security_config = SecurityHeadersFactory.create_default(environment=environment)

        # Customize based on configuration if available
        if hasattr(self.config, 'SECURITY_CSP_ENABLED'):
            if not self.config.SECURITY_CSP_ENABLED:
                security_config.csp = None

        if hasattr(self.config, 'SECURITY_HSTS_MAX_AGE'):
            security_config.hsts_max_age = self.config.SECURITY_HSTS_MAX_AGE

        if hasattr(self.config, 'SECURITY_X_FRAME_OPTIONS'):
            security_config.x_frame_options = self.config.SECURITY_X_FRAME_OPTIONS

        # Add CDN domains if configured
        if hasattr(self.config, 'SECURITY_CDN_DOMAINS') and self.config.SECURITY_CDN_DOMAINS:
            if security_config.csp:
                for domain in self.config.SECURITY_CDN_DOMAINS:
                    # Add to relevant CSP directives using get_directive + add_source
                    for directive_name in ['default-src', 'script-src', 'style-src', 'img-src']:
                        directive = security_config.csp.get_directive(directive_name)
                        if directive:
                            directive.add_source(domain)

        # Add API domains if configured
        if hasattr(self.config, 'SECURITY_API_DOMAINS') and self.config.SECURITY_API_DOMAINS:
            if security_config.csp:
                for domain in self.config.SECURITY_API_DOMAINS:
                    connect_src = security_config.csp.get_directive('connect-src')
                    if connect_src:
                        connect_src.add_source(domain)

        # Apply the comprehensive security middleware
        self.app.add_middleware(SecurityHeadersMiddleware, security_config=security_config)

    def _setup_health_check(self) -> None:
        """Setup health check endpoint for load balancers."""
        if not self.config.HEALTH_CHECK_ENABLED:
            return

        health_path = self.config.HEALTH_CHECK_PATH

        @self.app.get(health_path, tags=["Health"], include_in_schema=True)
        async def health_check():
            """
            Health check endpoint for load balancers and monitoring.

            Returns:
                200 OK with status information
            """
            return {
                "status": "healthy",
                "service": self.app.title or "REROUTE API",
                "version": self.app.version or "1.0.0"
            }

        # Add a protected health endpoint with detailed status (requires auth)
        if hasattr(self.config, 'HEALTH_CHECK_AUTHENTICATED') and self.config.HEALTH_CHECK_AUTHENTICATED:
            from reroute.decorators import requires

            @self.app.get(f"{health_path}/detailed", tags=["Health"], include_in_schema=True)
            @requires(roles="admin", check_func=lambda req: True)  # Require admin role
            async def detailed_health_check(request):
                """
                Detailed health check with system metrics (admin only).
                """
                import psutil
                import time

                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')

                return {
                    "status": "healthy",
                    "service": self.app.title or "REROUTE API",
                    "version": self.app.version or "1.0.0",
                    "timestamp": time.time(),
                    "system": {
                        "cpu_percent": cpu_percent,
                        "memory": {
                            "total": memory.total,
                            "available": memory.available,
                            "percent": memory.percent
                        },
                        "disk": {
                            "total": disk.total,
                            "free": disk.free,
                            "percent": (disk.used / disk.total) * 100
                        }
                    }
                }

        if self.config.VERBOSE_LOGGING:
            print(f"[OK] Health check endpoint: {health_path}")

    def _setup_request_size_limits(self) -> None:
        """Setup request size limiting middleware to prevent DoS attacks."""
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.responses import JSONResponse

        # Default to 16MB if not configured
        max_request_size = getattr(self.config, 'MAX_REQUEST_SIZE', 16 * 1024 * 1024)  # 16MB

        class RequestSizeMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                # Check Content-Length for requests with body
                content_length = request.headers.get("content-length")
                if content_length:
                    try:
                        content_length_value = int(content_length)
                        if content_length_value > max_request_size:
                            return JSONResponse(
                                status_code=413,
                                content={
                                    "error": "Request Entity Too Large",
                                    "max_size": max_request_size,
                                    "received": content_length_value
                                }
                            )
                    except ValueError:
                        # Invalid Content-Length header
                        return JSONResponse(
                            status_code=400,
                            content={"error": "Invalid Content-Length header"}
                        )

                # For chunked requests, we need to check during streaming
                # This is a basic protection - full protection would require
                # streaming body size checking which is more complex
                response = await call_next(request)
                return response

        # Add the middleware to the FastAPI app
        self.app.add_middleware(RequestSizeMiddleware)

        if self.config.VERBOSE_LOGGING:
            print(f"[OK] Request size limit: {max_request_size / (1024*1024):.1f}MB")

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
                    # Handle async before_request hooks
                    if inspect.iscoroutine(before_result):
                        before_result = await before_result
                    if before_result is not None:
                        return JSONResponse(content=before_result)

                # Extract parameters from request based on handler signature
                params = await self._extract_request_data(request, handler)

                # Call the actual handler with extracted parameters
                # Check if handler is async and await accordingly
                if inspect.iscoroutinefunction(handler):
                    result = await handler(**params)
                else:
                    result = handler(**params)

                # Call after_request hook if exists
                if route_instance and hasattr(route_instance, 'after_request'):
                    result = route_instance.after_request(result)
                    # Handle async after_request hooks
                    if inspect.iscoroutine(result):
                        result = await result

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

    def _setup_openapi_paths(self) -> None:
        """
        Apply custom OpenAPI documentation paths and metadata from configuration.

        Respects None values for individual endpoints:
        - DOCS_PATH = None -> disables Swagger UI
        - REDOC_PATH = None -> disables ReDoc UI
        - JSON_PATH = None -> disables OpenAPI JSON endpoint

        Also sets API metadata (title, version, description) from config.
        """
        if hasattr(self.config, 'OpenAPI'):
            # Set docs URLs based on config
            if self.config.OpenAPI.ENABLE:
                # Apply API metadata from config
                if hasattr(self.config.OpenAPI, 'TITLE') and self.config.OpenAPI.TITLE:
                    self.app.title = self.config.OpenAPI.TITLE
                if hasattr(self.config.OpenAPI, 'VERSION') and self.config.OpenAPI.VERSION:
                    self.app.version = self.config.OpenAPI.VERSION
                if hasattr(self.config.OpenAPI, 'DESCRIPTION') and self.config.OpenAPI.DESCRIPTION:
                    self.app.description = self.config.OpenAPI.DESCRIPTION

                # Respect None values for individual endpoints
                self.app.docs_url = self.config.OpenAPI.DOCS_PATH if self.config.OpenAPI.DOCS_PATH else None
                self.app.redoc_url = self.config.OpenAPI.REDOC_PATH if self.config.OpenAPI.REDOC_PATH else None
                self.app.openapi_url = self.config.OpenAPI.JSON_PATH if self.config.OpenAPI.JSON_PATH else None
            else:
                # Disable all docs if OpenAPI is disabled
                self.app.docs_url = None
                self.app.redoc_url = None
                self.app.openapi_url = None

            # Remove routes for disabled endpoints
            # FastAPI may have already registered routes with default URLs
            routes_to_remove = []
            for route in self.app.routes:
                if hasattr(route, 'path'):
                    # Check if this is a docs route that should be disabled
                    if self.app.docs_url is None and route.path in ['/docs', '/docs/oauth2-redirect']:
                        routes_to_remove.append(route)
                    elif self.app.redoc_url is None and route.path == '/redoc':
                        routes_to_remove.append(route)
                    elif self.app.openapi_url is None and route.path == '/openapi.json':
                        routes_to_remove.append(route)

            # Remove disabled routes
            for route in routes_to_remove:
                self.app.routes.remove(route)

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

    def run_server(self, project_name: Optional[str] = None, **uvicorn_kwargs) -> None:
        """
        Run the FastAPI application server with uvicorn.

        This is a convenience method that:
        - Checks port availability
        - Shows formatted startup messages
        - Passes configuration to uvicorn
        - Allows overriding config values via kwargs

        Args:
            project_name: Optional project name for display
            **uvicorn_kwargs: Additional uvicorn parameters (override config values)
                Common parameters:
                - host (str): Host to bind (default: from config.HOST)
                - port (int): Port to bind (default: from config.PORT)
                - reload (bool): Enable auto-reload (default: from config.AUTO_RELOAD)
                - workers (int): Number of worker processes
                - log_level (str): Logging level ("critical", "error", "warning", "info", "debug", "trace")
                - access_log (bool): Enable access log
                - use_colors (bool): Enable colored logging
                - proxy_headers (bool): Enable X-Forwarded-Proto, X-Forwarded-For headers
                - forwarded_allow_ips (str): Comma-separated list of IPs to trust with proxy headers

        Examples:
            # Basic usage
            adapter.run_server()

            # Override port
            adapter.run_server(port=8080)

            # Custom log level and workers
            adapter.run_server(workers=4, log_level="debug")

            # Disable reload even if config has AUTO_RELOAD=True
            adapter.run_server(reload=False)
        """
        try:
            import uvicorn
        except ImportError:
            raise ImportError(
                "uvicorn is not installed. Install it with: pip install reroute[fastapi]"
            )

        from reroute.utils import ensure_port_available

        # Get configuration defaults (can be overridden by uvicorn_kwargs)
        HOST = getattr(self.config, 'HOST', '0.0.0.0')
        PORT = getattr(self.config, 'PORT', 8000)
        RELOAD = getattr(self.config, 'AUTO_RELOAD', False)

        # Merge uvicorn arguments (kwargs override config)
        uvicorn_config = {
            "host": HOST,
            "port": PORT,
            "reload": RELOAD,
            **uvicorn_kwargs  # User kwargs take precedence
        }

        # Get final values after merge
        final_host = uvicorn_config.get("host", HOST)
        final_port = uvicorn_config.get("port", PORT)
        final_reload = uvicorn_config.get("reload", RELOAD)

        # Check port availability
        ensure_port_available(final_host, final_port)

        # Display startup banner (auto-detect from FastAPI app title if not provided)
        if not project_name:
            project_name = getattr(self.app, 'title', None) or "REROUTE Application"

        print("\n" + "="*50)
        print(f"{project_name} - REROUTE + FastAPI")
        print("="*50)
        print("\nStarting server...")

        # Show docs URLs if OpenAPI is enabled and paths are configured
        if hasattr(self.config, 'OpenAPI') and self.config.OpenAPI.ENABLE:
            docs_shown = False
            if self.config.OpenAPI.DOCS_PATH:
                print(f"API Docs (Swagger): http://localhost:{final_port}{self.config.OpenAPI.DOCS_PATH}")
                docs_shown = True
            if self.config.OpenAPI.REDOC_PATH:
                print(f"API Docs (ReDoc):   http://localhost:{final_port}{self.config.OpenAPI.REDOC_PATH}")
                docs_shown = True
            if self.config.OpenAPI.JSON_PATH:
                print(f"OpenAPI Spec:       http://localhost:{final_port}{self.config.OpenAPI.JSON_PATH}")
                docs_shown = True
            if not docs_shown:
                print("API Docs: Disabled (all paths set to None)")

        print(f"Health Check: http://localhost:{final_port}/health")
        print("\n")

        # When reload is enabled, uvicorn requires an import string instead of app object
        # Try to detect the import path, otherwise disable reload with a warning
        if final_reload:
            import inspect
            import sys

            # Try to find the module where run_server was called from
            frame = inspect.currentframe()
            caller_frame = frame.f_back  # Get caller's frame
            caller_module = inspect.getmodule(caller_frame)

            if caller_module and hasattr(caller_module, '__file__') and caller_module.__file__:
                # Extract module name from file path
                import os
                module_file = os.path.abspath(caller_module.__file__)
                module_name = os.path.basename(module_file).replace('.py', '')

                # Find the app variable name in the caller's local scope
                app_var_name = None
                for var_name, var_value in caller_frame.f_locals.items():
                    if var_value is self:
                        # Found the adapter variable, now find app
                        if hasattr(var_value, 'app') and var_value.app is self.app:
                            # Look for the app variable
                            for app_var, app_val in caller_frame.f_globals.items():
                                if app_val is self.app:
                                    app_var_name = app_var
                                    break
                            break

                # Default to 'app' if we can't find the variable name
                if not app_var_name:
                    app_var_name = 'app'

                # Construct import string (e.g., "main:app")
                app_import_string = f"{module_name}:{app_var_name}"

                print(f"[INFO] Auto-reload enabled: {app_import_string}\n")

                # Start server with import string
                uvicorn.run(app_import_string, **uvicorn_config)
            else:
                # Can't determine import path, disable reload
                print("[WARNING] Could not determine import path for reload. Disabling auto-reload.\n")
                uvicorn_config["reload"] = False
                uvicorn.run(self.app, **uvicorn_config)
        else:
            # Start server normally without reload
            uvicorn.run(self.app, **uvicorn_config)
