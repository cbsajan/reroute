"""
Flask Adapter for REROUTE

Integrates REROUTE's file-based routing with Flask.
"""

import inspect
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Type, get_type_hints

logger = logging.getLogger(__name__)

# Initialize colorama for Windows console colors
try:
    import colorama
    # Force strip=False to keep colors even when output is redirected
    colorama.init(autoreset=True, strip=False)
except ImportError:
    pass

import click
from reroute.core.router import Router
from reroute.config import Config
from reroute.params import Query, Path as PathParam, Header, Body, Cookie, Form, File, ParamBase
from reroute.security import SecurityHeadersConfig, SecurityHeadersFactory, detect_environment


class FlaskSecurityHeadersMiddleware:
    """
    Flask middleware for adding comprehensive security headers.

    This middleware adds OWASP-compliant security headers to all HTTP responses
    to protect against client-side attacks including XSS, clickjacking, and
    content injection attacks.
    """

    def __init__(self, app, security_config: SecurityHeadersConfig):
        """
        Initialize the security headers middleware.

        Args:
            app: Flask application instance
            security_config: Security headers configuration
        """
        self.app = app
        self.security_config = security_config

        # Register the after_request handler
        self.app.after_request(self._add_security_headers)

    def _add_security_headers(self, response):
        """
        Add security headers to the Flask response.

        Args:
            response: Flask response object

        Returns:
            Response with security headers added
        """
        # Get security headers from configuration
        security_headers = self.security_config.get_security_headers()

        # Add security headers to response
        for header_name, header_value in security_headers.items():
            response.headers[header_name] = header_value

        return response


