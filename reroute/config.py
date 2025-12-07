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

    # Security Configuration
    SECRET_KEY = "your-secret-key-change-in-production"  # Secret key for security operations

    # Database Configuration
    DATABASE_URL = None  # Database connection URL (optional)

    # CORS Configuration (applied globally to all routes)
    # SECURITY: Default to restrictive origins for production safety
    ENABLE_CORS = True
    # In production, set explicit origins in your environment:
    #   REROUTE_CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
    CORS_ALLOW_ORIGINS = ["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:3000", "http://127.0.0.1:8080"]
    CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    # Only allow common safe headers by default
    CORS_ALLOW_HEADERS = ["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"]
    CORS_ALLOW_CREDENTIALS = False

    # Health Check Configuration
    HEALTH_CHECK_ENABLED = True  # Enable /health endpoint for load balancers
    HEALTH_CHECK_PATH = "/health"  # Path for health check endpoint
    HEALTH_CHECK_AUTHENTICATED = False  # Set True to require auth for detailed health metrics

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

        # Valid log levels for validation
        VALID_LOG_LEVELS = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}

        def auto_detect_and_set(attr_name: str, env_value: str):
            """Auto-detect type and set Config attribute dynamically"""

            # Handle explicit empty values (null, none, empty)
            if env_value.lower() in ('null', 'none', '~', ''):
                return None

            # Boolean detection
            if env_value.lower() in ('true', 'false', '1', '0', 'yes', 'no', 'on', 'off'):
                return env_value.lower() in ('true', '1', 'yes', 'on')

            # Integer detection (handle negative numbers too)
            if env_value.lstrip('-').isdigit():
                try:
                    return int(env_value)
                except ValueError:
                    pass  # Fall through to string handling

            # List detection (comma-separated values)
            if ',' in env_value:
                return [item.strip() for item in env_value.split(',') if item.strip()]

            # Float detection (numbers with decimals)
            try:
                if '.' in env_value and env_value.replace('.', '').lstrip('-').isdigit():
                    return float(env_value)
            except ValueError:
                pass  # Fall through to string handling

            # Default to string
            return env_value

        # Auto-map ANY REROUTE_* environment variable to Config attributes
        for env_key, env_value in os.environ.items():
            # Only process REROUTE_* prefixed variables (security boundary)
            if not env_key.startswith('REROUTE_'):
                continue

            # Remove REROUTE_ prefix to get attribute name
            attr_name = env_key.replace('REROUTE_', '', 1)

            # Skip internal framework settings (security protection)
            if attr_name.startswith('ROUTES_') or attr_name in ('SUPPORTED_HTTP_METHODS', 'IGNORE_FOLDERS', 'IGNORE_FILES'):
                logger.warning(
                    f"Cannot override internal framework setting: {env_key}"
                )
                continue

            # Auto-detect type and set value
            try:
                parsed_value = auto_detect_and_set(attr_name, env_value)

                # Special validation for LOG_LEVEL
                if attr_name == 'LOG_LEVEL' and parsed_value:
                    if isinstance(parsed_value, str):
                        parsed_value_upper = parsed_value.upper()
                        if parsed_value_upper in VALID_LOG_LEVELS:
                            setattr(cls, attr_name, parsed_value_upper)
                        else:
                            logger.warning(
                                f"Invalid LOG_LEVEL: {env_value}. "
                                f"Must be one of: {', '.join(sorted(VALID_LOG_LEVELS))}. "
                                f"Using default value."
                            )
                            continue
                    else:
                        logger.warning(f"LOG_LEVEL must be a string, got {type(parsed_value)}")
                        continue

                # Special validation for PORT (must be valid port range)
                elif attr_name == 'PORT' and isinstance(parsed_value, int):
                    if not (1 <= parsed_value <= 65535):
                        logger.warning(
                            f"Invalid PORT: {parsed_value}. "
                            f"Must be between 1 and 65535. Using default value."
                        )
                        continue

                # Handle CORS_ORIGINS backward compatibility
                elif attr_name == 'CORS_ORIGINS':
                    # Map CORS_ORIGINS to CORS_ALLOW_ORIGINS for compatibility
                    setattr(cls, 'CORS_ALLOW_ORIGINS', parsed_value)
                    if cls.VERBOSE_LOGGING:
                        logger.info(f"Mapped REROUTE_CORS_ORIGINS to CORS_ALLOW_ORIGINS = {parsed_value}")
                    continue  # Don't set CORS_ORIGINS attribute itself

                # Set the attribute dynamically
                setattr(cls, attr_name, parsed_value)

                if cls.VERBOSE_LOGGING:
                    logger.info(f"Auto-set {attr_name} = {parsed_value} (from {env_key})")

            except Exception as e:
                logger.warning(
                    f"Failed to parse {env_key}: {e}. "
                    f"Environment variable will be ignored."
                )

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
