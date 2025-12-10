"""
REROUTE Configuration

Central configuration for the REROUTE framework.
"""

import os
import logging
import secrets
import hashlib
import string
import math
from pathlib import Path
from typing import List, Optional

# Optional dotenv support (install with: pip install python-dotenv)
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

logger = logging.getLogger(__name__)


class SecretKeyManager:
    """
    Manages secure secret key generation, validation, and environment detection.

    This class handles:
    - Cryptographically secure random key generation
    - Production environment detection
    - Secret key strength validation
    - Environment variable override support
    - Security event logging
    """

    # Minimum entropy requirements for security
    MIN_KEY_LENGTH = 32
    MIN_ENTROPY_BITS = 128

    # Production environment indicators
    PRODUCTION_INDICATORS = {
        'ENV', 'ENVIRONMENT', 'APP_ENV', 'FLASK_ENV', 'DJANGO_SETTINGS_MODULE',
        'NODE_ENV', 'RAILS_ENV', 'REROUTE_ENV', 'ENVIRONMENT_NAME'
    }

    # Production values that indicate production environment
    PRODUCTION_VALUES = {
        'production', 'prod', 'live', 'main', 'master', 'staging', 'stage'
    }

    @classmethod
    def is_production_environment(cls) -> bool:
        """
        Detect if the application is running in production environment.

        Returns:
            bool: True if production environment detected
        """
        # Check common production environment variables
        for env_var in cls.PRODUCTION_INDICATORS:
            env_value = os.getenv(env_var, '').lower()
            if env_value in cls.PRODUCTION_VALUES:
                logger.info(f"Production environment detected via {env_var}={env_value}")
                return True

        # Check for common production hosting providers
        hosting_indicators = {
            'VERCEL': os.getenv('VERCEL') == '1',
            'HEROKU': os.getenv('DYNO') is not None,
            'AWS': os.getenv('AWS_REGION') is not None,
            'GCP': os.getenv('GCP_PROJECT') is not None,
            'AZURE': os.getenv('WEBSITE_SITE_NAME') is not None,
            'RAILWAY': os.getenv('RAILWAY_ENVIRONMENT') is not None,
            'RENDER': os.getenv('RENDER_SERVICE_ID') is not None,
        }

        for provider, is_present in hosting_indicators.items():
            if is_present:
                logger.info(f"Production environment detected via {provider} hosting")
                return True

        # Check for production-specific file system indicators
        production_files = [
            '/proc/1/cgroup',  # Docker container indicator
            '/sys/hypervisor/uuid',  # AWS indicator
        ]

        for file_path in production_files:
            if os.path.exists(file_path):
                logger.info(f"Production environment detected via {file_path}")
                return True

        return False

    @classmethod
    def generate_secure_key(cls, length: int = MIN_KEY_LENGTH) -> str:
        """
        Generate a cryptographically secure random key.

        Args:
            length: Key length in bytes (default: 32)

        Returns:
            str: URL-safe base64-encoded random key
        """
        if length < cls.MIN_KEY_LENGTH:
            raise ValueError(f"Key length must be at least {cls.MIN_KEY_LENGTH} characters")

        secure_key = secrets.token_urlsafe(length)

        # Verify the generated key meets entropy requirements
        if not cls._validate_key_entropy(secure_key):
            # Generate again if entropy is insufficient (very rare)
            secure_key = secrets.token_urlsafe(length + 8)

        logger.info("Secure key generated successfully")
        return secure_key

    @classmethod
    def _validate_key_entropy(cls, key: str) -> bool:
        """
        Validate that a key has sufficient entropy.

        Args:
            key: Secret key to validate

        Returns:
            bool: True if key has sufficient entropy
        """
        if len(key) < cls.MIN_KEY_LENGTH:
            return False

        # Calculate Shannon entropy
        char_counts = {}
        for char in key:
            char_counts[char] = char_counts.get(char, 0) + 1

        entropy = 0
        key_length = len(key)

        for count in char_counts.values():
            probability = count / key_length
            # Shannon entropy formula: -p * log2(p)
            if probability > 0:
                entropy -= probability * math.log2(probability)

        # Convert to bits (entropy is already in bits per character)
        entropy_bits = entropy * key_length

        return entropy_bits >= cls.MIN_ENTROPY_BITS

    @classmethod
    def validate_key_strength(cls, key: str) -> tuple[bool, str]:
        """
        Validate secret key strength and provide feedback.

        Args:
            key: Secret key to validate

        Returns:
            tuple: (is_valid, error_message)
        """
        if not key:
            return False, "Secret key cannot be empty"

        if len(key) < cls.MIN_KEY_LENGTH:
            return False, f"Secret key must be at least {cls.MIN_KEY_LENGTH} characters (got {len(key)})"

        # Check for obviously weak keys
        weak_patterns = [
            'your-secret-key',
            'secret-key',
            'default-key',
            'change-me',
            'replace-me',
            'test-key',
            'dev-key',
            '123456',
            'password',
            'admin',
            'root',
        ]

        key_lower = key.lower()
        for pattern in weak_patterns:
            if pattern in key_lower:
                return False, f"Secret key contains weak pattern: '{pattern}'"

        # Check for low entropy (repeating characters) - adjust threshold based on key length
        unique_ratio = len(set(key)) / len(key)
        # More gradual scaling for very long keys, minimum 5% unique
        min_unique_ratio = max(0.05, 0.3 - (len(key) - cls.MIN_KEY_LENGTH) * 0.0005)
        if unique_ratio < min_unique_ratio:
            return False, f"Secret key has low entropy (too many repeating characters: {unique_ratio:.1%} unique, minimum {min_unique_ratio:.1%})"

        # Validate entropy
        if not cls._validate_key_entropy(key):
            return False, f"Secret key has insufficient entropy (< {cls.MIN_ENTROPY_BITS} bits)"

        return True, ""

    @classmethod
    def get_or_generate_secret_key(cls, config_key: str = None) -> str:
        """
        Get secret key from environment or generate a secure one.

        Args:
            config_key: Default key from config class

        Returns:
            str: Secure secret key
        """
        is_production = cls.is_production_environment()

        # 1. Check environment variable first (highest priority)
        env_key = os.getenv('REROUTE_SECRET_KEY')
        if env_key:
            is_valid, error_msg = cls.validate_key_strength(env_key)
            if not is_valid:
                if is_production:
                    logger.critical(f"CRITICAL: Invalid SECRET_KEY in production: {error_msg}")
                    raise ValueError(
                        f"CRITICAL SECURITY: Invalid REROUTE_SECRET_KEY in production. "
                        f"Error: {error_msg}. "
                        f"Set a strong secret key with at least {cls.MIN_KEY_LENGTH} characters."
                    )
                else:
                    logger.warning(f"Weak SECRET_KEY in development: {error_msg}")
                    # Generate a better key for development
                    secure_key = cls.generate_secure_key()
                    logger.info(f"Generated secure development key: {secure_key[:8]}...")
                    return secure_key
            else:
                logger.info("Using SECRET_KEY from environment variable")
                return env_key

        # 2. Use config-provided key with validation
        if config_key:
            is_valid, error_msg = cls.validate_key_strength(config_key)
            if not is_valid:
                if is_production:
                    logger.critical(f"CRITICAL: Default insecure SECRET_KEY detected in production")
                    raise ValueError(
                        f"CRITICAL SECURITY: Default insecure SECRET_KEY detected in production. "
                        f"Set REROUTE_SECRET_KEY environment variable with a strong secret key. "
                        f"Error: {error_msg}"
                    )
                else:
                    logger.warning(f"Default SECRET_KEY is weak: {error_msg}")
                    # Generate a secure key for development
                    secure_key = cls.generate_secure_key()
                    logger.warning(f"Generated secure development key: {secure_key[:8]}...")
                    return secure_key
            else:
                logger.info("Using valid config-provided SECRET_KEY")
                return config_key

        # 3. Generate a secure key (fallback)
        secure_key = cls.generate_secure_key()

        if is_production:
            logger.critical("CRITICAL: No SECRET_KEY provided in production")
            raise ValueError(
                f"CRITICAL SECURITY: No SECRET_KEY configured in production. "
                f"Set REROUTE_SECRET_KEY environment variable with a strong secret key."
            )
        else:
            logger.info(f"Generated secure default key: {secure_key[:8]}...")
            return secure_key


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
    # WARNING: This will be automatically validated and replaced if insecure
    SECRET_KEY = "your-secret-key-change-in-production"  # Will be validated/replaced by SecretKeyManager

    # Database Configuration
    DATABASE_URL = None  # Database connection URL (optional)

    # CORS Configuration (applied globally to all routes)
    # SECURITY: Default to disabled for maximum security
    ENABLE_CORS = False  # Secure by default - must be explicitly enabled
    # In production, set explicit origins in your environment:
    #   REROUTE_ENABLE_CORS=true
    #   REROUTE_CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
    CORS_ALLOW_ORIGINS = []  # Empty list - no origins allowed by default
    CORS_ALLOW_METHODS = ["GET", "HEAD", "OPTIONS"]  # Only safe methods by default
    # Only allow essential headers by default
    CORS_ALLOW_HEADERS = ["Content-Type", "Accept"]
    CORS_ALLOW_CREDENTIALS = False  # Never allow credentials by default

    # Health Check Configuration
    HEALTH_CHECK_ENABLED = True  # Enable /health endpoint for load balancers
    HEALTH_CHECK_PATH = "/health"  # Path for health check endpoint
    HEALTH_CHECK_AUTHENTICATED = False  # Set True to require auth for detailed health metrics

    # Security Headers Configuration
    # Controls comprehensive HTTP security headers for client-side attack protection
    SECURITY_HEADERS_ENABLED = True  # Enable/disable security headers middleware

    # Content Security Policy (CSP) configuration
    # Prevents various injection attacks by specifying which dynamic resources are allowed
    SECURITY_CSP_ENABLED = True  # Enable Content Security Policy header

    # HSTS (HTTP Strict Transport Security) configuration
    # Forces HTTPS connections and protects against protocol downgrade attacks
    SECURITY_HSTS_ENABLED = True  # Enable HSTS (auto-disabled in development)
    SECURITY_HSTS_MAX_AGE = 31536000  # HSTS max-age in seconds (1 year)
    SECURITY_HSTS_INCLUDE_SUBDOMAINS = True  # Apply HSTS to all subdomains
    SECURITY_HSTS_PRELOAD = False  # Submit to HSTS preload list

    # X-Frame-Options configuration
    # Prevents clickjacking attacks by controlling whether your site can be embedded
    SECURITY_X_FRAME_OPTIONS = "DENY"  # DENY, SAMEORIGIN, or ALLOW-FROM

    # X-Content-Type-Options configuration
    # Prevents MIME-type sniffing attacks
    SECURITY_X_CONTENT_TYPE_OPTIONS = True  # Enable nosniff header

    # X-XSS-Protection configuration
    # Enables browser XSS filtering (legacy, but still useful for older browsers)
    SECURITY_X_XSS_PROTECTION = "1; mode=block"  # Enable XSS protection

    # Referrer Policy configuration
    # Controls how much referrer information is sent with requests
    SECURITY_REFERRER_POLICY = "strict-origin-when-cross-origin"  # Referrer information control

    # Permissions Policy configuration
    # Controls which browser features can be used by your web application
    SECURITY_PERMISSIONS_POLICY_ENABLED = True  # Enable Permissions Policy header

    # Environment-specific domains
    # Configure these for production deployments with external services
    SECURITY_CDN_DOMAINS = []  # List of CDN domains for assets (e.g., ["https://cdn.example.com"])
    SECURITY_API_DOMAINS = []  # List of API domains for backend calls (e.g., ["https://api.example.com"])

    # Custom security headers
    # Add any additional security headers as key-value pairs
    SECURITY_CUSTOM_HEADERS = {}  # Example: {"X-Custom-Security": "value"}

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
    def _initialize_secure_secret_key(cls):
        """
        Initialize and validate the secret key securely.

        This method is called automatically during config loading to ensure
        the secret key is secure in all environments.
        """
        try:
            # Get the current secret key (will be validated and potentially replaced)
            secure_key = SecretKeyManager.get_or_generate_secret_key(
                config_key=getattr(cls, 'SECRET_KEY', None)
            )

            # Update the class attribute with the secure key
            cls.SECRET_KEY = secure_key

            # Log success without exposing the actual key
            logger.info("Secret key initialized and validated successfully")

        except ValueError as e:
            # Critical security error in production
            logger.critical(f"CRITICAL SECRET KEY ERROR: {e}")
            raise
        except Exception as e:
            # Unexpected error during key initialization
            logger.error(f"Unexpected error during secret key initialization: {e}")
            # Fail securely - generate a temporary key
            cls.SECRET_KEY = SecretKeyManager.generate_secure_key()
            logger.warning("Generated emergency secret key due to initialization error")

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

        # Validate CORS configuration for security
        cls._validate_cors_configuration()

        # Initialize secure secret key after loading all environment variables
        cls._initialize_secure_secret_key()

        return cls

    @classmethod
    def _validate_cors_configuration(cls):
        """
        Validate CORS configuration for security compliance.

        This method ensures that CORS settings follow secure-by-default principles
        and provides warnings for potentially insecure configurations.
        """
        is_production = SecretKeyManager.is_production_environment()

        # Security: If CORS is enabled, validate origins
        if getattr(cls, 'ENABLE_CORS', False):
            cors_origins = getattr(cls, 'CORS_ALLOW_ORIGINS', [])

            if not cors_origins:
                logger.warning(
                    "CORS is enabled but no origins are specified. "
                    "This may allow any origin depending on the framework implementation."
                )
            else:
                # Security: Check for overly permissive origins
                dangerous_patterns = ['*', '://*.', '://0.0.0.0', '://127.0.0.1']
                for origin in cors_origins:
                    if any(pattern in origin.lower() for pattern in dangerous_patterns):
                        if is_production:
                            logger.error(
                                f"DANGEROUS CORS origin detected in production: {origin}. "
                                "This can lead to data leakage and security vulnerabilities."
                            )
                        else:
                            logger.warning(
                                f"Dangerous CORS origin detected in development: {origin}. "
                                "Avoid using wildcards in production."
                            )

                # Security: Check for localhost origins in production
                if is_production:
                    localhost_patterns = ['localhost', '127.0.0.1', '0.0.0.0']
                    for origin in cors_origins:
                        if any(pattern in origin.lower() for pattern in localhost_patterns):
                            logger.error(
                                f"Localhost CORS origin detected in production: {origin}. "
                                "This should not be used in production environments."
                            )

            # Security: Validate allowed methods
            cors_methods = getattr(cls, 'CORS_ALLOW_METHODS', [])
            dangerous_methods = ['DELETE', 'PUT', 'PATCH']

            if is_production and any(method in cors_methods for method in dangerous_methods):
                logger.warning(
                    f"State-changing methods allowed in CORS: {[m for m in dangerous_methods if m in cors_methods]}. "
                    "Ensure this is intentional and properly secured."
                )

            # Security: Warn about credentials
            if getattr(cls, 'CORS_ALLOW_CREDENTIALS', False):
                if is_production:
                    logger.error(
                        "CORS credentials enabled in production. "
                        "This increases security risk and should only be used with trusted origins."
                    )
                else:
                    logger.warning(
                        "CORS credentials enabled. Ensure you understand the security implications."
                    )

        else:
            # CORS is disabled - this is secure
            if cls.VERBOSE_LOGGING:
                logger.info("CORS is disabled - secure by default")

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

        # Validate secret key - this will trigger secure initialization if not already done
        cls._initialize_secure_secret_key()

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

    # Development CORS - more permissive for local development
    # SECURITY: Still requires explicit enablement, but provides common dev origins
    ENABLE_CORS = True  # Enable for development convenience
    CORS_ALLOW_ORIGINS = [
        "http://localhost:3000", "http://localhost:3001", "http://localhost:5173",  # Common dev servers
        "http://127.0.0.1:3000", "http://127.0.0.1:3001", "http://127.0.0.1:5173",
        "http://localhost:8080", "http://127.0.0.1:8080"  # Alternative dev ports
    ]
    CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]  # Full methods for dev
    CORS_ALLOW_HEADERS = [
        "Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin",
        "X-CSRF-Token", "X-API-Key", "User-Agent"  # Common dev headers
    ]

    # Development Security Headers - more permissive for local development
    # Still provides protection but allows development tools and inline content
    SECURITY_HEADERS_ENABLED = True
    SECURITY_HSTS_ENABLED = False  # Disable HSTS in development (no HTTPS typically)
    SECURITY_X_FRAME_OPTIONS = "SAMEORIGIN"  # Allow same-origin framing for dev tools
    SECURITY_REFERRER_POLICY = "strict-origin-when-cross-origin"  # Standard referrer policy

    # Development-friendly CSP defaults
    # These are automatically adjusted by the security middleware for development
    SECURITY_CDN_DOMAINS = []  # Typically no CDN in development
    SECURITY_API_DOMAINS = []  # Local API in development


