"""
REROUTE Configuration

Central configuration for the REROUTE framework.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional

# Optional dotenv support (install with: pip install python-dotenv)
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

logger = logging.getLogger(__name__)


class Config:
    """
    Framework configuration settings.

    Organized into:
    - Internal: REROUTE framework internals (DO NOT MODIFY)
    - Env: Environment file configuration
    - User Settings: Configurable by developers
    """

    class Internal:
        """
        REROUTE Framework Internal Configuration

        WARNING: THESE SETTINGS ARE PROTECTED AND CANNOT BE MODIFIED.
        These are crucial for REROUTE's core functionality.
        Any attempt to override will raise an error.
        """
        # Routing Internals
        ROUTES_DIR_NAME = "routes"  # Directory name for routes
        ROUTE_FILE_NAME = "page.py"  # File name for route handlers
        SUPPORTED_HTTP_METHODS = ["get", "post", "put", "delete", "patch", "head", "options"]

        # Security & Validation
        ENABLE_PATH_VALIDATION = True  # Validate route paths for security
        ALLOWED_ROUTE_EXTENSIONS = [".py"]  # Only Python files allowed

        # Ignore Patterns
        IGNORE_FOLDERS = ["__pycache__", ".git", "node_modules", "venv", ".venv"]
        IGNORE_FILES = ["__init__.py", "config.py"]

    class Env:
        """Environment file configuration"""
        file = ".env"  # Path to .env file (can be ".env.prod", ".env.dev", etc.)
        auto_load = True  # Automatically load .env file
        override = True  # Override existing environment variables

    class OpenAPI:
        """
        OpenAPI/Swagger documentation settings.

        Applies to both FastAPI and Flask frameworks.
        Users can customize documentation endpoints and API metadata.

        Usage:
            class CustomConfig(Config):
                class OpenAPI:
                    ENABLE = True
                    DOCS_PATH = "/api-docs"
                    REDOC_PATH = None  # Disable ReDoc
        """
        # Enable/Disable OpenAPI documentation
        ENABLE = True  # True by default for FastAPI, opt-in for Flask

        # Documentation Endpoints (customizable)
        DOCS_PATH = "/docs"            # Swagger UI endpoint
        REDOC_PATH = "/redoc"          # ReDoc endpoint
        JSON_PATH = "/openapi.json"    # OpenAPI JSON spec endpoint

        # API Metadata
        TITLE = None                   # Auto-generated from project name if None
        VERSION = "1.0.0"              # API version
        DESCRIPTION = None             # Auto-generated if None

    # User-Configurable Settings
    # ============================

    # API Configuration
    API_BASE_PATH = ""  # Base path for all routes (e.g., "/api/v1")

    # Framework Behavior
    DEBUG = False  # Debug mode (enables detailed error pages, auto-reload)
    VERBOSE_LOGGING = True
    LOG_LEVEL = "INFO"  # Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
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

    # Health Check Configuration
    HEALTH_CHECK_ENABLED = True  # Enable /health endpoint for load balancers
    HEALTH_CHECK_PATH = "/health"  # Path for health check endpoint

    def __init_subclass__(cls, **kwargs):
        """
        Validate that child classes don't override FINAL attributes.

        This hook is called automatically when a class inherits from Config.
        """
        super().__init_subclass__(**kwargs)

        # Get parent class (Config)
        parent_cls = cls.__bases__[0]

        # Check if Internal class was overridden
        if 'Internal' in cls.__dict__:
            raise TypeError(
                f"Cannot override Config.Internal in {cls.__name__}. "
                "Config.Internal contains framework-critical settings."
            )

    @classmethod
    def load_from_env(cls, env_file: Optional[str] = None):
        """
        Load configuration from .env file and environment variables.

        All environment variables must be prefixed with REROUTE_*

        This method:
        1. Loads .env file (if exists and python-dotenv is installed)
        2. Maps REROUTE_* environment variables to Config attributes
        3. Handles type conversion (bool, int, lists)

        Args:
            env_file: Path to .env file (overrides Config.Env.file)

        Example .env file:
            REROUTE_DEBUG=True
            REROUTE_PORT=8000
            REROUTE_HOST=localhost
            REROUTE_LOG_LEVEL=DEBUG
            REROUTE_CORS_ALLOW_ORIGINS=http://localhost:3000,http://localhost:5173
            REROUTE_API_BASE_PATH=/api/v1

        Example usage:
            Config.load_from_env()  # Uses Config.Env.file
            Config.load_from_env(".env.prod")  # Custom file
        """
        # Load .env file if available
        env_file_path = env_file or cls.Env.file

        if DOTENV_AVAILABLE and cls.Env.auto_load:
            env_path = Path(env_file_path)
            if env_path.exists():
                load_dotenv(env_path, override=cls.Env.override)
                if cls.VERBOSE_LOGGING:
                    logger.info(f"Loaded environment from: {env_path}")
            elif cls.VERBOSE_LOGGING:
                logger.info(f".env file not found: {env_path}")
        elif not DOTENV_AVAILABLE and cls.Env.auto_load:
            if cls.VERBOSE_LOGGING:
                logger.warning("python-dotenv not installed. Install with: pip install python-dotenv")

        # Helper functions for type conversion
        def parse_bool(value: str) -> bool:
            """Parse boolean from string"""
            return str(value).lower() in ('true', '1', 'yes', 'on')

        def parse_int(value: str) -> int:
            """Parse integer from string"""
            try:
                return int(value)
            except (ValueError, TypeError):
                return 0

        def parse_list(value: str) -> List[str]:
            """Parse comma-separated list from string"""
            return [item.strip() for item in str(value).split(',') if item.strip()]

        # Whitelist of allowed config keys (security: prevent arbitrary attribute setting)
        ALLOWED_CONFIG_KEYS = {
            # API Configuration
            'API_BASE_PATH',

            # Framework Behavior
            'DEBUG', 'VERBOSE_LOGGING', 'LOG_LEVEL', 'AUTO_RELOAD',

            # Server Configuration
            'HOST', 'PORT',

            # CORS Configuration
            'ENABLE_CORS', 'CORS_ALLOW_ORIGINS', 'CORS_ALLOW_METHODS',
            'CORS_ALLOW_HEADERS', 'CORS_ALLOW_CREDENTIALS',

            # Health Check Configuration
            'HEALTH_CHECK_ENABLED', 'HEALTH_CHECK_PATH'
        }

        # Valid log levels for validation
        VALID_LOG_LEVELS = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}

        # Auto-map REROUTE_* environment variables to Config attributes
        for env_key, env_value in os.environ.items():
            # Only process REROUTE_* prefixed variables
            if not env_key.startswith('REROUTE_'):
                continue

            # Remove REROUTE_ prefix to get attribute name
            attr_name = env_key.replace('REROUTE_', '', 1)

            # Security: Check against whitelist first
            if attr_name not in ALLOWED_CONFIG_KEYS:
                logger.warning(
                    f"Config key not in whitelist: {env_key}. "
                    f"Only REROUTE_* variables for user-configurable settings are allowed."
                )
                continue

            # Check if this attribute exists in Config
            if not hasattr(cls, attr_name):
                if cls.VERBOSE_LOGGING:
                    logger.warning(f"Unknown config variable: {env_key}")
                continue

            # Get current attribute value to determine type
            current_value = getattr(cls, attr_name)

            # Skip if it's a method or nested class
            if callable(current_value) or isinstance(current_value, type):
                continue

            # Type conversion based on current value type
            if isinstance(current_value, bool):
                setattr(cls, attr_name, parse_bool(env_value))
            elif isinstance(current_value, int):
                setattr(cls, attr_name, parse_int(env_value))
            elif isinstance(current_value, list):
                setattr(cls, attr_name, parse_list(env_value))
            else:
                # String or other types - validate and set
                # Special validation for LOG_LEVEL
                if attr_name == 'LOG_LEVEL':
                    env_value_upper = env_value.upper()
                    if env_value_upper not in VALID_LOG_LEVELS:
                        logger.warning(
                            f"Invalid LOG_LEVEL: {env_value}. "
                            f"Must be one of: {', '.join(sorted(VALID_LOG_LEVELS))}. "
                            f"Using default: {current_value}"
                        )
                        continue
                    setattr(cls, attr_name, env_value_upper)
                else:
                    setattr(cls, attr_name, env_value)

        return cls

    @classmethod
    def validate(cls) -> bool:
        """
        Validate configuration settings.

        Returns:
            True if configuration is valid
        """
        # Validate framework internals
        if not cls.Internal.ROUTE_FILE_NAME.endswith(".py"):
            raise ValueError("Internal.ROUTE_FILE_NAME must be a Python file")

        if not cls.Internal.SUPPORTED_HTTP_METHODS:
            raise ValueError("Internal.SUPPORTED_HTTP_METHODS cannot be empty")

        # Validate user configuration
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if cls.LOG_LEVEL.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(valid_levels)}")

        return True


class DevConfig(Config):
    """Development configuration with helpful defaults."""

    class Env:
        """Development environment configuration"""
        file = ".env.dev"  # Development environment file
        auto_load = True
        override = True

    DEBUG = True
    VERBOSE_LOGGING = True
    LOG_LEVEL = "DEBUG"
    AUTO_RELOAD = True


class ProdConfig(Config):
    """Production configuration optimized for performance."""

    class Env:
        """Production environment configuration"""
        file = ".env.prod"  # Production environment file
        auto_load = True
        override = False  # Don't override system env vars in production

    DEBUG = False
    VERBOSE_LOGGING = False
    LOG_LEVEL = "WARNING"
    AUTO_RELOAD = False
    ENABLE_CORS = True  # Typically needed in production


# Default configuration
DEFAULT_CONFIG = Config
