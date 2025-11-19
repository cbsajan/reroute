"""
REROUTE Configuration

Central configuration for the REROUTE framework.
"""

from pathlib import Path
from typing import List


class Config:
    """
    Framework configuration settings.

    All important settings are defined here to make the framework
    easy to configure and maintain.
    """

    # Routing Configuration
    ROUTES_DIR_NAME = "routes"
    ROUTE_FILE_NAME = "page.py"
    API_BASE_PATH = ""  # Base path for all routes (e.g., "/api/v1")

    # Supported HTTP methods
    SUPPORTED_HTTP_METHODS = ["get", "post", "put", "delete", "patch", "head", "options"]

    # Security Configuration
    ENABLE_PATH_VALIDATION = True
    ALLOWED_ROUTE_EXTENSIONS = [".py"]

    # Framework Behavior
    VERBOSE_LOGGING = True
    AUTO_RELOAD = False  # Auto-reload on file changes (dev mode)

    # Server Configuration
    HOST = "0.0.0.0"
    PORT = 7376

    # CORS Configuration (applied globally to all routes)
    ENABLE_CORS = True
    CORS_ALLOW_ORIGINS = ["*"]  # List of allowed origins or ["*"] for all
    CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    CORS_ALLOW_HEADERS = ["*"]  # List of allowed headers or ["*"] for all
    CORS_ALLOW_CREDENTIALS = False

    # File/Folder Naming Conventions
    IGNORE_FOLDERS = ["__pycache__", ".git", "node_modules", "venv", ".venv"]
    IGNORE_FILES = ["__init__.py", "config.py"]

    @classmethod
    def validate(cls) -> bool:
        """
        Validate configuration settings.

        Returns:
            True if configuration is valid
        """
        if not cls.ROUTE_FILE_NAME.endswith(".py"):
            raise ValueError("ROUTE_FILE_NAME must be a Python file")

        if not cls.SUPPORTED_HTTP_METHODS:
            raise ValueError("SUPPORTED_HTTP_METHODS cannot be empty")

        return True


class DevConfig(Config):
    """Development configuration with helpful defaults."""
    VERBOSE_LOGGING = True
    AUTO_RELOAD = True


class ProdConfig(Config):
    """Production configuration optimized for performance."""
    VERBOSE_LOGGING = False
    AUTO_RELOAD = False


# Default configuration
DEFAULT_CONFIG = Config
