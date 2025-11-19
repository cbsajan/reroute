"""
Base Classes for REROUTE

Provides base classes that users can inherit from for their routes.
"""

from typing import Any, Dict, Optional


class RouteBase:
    """
    Base class for all routes in REROUTE.

    User routes should inherit from this class and implement
    HTTP method handlers (get, post, put, delete, etc.)

    Example:
        class UserRoutes(RouteBase):
            tag = "Users"  # Custom Swagger category/tag

            def get(self):
                return {"users": [...]}

            def post(self):
                return {"message": "User created"}
    """

    # Swagger/OpenAPI tag (category) - can be overridden in subclasses
    tag: Optional[str] = None

    def __init__(self):
        """Initialize the route. Override this for custom initialization."""
        pass

    def before_request(self) -> Optional[Dict[str, Any]]:
        """
        Hook called before any request handler.

        Can be used for:
        - Authentication checks
        - Logging
        - Request validation

        Returns:
            None to continue, or a dict to return immediately
        """
        return None

    def after_request(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook called after request handler.

        Can be used for:
        - Response modification
        - Logging
        - Adding headers

        Args:
            response: The response from the handler

        Returns:
            Modified response
        """
        return response

    def on_error(self, error: Exception) -> Dict[str, Any]:
        """
        Hook called when an error occurs.

        Args:
            error: The exception that occurred

        Returns:
            Error response
        """
        return {
            "error": str(error),
            "type": type(error).__name__
        }