class ProdConfig(Config):
    """Production configuration optimized for performance and security."""

    class Env:
        """Production environment configuration"""
        file = ".env.prod"  # Production environment file
        auto_load = True
        override = False  # Don't override system env vars in production

    DEBUG = False
    VERBOSE_LOGGING = False
    LOG_LEVEL = "WARNING"
    AUTO_RELOAD = False

    # Production CORS - maximum security by default
    # SECURITY: Must be explicitly configured via environment variables
    ENABLE_CORS = False  # Disabled by default for security
    # Production origins should be set via REROUTE_CORS_ORIGINS environment variable
    CORS_ALLOW_ORIGINS = []  # Must be explicitly configured
    CORS_ALLOW_METHODS = ["GET", "HEAD", "OPTIONS"]  # Only safe methods
    CORS_ALLOW_HEADERS = ["Content-Type", "Accept"]  # Minimal headers only

    # Production Security Headers - maximum security configuration
    # Strict security headers suitable for production environments
    SECURITY_HEADERS_ENABLED = True
    SECURITY_HSTS_ENABLED = True  # Enable HSTS in production
    SECURITY_HSTS_MAX_AGE = 31536000  # 1 year
    SECURITY_HSTS_INCLUDE_SUBDOMAINS = True  # Apply to all subdomains
    SECURITY_HSTS_PRELOAD = True  # Submit to HSTS preload list
    SECURITY_X_FRAME_OPTIONS = "DENY"  # Strictest frame protection
    SECURITY_X_CONTENT_TYPE_OPTIONS = True  # Prevent MIME sniffing
    SECURITY_X_XSS_PROTECTION = "1; mode=block"  # Enable XSS protection
    SECURITY_REFERRER_POLICY = "strict-origin-when-cross-origin"  # Privacy-focused
    SECURITY_PERMISSIONS_POLICY_ENABLED = True  # Restrict browser features

    # Production domains should be configured via environment variables
    # These provide examples of typical production configurations
    # SECURITY_CDN_DOMAINS = ["https://cdn.example.com", "https://assets.example.com"]
    # SECURITY_API_DOMAINS = ["https://api.example.com", "https://backend.example.com"]
    SECURITY_CDN_DOMAINS = []  # Configure via environment variable
    SECURITY_API_DOMAINS = []  # Configure via environment variable

    # Custom production headers can be added as needed
    # Example: SECURITY_CUSTOM_HEADERS = {"X-Content-DPR": "1"}


# Default configuration
DEFAULT_CONFIG = Config
