"""
Security Headers Middleware for REROUTE

Comprehensive security headers implementation for client-side attack protection.

This module provides:
- OWASP-compliant security headers
- Environment-specific configurations
- Flexible policy customization
- Automatic header management

Supported Headers:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY/SAMEORIGIN
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security (HSTS): HTTPS enforcement
- Content-Security-Policy (CSP): Injection attack prevention
- Referrer-Policy: Referrer information control
- Permissions-Policy: Browser feature access control
"""

import os
import logging
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Environment types for security header configuration."""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class CSPDirective:
    """Content Security Policy directive builder."""

    def __init__(self, directive: str, *sources: str):
        self.directive = directive
        self.sources = list(sources)

    def add_source(self, source: str) -> 'CSPDirective':
        """Add a source to this directive."""
        if source not in self.sources:
            self.sources.append(source)
        return self

    def remove_source(self, source: str) -> 'CSPDirective':
        """Remove a source from this directive."""
        if source in self.sources:
            self.sources.remove(source)
        return self

    def __str__(self) -> str:
        if self.sources:
            return f"{self.directive} {' '.join(self.sources)}"
        return self.directive


class ContentSecurityPolicy:
    """
    Content Security Policy (CSP) configuration.

    CSP prevents various injection attacks by specifying which
    dynamic resources are allowed to load.
    """

    def __init__(self):
        self.directives: Dict[str, CSPDirective] = {}
        self._setup_default_directives()

    def _setup_default_directives(self):
        """Setup default CSP directives for security."""
        # Script security
        self.add_directive(CSPDirective("script-src", "'self'"))

        # Object security
        self.add_directive(CSPDirective("object-src", "'none'"))

        # Base restrictions
        self.add_directive(CSPDirective("base-uri", "'self'"))

        # Form targets
        self.add_directive(CSPDirective("form-action", "'self'"))

        # Frame ancestors (replaces X-Frame-Options)
        self.add_directive(CSPDirective("frame-ancestors", "'none'"))

        # Image sources
        self.add_directive(CSPDirective("img-src", "'self'", "data:", "https:"))

        # Style sources
        self.add_directive(CSPDirective("style-src", "'self'", "'unsafe-inline'"))

        # Font sources
        self.add_directive(CSPDirective("font-src", "'self'", "data:", "https:"))

        # Connect sources (API calls, WebSockets)
        self.add_directive(CSPDirective("connect-src", "'self'"))

        # Default source for anything not specified
        self.add_directive(CSPDirective("default-src", "'self'"))

    def add_directive(self, directive: CSPDirective) -> 'ContentSecurityPolicy':
        """Add or replace a CSP directive."""
        self.directives[directive.directive] = directive
        return self

    def remove_directive(self, directive_name: str) -> 'ContentSecurityPolicy':
        """Remove a CSP directive."""
        if directive_name in self.directives:
            del self.directives[directive_name]
        return self

    def get_directive(self, name: str) -> Optional[CSPDirective]:
        """Get a specific CSP directive."""
        return self.directives.get(name)

    def allow_external_scripts(self, sources: List[str]) -> 'ContentSecurityPolicy':
        """Allow scripts from external sources."""
        script_src = self.get_directive("script-src")
        if script_src:
            for source in sources:
                script_src.add_source(source)
        return self

    def allow_external_styles(self, sources: List[str]) -> 'ContentSecurityPolicy':
        """Allow styles from external sources."""
        style_src = self.get_directive("style-src")
        if style_src:
            for source in sources:
                style_src.add_source(source)
        return self

    def allow_fonts_from(self, sources: List[str]) -> 'ContentSecurityPolicy':
        """Allow fonts from external sources."""
        font_src = self.get_directive("font-src")
        if font_src:
            for source in sources:
                font_src.add_source(source)
        return self

    def allow_api_endpoints(self, sources: List[str]) -> 'ContentSecurityPolicy':
        """Allow connections to external API endpoints."""
        connect_src = self.get_directive("connect-src")
        if connect_src:
            for source in sources:
                connect_src.add_source(source)
        return self

    def __str__(self) -> str:
        """Generate CSP header value."""
        if not self.directives:
            return ""
        return "; ".join(str(directive) for directive in self.directives.values())


class PermissionsPolicy:
    """
    Permissions Policy (formerly Feature Policy) configuration.

    Controls which browser features can be used by the web application.
    """

    def __init__(self):
        self.policies: Dict[str, List[str]] = {}
        self._setup_default_policies()

    def _setup_default_policies(self):
        """Setup default permissions policies for security."""
        # Camera and microphone
        self.set_policy("camera", ["'none'"])
        self.set_policy("microphone", ["'none'"])

        # Geolocation
        self.set_policy("geolocation", ["'self'"])

        # Payment requests
        self.set_policy("payment", ["'none'"])

        # USB devices
        self.set_policy("usb", ["'none'"])

        # Magnetic card reader
        self.set_policy("magnetometer", ["'none'"])

        # Gyroscope and accelerometer
        self.set_policy("gyroscope", ["'none'"])
        self.set_policy("accelerometer", ["'none'"])

        # Ambient light sensor
        self.set_policy("ambient-light-sensor", ["'none'"])

        # Screen wake lock
        self.set_policy("wake-lock", ["'none'"])

        # Web share API
        self.set_policy("web-share", ["'none'"])

        # Clipboard access
        self.set_policy("clipboard-read", ["'self'"])
        self.set_policy("clipboard-write", ["'self'"])

    def set_policy(self, feature: str, allowlist: List[str]) -> 'PermissionsPolicy':
        """Set a permissions policy for a feature."""
        self.policies[feature] = allowlist
        return self

    def allow_feature(self, feature: str, origins: List[str] = None) -> 'PermissionsPolicy':
        """Allow a feature for specific origins (default: all origins)."""
        if origins is None:
            origins = ["*"]
        self.policies[feature] = origins
        return self

    def disable_feature(self, feature: str) -> 'PermissionsPolicy':
        """Disable a feature completely."""
        self.policies[feature] = ["'none'"]
        return self

    def __str__(self) -> str:
        """Generate Permissions-Policy header value."""
        if not self.policies:
            return ""

        policies = []
        for feature, allowlist in self.policies.items():
            if allowlist:
                policies.append(f"{feature}=({', '.join(allowlist)})")

        return ", ".join(policies)


@dataclass
class SecurityHeadersConfig:
    """
    Configuration for security headers.

    This class provides comprehensive control over HTTP security headers
    with environment-specific defaults and flexible customization.
    """

    # Basic security headers
    x_content_type_options: bool = True
    x_frame_options: str = "DENY"  # DENY, SAMEORIGIN, ALLOW-FROM
    x_xss_protection: str = "1; mode=block"

    # Strict Transport Security (HSTS)
    hsts_enabled: bool = False  # Only enabled in production
    hsts_max_age: int = 31536000  # 1 year in seconds
    hsts_include_subdomains: bool = True
    hsts_preload: bool = False

    # Content Security Policy
    csp_enabled: bool = True
    csp: Optional[ContentSecurityPolicy] = None

    # Referrer Policy
    referrer_policy: str = "strict-origin-when-cross-origin"

    # Permissions Policy
    permissions_policy_enabled: bool = True
    permissions_policy: Optional[PermissionsPolicy] = None

    # Additional headers
    cross_origin_embedder_policy: Optional[str] = None
    cross_origin_opener_policy: Optional[str] = None
    cross_origin_resource_policy: Optional[str] = None

    # Environment and overrides
    environment: Environment = Environment.DEVELOPMENT
    custom_headers: Dict[str, str] = None

    def __post_init__(self):
        """Initialize default policies after dataclass creation."""
        if self.csp is None:
            self.csp = ContentSecurityPolicy()

        if self.permissions_policy is None:
            self.permissions_policy = PermissionsPolicy()

        if self.custom_headers is None:
            self.custom_headers = {}

        # Auto-enable HSTS in production
        if self.environment == Environment.PRODUCTION:
            self.hsts_enabled = True

    def get_security_headers(self) -> Dict[str, str]:
        """
        Generate security headers based on current configuration.

        Returns:
            Dictionary of header names to values
        """
        headers = {}

        # X-Content-Type-Options
        if self.x_content_type_options:
            headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options
        if self.x_frame_options:
            headers["X-Frame-Options"] = self.x_frame_options

        # X-XSS-Protection
        if self.x_xss_protection:
            headers["X-XSS-Protection"] = self.x_xss_protection

        # Strict-Transport-Security (HSTS)
        if self.hsts_enabled:
            hsts_value = f"max-age={self.hsts_max_age}"
            if self.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.hsts_preload:
                hsts_value += "; preload"
            headers["Strict-Transport-Security"] = hsts_value

        # Content Security Policy
        if self.csp_enabled and self.csp:
            csp_value = str(self.csp)
            if csp_value:
                headers["Content-Security-Policy"] = csp_value

        # Referrer Policy
        if self.referrer_policy:
            headers["Referrer-Policy"] = self.referrer_policy

        # Permissions Policy
        if self.permissions_policy_enabled and self.permissions_policy:
            pp_value = str(self.permissions_policy)
            if pp_value:
                headers["Permissions-Policy"] = pp_value

        # Cross-origin headers
        if self.cross_origin_embedder_policy:
            headers["Cross-Origin-Embedder-Policy"] = self.cross_origin_embedder_policy

        if self.cross_origin_opener_policy:
            headers["Cross-Origin-Opener-Policy"] = self.cross_origin_opener_policy

        if self.cross_origin_resource_policy:
            headers["Cross-Origin-Resource-Policy"] = self.cross_origin_resource_policy

        # Custom headers
        headers.update(self.custom_headers)

        return headers

    def add_custom_header(self, name: str, value: str) -> 'SecurityHeadersConfig':
        """Add a custom security header."""
        self.custom_headers[name] = value
        return self

    def configure_for_cdn(self, cdn_domains: List[str]) -> 'SecurityHeadersConfig':
        """Configure security headers for CDN usage."""
        if self.csp:
            # Allow scripts, styles, fonts from CDN
            self.csp.allow_external_scripts(cdn_domains)
            self.csp.allow_external_styles(cdn_domains)
            self.csp.allow_fonts_from(cdn_domains)

        # Update Cross-Origin-Resource-Policy for CDN
        if cdn_domains:
            self.cross_origin_resource_policy = "cross-origin"

        return self

    def configure_for_api(self, api_domains: List[str]) -> 'SecurityHeadersConfig':
        """Configure security headers for API usage."""
        if self.csp:
            # Allow connections to API domains
            self.csp.allow_api_endpoints(api_domains)

        return self

    def configure_for_development(self) -> 'SecurityHeadersConfig':
        """Configure headers for development environment."""
        self.environment = Environment.DEVELOPMENT

        # Very loose CSP for development to avoid any conflicts
        if self.csp:
            # Allow all script sources for maximum compatibility
            script_src = self.csp.get_directive("script-src")
            if script_src:
                script_src.add_source("'self'")
                script_src.add_source("'unsafe-inline'")
                script_src.add_source("'unsafe-eval'")
                script_src.add_source("https:")
                script_src.add_source("http:")
                # Allow external CDNs for Swagger UI
                script_src.add_source("https://cdn.jsdelivr.net")
                script_src.add_source("https://unpkg.com")
                script_src.add_source("https://cdnjs.cloudflare.com")

            # Allow external stylesheets (style-src-elem for external, style-src for inline)
            style_src = self.csp.get_directive("style-src")
            if style_src:
                style_src.add_source("'self'")
                style_src.add_source("'unsafe-inline'")
                # Allow external CDNs for Swagger UI styles
                style_src.add_source("https://cdn.jsdelivr.net")
                style_src.add_source("https://unpkg.com")
                style_src.add_source("https://cdnjs.cloudflare.com")

            # Add explicit style-src-elem for external stylesheets - ultra-permissive for development
            self.csp.add_directive(CSPDirective("style-src-elem", "'self'", "'unsafe-inline'", "https:", "http:", "https://cdn.jsdelivr.net", "https://unpkg.com", "https://cdnjs.cloudflare.com", "data:", "blob:"))

            # Add script-src-elem for external scripts (modern browsers) - ultra-permissive for development
            self.csp.add_directive(CSPDirective("script-src-elem", "'self'", "'unsafe-inline'", "'unsafe-eval'", "https:", "http:", "https://cdn.jsdelivr.net", "https://unpkg.com", "https://cdnjs.cloudflare.com", "data:", "blob:"))

            # Allow font-src for external fonts
            self.csp.add_directive(CSPDirective("font-src", "'self'", "https:", "http:", "data:"))

            # Allow image-src for external images
            self.csp.add_directive(CSPDirective("img-src", "'self'", "data:", "https:", "http:"))

            # Allow connect-src for any connections in development
            connect_src = self.csp.get_directive("connect-src")
            if connect_src:
                connect_src.add_source("'self'")
                connect_src.add_source("ws:")
                connect_src.add_source("wss:")
                connect_src.add_source("http:")
                connect_src.add_source("https:")
                connect_src.add_source("http://localhost:*")
                connect_src.add_source("http://127.0.0.1:*")

            # Allow webpack dev server and other development tools
            connect_src = self.csp.get_directive("connect-src")
            if connect_src:
                connect_src.add_source("ws:")
                connect_src.add_source("http://localhost:*")
                connect_src.add_source("http://127.0.0.1:*")

        # Add ultra-permissive default-src for development
        default_src = self.csp.get_directive("default-src")
        if default_src:
            default_src.add_source("'self'")
            default_src.add_source("'unsafe-inline'")
            default_src.add_source("'unsafe-eval'")
            default_src.add_source("https:")
            default_src.add_source("http:")
            default_src.add_source("data:")
            default_src.add_source("blob:")
            default_src.add_source("https://cdn.jsdelivr.net")
            default_src.add_source("https://unpkg.com")
            default_src.add_source("https://cdnjs.cloudflare.com")

        # Disable HSTS in development
        self.hsts_enabled = False

        # Completely disable permissions policy in development for maximum freedom
        if self.permissions_policy:
            # Clear ALL policies - no restrictions in development
            self.permissions_policy.policies = {}

        return self

    def configure_for_production(self) -> 'SecurityHeadersConfig':
        """Configure headers for production environment."""
        self.environment = Environment.PRODUCTION

        # Enable HSTS in production
        self.hsts_enabled = True

        # More restrictive CSP for production
        if self.csp:
            # Remove unsafe-inline from production CSP
            script_src = self.csp.get_directive("script-src")
            if script_src:
                script_src.sources = [src for src in script_src.sources if src != "'unsafe-inline'"]

        return self


class SecurityHeadersFactory:
    """
    Factory for creating environment-appropriate security header configurations.

    This class provides convenient methods to create security header configurations
    for different environments and use cases.
    """

    @staticmethod
    def create_default(environment: Environment = Environment.DEVELOPMENT) -> SecurityHeadersConfig:
        """
        Create default security headers configuration for the given environment.

        Args:
            environment: Target environment (development, production, testing)

        Returns:
            SecurityHeadersConfig instance
        """
        config = SecurityHeadersConfig(environment=environment)

        if environment == Environment.DEVELOPMENT:
            config.configure_for_development()
        elif environment == Environment.PRODUCTION:
            config.configure_for_production()
        elif environment == Environment.TESTING:
            # Minimal security headers for testing
            config.x_content_type_options = False
            config.x_frame_options = "SAMEORIGIN"
            config.csp_enabled = False
            config.hsts_enabled = False

        return config

    @staticmethod
    def create_for_single_page_app(cdn_domains: List[str] = None, api_domains: List[str] = None) -> SecurityHeadersConfig:
        """
        Create security headers configuration optimized for Single Page Applications.

        Args:
            cdn_domains: List of CDN domains for assets
            api_domains: List of API domains for backend calls

        Returns:
            SecurityHeadersConfig instance optimized for SPAs
        """
        config = SecurityHeadersFactory.create_default(Environment.PRODUCTION)

        # Configure CSP for SPA needs
        if config.csp:
            # Allow more sources for typical SPA requirements
            config.csp.allow_external_scripts(cdn_domains or [])
            config.csp.allow_external_styles(cdn_domains or [])
            config.csp.allow_api_endpoints(api_domains or [])

            # Allow common SPA features
            script_src = config.csp.get_directive("script-src")
            if script_src:
                script_src.add_source("'unsafe-eval'")

            connect_src = config.csp.get_directive("connect-src")
            if connect_src:
                connect_src.add_source("'self'")

        # Configure for CDN if specified
        if cdn_domains:
            config.configure_for_cdn(cdn_domains)

        return config

    @staticmethod
    def create_for_api_only(allowed_origins: List[str] = None) -> SecurityHeadersConfig:
        """
        Create security headers configuration for API-only applications.

        Args:
            allowed_origins: List of allowed origins for API access

        Returns:
            SecurityHeadersConfig instance optimized for APIs
        """
        config = SecurityHeadersFactory.create_default(Environment.PRODUCTION)

        # API-specific CSP
        if config.csp:
            # API doesn't need most CSP restrictions
            config.csp.remove_directive("script-src")
            config.csp.remove_directive("style-src")
            config.csp.remove_directive("font-src")
            config.csp.remove_directive("img-src")

            # Only essential restrictions for API
            config.csp.add_directive(CSPDirective("default-src", "'none'"))
            config.csp.add_directive(CSPDirective("frame-ancestors", "'none'"))

        # Restrict to API origins
        if allowed_origins and config.permissions_policy:
            config.permissions_policy.set_policy("geolocation", allowed_origins)

        return config

    @staticmethod
    def create_for_static_site(cdn_domains: List[str] = None) -> SecurityHeadersConfig:
        """
        Create security headers configuration for static websites.

        Args:
            cdn_domains: List of CDN domains for static assets

        Returns:
            SecurityHeadersConfig instance optimized for static sites
        """
        config = SecurityHeadersFactory.create_default(Environment.PRODUCTION)

        # Static site CSP - very restrictive
        if config.csp:
            # Only allow same-origin and CDN resources
            script_src = config.csp.get_directive("script-src")
            if script_src:
                script_src.sources = ["'self'"]
                if cdn_domains:
                    script_src.sources.extend(cdn_domains)

            style_src = config.csp.get_directive("style-src")
            if style_src:
                style_src.sources = ["'self'"]
                if cdn_domains:
                    style_src.sources.extend(cdn_domains)
                # Allow inline styles for static sites
                style_src.add_source("'unsafe-inline'")

        # Configure for CDN
        if cdn_domains:
            config.configure_for_cdn(cdn_domains)

        return config


def detect_environment() -> Environment:
    """
    Automatically detect the current environment.

    Returns:
        Detected environment (development, production, or testing)
    """
    # Check for production environment indicators
    production_indicators = [
        'production', 'prod', 'live', 'main', 'master', 'staging', 'stage'
    ]

    test_indicators = [
        'test', 'testing', 'ci', 'continuous', 'integration'
    ]

    # Check environment variables
    for env_var in ['ENV', 'ENVIRONMENT', 'APP_ENV', 'FLASK_ENV', 'DJANGO_SETTINGS_MODULE', 'NODE_ENV']:
        env_value = os.getenv(env_var, '').lower()
        if env_value in production_indicators:
            return Environment.PRODUCTION
        elif env_value in test_indicators:
            return Environment.TESTING

    # Check for development indicators
    if os.getenv('DEBUG', '').lower() in ['true', '1', 'yes', 'on']:
        return Environment.DEVELOPMENT

    # Check for common testing indicators
    if 'pytest' in os.sys.modules or 'unittest' in os.sys.modules:
        return Environment.TESTING

    # Default to development
    return Environment.DEVELOPMENT


def create_security_headers_from_config(config_dict: Dict[str, Any]) -> SecurityHeadersConfig:
    """
    Create SecurityHeadersConfig from a configuration dictionary.

    This allows loading security header configuration from environment
    variables, config files, or other sources.

    Args:
        config_dict: Dictionary containing security header configuration

    Returns:
        SecurityHeadersConfig instance
    """
    # Extract basic configuration
    environment = config_dict.get('environment', detect_environment())
    if isinstance(environment, str):
        environment = Environment(environment.lower())

    # Create base configuration
    headers_config = SecurityHeadersConfig(environment=environment)

    # Override with provided configuration
    for key, value in config_dict.items():
        if hasattr(headers_config, key) and key not in ['environment', 'csp', 'permissions_policy', 'custom_headers']:
            setattr(headers_config, key, value)

    # Handle CSP configuration
    csp_config = config_dict.get('csp')
    if isinstance(csp_config, dict):
        # Custom CSP configuration would be handled here
        pass

    # Handle custom headers
    custom_headers = config_dict.get('custom_headers')
    if isinstance(custom_headers, dict):
        for name, value in custom_headers.items():
            headers_config.add_custom_header(name, value)

    return headers_config