class FlaskAdapter:
    """
    Adapter to integrate REROUTE routing with Flask.

    This adapter:
    1. Discovers routes using REROUTE's Router
    2. Registers them as Flask endpoints
    3. Handles request/response conversion
    4. Optionally provides OpenAPI documentation

    Example:
        from flask import Flask
        from reroute import FlaskAdapter
        from config import DevConfig

        app = Flask(__name__)
        adapter = FlaskAdapter(app, app_dir="./app", config=DevConfig)
        adapter.register_routes()

        # Now you can run: python main.py
    """

    def __init__(
        self,
        flask_app,
        app_dir: Path = Path("./app"),
        config: Optional[Type[Config]] = None
    ):
        """
        Initialize the Flask adapter.

        Args:
            flask_app: Flask application instance
            app_dir: Path to the app directory containing routes/
            config: REROUTE configuration (optional)
        """
        self.config = config or Config
        self.app_dir = Path(app_dir)
        self.app = flask_app
        self.router = Router(self.app_dir, config=self.config)

        # Import Flask-specific dependencies
        try:
            from flask import request, jsonify
            self.request = request
            self.jsonify = jsonify
        except ImportError:
            raise ImportError(
                "Flask is not installed. Install it with: pip install reroute[flask]"
            )

        # Initialize Spectree for OpenAPI if enabled
        if self.config.OpenAPI.ENABLE:
            try:
                from spectree import SpecTree, Response

                # Auto-generate title from Flask app name if not provided
                api_title = self.config.OpenAPI.TITLE
                if api_title is None:
                    api_title = getattr(flask_app, 'name', 'API').replace('_', ' ').title()

                # Auto-generate description if not provided
                api_description = self.config.OpenAPI.DESCRIPTION
                if api_description is None:
                    api_description = f"{api_title} - Built with REROUTE"

                # Import page templates and disable ReDoc (broken CDN URL)
                from spectree import page

                # Extract base path from DOCS_PATH for Spectree
                # Spectree appends /swagger/, /scalar/, etc. to the base path
                # IMPORTANT: path must NOT be empty string, or Spectree filters out ALL routes
                # If DOCS_PATH is "/docs", use "apidoc" -> generates /apidoc/swagger/
                # If DOCS_PATH is "/api/docs", use "api" -> generates /api/swagger/
                docs_path = self.config.OpenAPI.DOCS_PATH
                if docs_path:
                    # Extract first meaningful segment (e.g., "/api/docs" -> "api", "/docs" -> "docs")
                    segments = [s for s in docs_path.strip('/').split('/') if s]
                    base_path = segments[0] if segments else 'apidoc'
                else:
                    # Default fallback
                    base_path = 'apidoc'

                # Warn if JSON_PATH is configured (Flask/Spectree derives it from DOCS_PATH)
                json_path = getattr(self.config.OpenAPI, 'JSON_PATH', None)
                if json_path:
                    click.secho(f"[WARNING] OpenAPI.JSON_PATH is ignored in Flask adapter", fg='yellow')
                    click.secho(f"          JSON spec is auto-generated at: /{base_path}/openapi.json", fg='yellow')

                # Fix Spectree template bug: Spectree registers route as //openapi.json when path=''
                # This causes browser to treat it as protocol-relative URL (breaks)
                # Solution: Use window.location.origin + cleaned spec_url
                swagger_template = page.PAGE_TEMPLATES['swagger']
                swagger_template_fixed = swagger_template.replace(
                    'url: "{spec_url}"',
                    'url: window.location.origin + "{spec_url}".replace(/\\/\\//g, "/")'
                )

                # Create custom page templates without ReDoc
                custom_page_templates = {
                    'swagger': swagger_template_fixed,
                    'scalar': page.PAGE_TEMPLATES['scalar']
                    # ReDoc is disabled - CDN URL is broken (redoc@next returns 404)
                }

                self.spec = SpecTree(
                    'flask',
                    title=api_title,
                    version=self.config.OpenAPI.VERSION,
                    path=base_path,
                    MODE='strict',
                    page_templates=custom_page_templates
                )

                # Store base path for startup message
                self._spec_base_path = base_path

                self.Response = Response
            except ImportError:
                click.secho("\n[ERROR] spectree is required when Config.OpenAPI.ENABLE = True", fg='red', bold=True)
                click.secho("        Install it with: pip install -r requirements.txt", fg='yellow')
                click.secho("        Or disable OpenAPI in config.py: OpenAPI.ENABLE = False\n", fg='yellow')
                sys.exit(1)
        else:
            self.spec = None
            self.Response = None

        # Dynamically create HTTP method decorators from Internal.SUPPORTED_HTTP_METHODS
        # Methods are created in lowercase (get, post, etc.) but passed uppercase to Flask
        for method in self.config.Internal.SUPPORTED_HTTP_METHODS:
            method_lower = method.lower()  # Ensure lowercase for decorator name
            method_upper = method.upper()  # Uppercase for Flask HTTP method
            setattr(self, method_lower, self._create_method_decorator(method_upper))

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
        FlaskSecurityHeadersMiddleware(self.app, security_config)

    def _setup_health_check(self) -> None:
        """Setup health check endpoint for load balancers."""
        if not self.config.HEALTH_CHECK_ENABLED:
            return

        health_path = self.config.HEALTH_CHECK_PATH

        @self.app.route(health_path, methods=['GET'])
        def health_check():
            """Health check endpoint for load balancers and monitoring."""
            return self.jsonify({
                "status": "healthy",
                "service": self.app.name or "REROUTE API",
                "version": getattr(self.config.OpenAPI, 'VERSION', '1.0.0') if hasattr(self.config, 'OpenAPI') else '1.0.0'
            })

        # Add a protected health endpoint with detailed status (requires auth)
        if hasattr(self.config, 'HEALTH_CHECK_AUTHENTICATED') and self.config.HEALTH_CHECK_AUTHENTICATED:
            from reroute.decorators import requires

            @self.app.route(f"{health_path}/detailed", methods=['GET'])
            @requires(roles="admin", check_func=lambda req: True)  # Require admin role
            def detailed_health_check():
                """Detailed health check with system metrics (admin only)."""
                try:
                    import psutil
                    import time

                    # Get system metrics
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()
                    disk = psutil.disk_usage('/')

                    return self.jsonify({
                        "status": "healthy",
                        "service": self.app.name or "REROUTE API",
                        "version": getattr(self.config.OpenAPI, 'VERSION', '1.0.0') if hasattr(self.config, 'OpenAPI') else '1.0.0',
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
                    })
                except ImportError:
                    return self.jsonify({
                        "status": "healthy",
                        "service": self.app.name or "REROUTE API",
                        "version": getattr(self.config.OpenAPI, 'VERSION', '1.0.0') if hasattr(self.config, 'OpenAPI') else '1.0.0',
                        "message": "Install psutil for detailed metrics: pip install psutil"
                    })

        if self.config.VERBOSE_LOGGING:
            click.secho(f"[OK] Health check endpoint: {health_path}", fg='green')

    def _setup_request_size_limits(self) -> None:
        """Setup request size limiting to prevent DoS attacks."""
        # Default to 16MB if not configured
        max_request_size = getattr(self.config, 'MAX_REQUEST_SIZE', 16 * 1024 * 1024)  # 16MB

        @self.app.before_request
        def check_request_size():
            """Check request size before processing."""
            # Check Content-Length for requests with body
            content_length = self.request.headers.get("content-length")
            if content_length:
                try:
                    content_length_value = int(content_length)
                    if content_length_value > max_request_size:
                        return self.jsonify({
                            "error": "Request Entity Too Large",
                            "max_size": max_request_size,
                            "received": content_length_value
                        }), 413
                except ValueError:
                    # Invalid Content-Length header
                    return self.jsonify({
                        "error": "Invalid Content-Length header"
                    }), 400

        if self.config.VERBOSE_LOGGING:
            click.secho(f"[OK] Request size limit: {max_request_size / (1024*1024):.1f}MB", fg='green')

    def register_routes(self) -> None:
        """
        Discover and register all REROUTE file-based routes with Flask.

        This method:
        1. Discovers routes using REROUTE Router
        2. Loads route handlers
        3. Registers each route with Flask
        """
        # Discover and load routes
        self.router.load_routes()

        # Register all routes
        for route_path, route_data in self.router.routes.items():
            handlers = route_data["handlers"]
            route_instance = route_data.get("instance")

            # Register each HTTP method for this route
            for method, handler in handlers.items():
                self._register_flask_route(
                    route_path,
                    method.upper(),
                    handler,
                    route_instance
                )

        # Register Spectree (enables /apidoc/* endpoints)
        if self.spec:
            self.spec.register(self.app)

        if self.config.VERBOSE_LOGGING:
            print(f"\n[OK] Registered {len(self.router.routes)} REROUTE routes with Flask")
            print(f"\nAll registered routes:")
            for rule in self.app.url_map.iter_rules():
                print(f"  {rule.rule} -> {rule.methods}")

    def _create_method_decorator(self, http_method: str):
        """
        Factory to create HTTP method-specific decorators.

        Args:
            http_method: HTTP method name (GET, POST, etc.)

        Returns:
            Decorator function for the specified HTTP method
        """
        def method_decorator(path, **options):
            """Decorator for {http_method} requests"""
            def wrapper(func):
                # Extract validation from function signature
                validation = {}
                if self.spec:
                    validation = self._extract_validation(func)

                # Apply Spectree validation if OpenAPI enabled
                if self.spec and validation:
                    validated_func = self.spec.validate(**validation, **options)(func)
                else:
                    validated_func = func

                # Create unique endpoint name
                endpoint_name = f"{path}_{http_method}".replace('/', '_').strip('_')

                # Register with Flask
                self.app.add_url_rule(
                    path,
                    endpoint=endpoint_name,
                    view_func=validated_func,
                    methods=[http_method]
                )

                return validated_func
            return wrapper

        # Set proper function metadata for IDE hints
        method_decorator.__name__ = http_method.lower()
        method_decorator.__doc__ = f"Decorator for {http_method} requests"

        return method_decorator

    def route(self, path, methods=['GET'], **options):
        """
        Generic route decorator supporting multiple HTTP methods.

        Args:
            path: URL path for the route
            methods: List of HTTP methods (default: ['GET'])
            **options: Additional options for Spectree validation

        Returns:
            Decorator function
        """
        def decorator(func):
            # Extract validation from function signature
            validation = {}
            if self.spec:
                validation = self._extract_validation(func)

            # Apply Spectree validation if OpenAPI enabled
            if self.spec and validation:
                validated_func = self.spec.validate(**validation, **options)(func)
            else:
                validated_func = func

            # Create unique endpoint name
            endpoint_name = f"{path}_{'_'.join(methods)}".replace('/', '_').strip('_')

            # Register with Flask
            self.app.add_url_rule(
                path,
                endpoint=endpoint_name,
                view_func=validated_func,
                methods=methods
            )

            return validated_func
        return decorator

    def _extract_validation(self, func):
        """
        Extract Spectree validation models from REROUTE params and type hints.

        Args:
            func: Handler function to extract validation from

        Returns:
            Dictionary with validation models for Spectree
        """
        try:
            from pydantic import BaseModel, create_model, Field
        except ImportError:
            return {}

        sig = inspect.signature(func)
        validation = {}

        # Collect query parameters
        query_fields = {}
        json_model = None

        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            annotation = param.annotation if param.annotation != inspect.Parameter.empty else str

            # Check for REROUTE parameter types
            if isinstance(param.default, Query):
                # Build field definition for Pydantic
                field_default = param.default.default if param.default.default is not ... else ...
                field_info = Field(default=field_default, description=param.default.description or "")
                query_fields[param_name] = (annotation, field_info)

            elif isinstance(param.default, Body):
                # If Body param, use the annotation as the model
                if hasattr(annotation, '__mro__') and BaseModel in annotation.__mro__:
                    json_model = annotation

            # Check if parameter is type-hinted with a Pydantic model directly
            elif hasattr(annotation, '__mro__') and BaseModel in annotation.__mro__:
                json_model = annotation

        # Create dynamic query model if needed
        if query_fields:
            QueryModel = create_model(f'{func.__name__}_Query', **query_fields)
            validation['query'] = QueryModel

        if json_model:
            validation['json'] = json_model

        # Add a default response model if none exists
        # This ensures ALL routes appear in Swagger UI, even without explicit models
        if self.Response and not validation:
            # Create a generic response model for routes without validation
            GenericResponse = create_model(
                f'{func.__name__}_Response',
                __base__=BaseModel,
                **{'data': (dict, Field(default={}, description="Response data"))}
            )
            validation['resp'] = self.Response(HTTP_200=GenericResponse)

        return validation

    def _extract_request_data(self, handler: callable, **path_params) -> Dict[str, Any]:
        """
        Extract request data based on handler parameter annotations.

        Args:
            handler: The handler function to extract parameters for
            **path_params: Path parameters from route

        Returns:
            Dictionary of parameter names to extracted values
        """
        extracted_params = {}

        # Get handler signature
        sig = inspect.signature(handler)

        # Get query parameters
        query_params = dict(self.request.args)

        # Get headers
        headers = dict(self.request.headers)

        # Get cookies
        cookies = dict(self.request.cookies)

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
                value = headers.get(header_key) or headers.get(header_key.lower())
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
                    body_data = self.request.get_json(silent=True) or {}
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
                    value = self.request.form.get(param_name)
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
                    value = self.request.files.get(param_name)
                    if value is None and default_value.default is not ...:
                        value = default_value.default
                    elif value is None and default_value.required:
                        raise ValueError(f"Required file '{param_name}' is missing")
                    extracted_params[param_name] = value
                except Exception as e:
                    if default_value.required:
                        raise ValueError(f"Invalid file upload for parameter '{param_name}': {str(e)}")

        return extracted_params

    def _register_flask_route(
        self,
        path: str,
        method: str,
        handler: callable,
        route_instance: Optional[Any] = None
    ) -> None:
        """
        Register a single route with Flask.

        Args:
            path: Route path (e.g., "/user")
            method: HTTP method (GET, POST, etc.)
            handler: The handler function
            route_instance: Route class instance (if class-based)
        """
        # Determine Swagger tag/category
        tag = self._get_route_tag(path, route_instance)

        # Apply Spectree validation to handler FIRST (before wrapping in closure)
        # This allows Spectree to track the validated handler for OpenAPI generation
        if self.spec:
            validation = self._extract_validation(handler)
            handler = self.spec.validate(**validation, tags=[tag] if tag else [])(handler)

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

        # Convert path parameters to Flask format
        # REROUTE uses {param}, Flask uses <param>
        flask_path = full_path.replace('{', '<').replace('}', '>')

        # Warn if handler is async (Flask doesn't support async natively)
        if inspect.iscoroutinefunction(handler):
            logger.warning(
                f"Async handler detected for {method} {full_path}. "
                f"Flask does not support async handlers natively. "
                f"Consider using FastAPI instead, or use a sync handler with Flask."
            )

        def flask_handler(**path_params):
            try:
                # Call before_request hook if exists
                if route_instance and hasattr(route_instance, 'before_request'):
                    before_result = route_instance.before_request()
                    if before_result is not None:
                        # For OpenAPI, return dict directly; flask-openapi3 handles JSON conversion
                        if self.config.OpenAPI.ENABLE:
                            return before_result
                        return self.jsonify(before_result)

                # Extract parameters from request based on handler signature
                params = self._extract_request_data(handler, **path_params)

                # Call the actual handler with extracted parameters
                result = handler(**params)

                # Call after_request hook if exists
                if route_instance and hasattr(route_instance, 'after_request'):
                    result = route_instance.after_request(result)

                # For OpenAPI, return dict directly; flask-openapi3 handles JSON conversion
                if self.config.OpenAPI.ENABLE:
                    return result
                return self.jsonify(result)

            except Exception as e:
                # Call error hook if exists
                if route_instance and hasattr(route_instance, 'on_error'):
                    error_response = route_instance.on_error(e)
                    if self.config.OpenAPI.ENABLE:
                        return error_response, 500
                    return self.jsonify(error_response), 500

                # Default error response
                error_dict = {
                    "error": str(e),
                    "type": type(e).__name__
                }
                if self.config.OpenAPI.ENABLE:
                    return error_dict, 500
                return self.jsonify(error_dict), 500

        # Copy docstring from handler to wrapper for OpenAPI docs
        if handler.__doc__:
            flask_handler.__doc__ = handler.__doc__
        else:
            # Generate a basic docstring if none exists
            flask_handler.__doc__ = f"{method} {full_path}"

        # Copy Spectree metadata attributes from validated handler to flask_handler closure
        # (handler was already validated at the beginning of this function if self.spec exists)
        if self.spec:
            # These attributes are set by spec.validate() and used by Spectree for OpenAPI generation
            spectree_attrs = ['_decorator', 'deprecated', 'operation_id',
                             'path_parameter_descriptions', 'security', 'tags']
            for attr in spectree_attrs:
                if hasattr(handler, attr):
                    setattr(flask_handler, attr, getattr(handler, attr))

        # Set endpoint name to avoid conflicts (combine path + method)
        endpoint_name = f"{full_path}_{method}".replace('/', '_').replace('<', '').replace('>', '')

        # Register with Flask
        self.app.add_url_rule(
            flask_path,
            endpoint=endpoint_name,
            view_func=flask_handler,
            methods=[method]
        )

        if self.config.VERBOSE_LOGGING:
            print(f"  {method:7} {full_path}")

    def _setup_cors(self) -> None:
        """
        Setup CORS globally based on configuration.
        """
        if getattr(self.config, 'ENABLE_CORS', True):
            try:
                from flask_cors import CORS
                CORS(
                    self.app,
                    origins=getattr(self.config, 'CORS_ALLOW_ORIGINS', ["*"]),
                    supports_credentials=getattr(self.config, 'CORS_ALLOW_CREDENTIALS', False),
                    methods=getattr(self.config, 'CORS_ALLOW_METHODS', ["*"]),
                    allow_headers=getattr(self.config, 'CORS_ALLOW_HEADERS', ["*"]),
                )
            except ImportError:
                click.secho("\n[ERROR] flask-cors is required", fg='red', bold=True)
                click.secho("Install it with: ", fg='yellow', nl=False)
                click.secho("pip install -r requirements.txt", fg='yellow', bold=True)
                sys.exit(1)

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
        path_parts = [p for p in path.strip('/').split('/') if p and not p.startswith('{')]
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
        Manually add a route to Flask (outside of REROUTE's file-based routing).

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
            self._register_flask_route(path, method.upper(), handler, None)

    def run_server(self, project_name: Optional[str] = None, **flask_kwargs) -> None:
        """
        Run the Flask application server.

        This is a convenience method that:
        - Checks port availability
        - Shows formatted startup messages
        - Passes configuration to Flask's app.run()
        - Allows overriding config values via kwargs

        Args:
            project_name: Optional project name for display
            **flask_kwargs: Additional Flask parameters (override config values)
                Common parameters:
                - host (str): Host to bind (default: from config.HOST)
                - port (int): Port to bind (default: from config.PORT)
                - debug (bool): Enable debug mode (default: from config.DEBUG)
                - use_reloader (bool): Enable auto-reloader
                - use_debugger (bool): Enable debugger
                - threaded (bool): Handle requests in separate threads
                - processes (int): Number of processes to spawn

        Examples:
            # Basic usage
            adapter.run_server()

            # Override port
            adapter.run_server(port=8080)

            # Enable debug and reloader
            adapter.run_server(debug=True, use_reloader=True)

            # Disable debug even if config has DEBUG=True
            adapter.run_server(debug=False)
        """
        from reroute.utils import ensure_port_available

        # Get configuration defaults (can be overridden by flask_kwargs)
        HOST = getattr(self.config, 'HOST', '0.0.0.0')
        PORT = getattr(self.config, 'PORT', 5000)
        DEBUG = getattr(self.config, 'DEBUG', False)

        # Merge Flask arguments (kwargs override config)
        flask_config = {
            "host": HOST,
            "port": PORT,
            "debug": DEBUG,
            **flask_kwargs  # User kwargs take precedence
        }

        # Get final values after merge
        final_host = flask_config.get("host", HOST)
        final_port = flask_config.get("port", PORT)
        final_debug = flask_config.get("debug", DEBUG)

        # Check port availability
        ensure_port_available(final_host, final_port)

        # Display startup banner (auto-detect from Flask app name if not provided)
        if not project_name:
            project_name = getattr(self.app, 'name', None) or "REROUTE Application"

        print("\n" + "="*50)
        print(f"{project_name} - REROUTE + Flask")
        print("="*50)
        print("\nStarting server...")

        # Show docs URL if Spectree is enabled
        if self.spec:
            # Build paths based on Spectree base path
            base = f"/{self._spec_base_path}" if self._spec_base_path else ""
            print(f"API Docs (Swagger): http://localhost:{final_port}{base}/swagger/")
            print(f"API Docs (Scalar):  http://localhost:{final_port}{base}/scalar/")
            print(f"OpenAPI Spec:       http://localhost:{final_port}{base}/openapi.json")

        print(f"Health Check:       http://localhost:{final_port}/health")
        print("\n")

        # Start server
        self.app.run(**flask_config)
