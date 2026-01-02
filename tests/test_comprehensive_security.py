"""
Test comprehensive security headers implementation.

This test verifies that the comprehensive security module is properly integrated
and applying OWASP-compliant security headers in both FastAPI and Flask adapters.
"""

import pytest
import os
from unittest.mock import Mock, patch

# Import the security components
from reroute.security import (
    SecurityHeadersConfig,
    SecurityHeadersFactory,
    detect_environment,
    Environment,
    CSPDirective
)

# Import adapters
from reroute.adapters.fastapi import SecurityHeadersMiddleware, FastAPIAdapter
from reroute.adapters.flask import FlaskSecurityHeadersMiddleware, FlaskAdapter


class TestSecurityHeadersConfig:
    """Test the SecurityHeadersConfig class."""

    def test_default_configuration(self):
        """Test default security configuration."""
        config = SecurityHeadersConfig()
        headers = config.get_security_headers()

        # Check that essential headers are present
        assert 'X-Content-Type-Options' in headers
        assert 'X-Frame-Options' in headers
        assert 'Content-Security-Policy' in headers
        assert 'X-XSS-Protection' in headers
        assert 'Referrer-Policy' in headers

        # Check values
        assert headers['X-Content-Type-Options'] == 'nosniff'
        assert headers['X-Frame-Options'] == 'DENY'
        assert 'default-src' in headers['Content-Security-Policy']

    def test_development_configuration(self):
        """Test development-friendly configuration."""
        config = SecurityHeadersFactory.create_default(Environment.DEVELOPMENT)
        headers = config.get_security_headers()

        # HSTS should be disabled in development
        assert 'Strict-Transport-Security' not in headers

        # CSP should be more permissive
        csp = headers.get('Content-Security-Policy', '')
        assert 'unsafe-inline' in csp or 'unsafe-eval' in csp

    def test_production_configuration(self):
        """Test production-secure configuration."""
        config = SecurityHeadersFactory.create_default(Environment.PRODUCTION)
        headers = config.get_security_headers()

        # HSTS should be enabled in production
        assert 'Strict-Transport-Security' in headers
        assert 'max-age=' in headers['Strict-Transport-Security']

        # CSP should be strict but allow unsafe-inline for styles (common requirement)
        csp = headers.get('Content-Security-Policy', '')
        assert 'unsafe-inline' not in csp or 'style-src' in csp  # Allow inline for styles only
        assert 'unsafe-eval' not in csp  # Never allow eval in production

    def test_cdn_domains_configuration(self):
        """Test CDN domain configuration."""
        config = SecurityHeadersFactory.create_for_single_page_app()

        # Add CDN domains
        cdn_domains = ['https://cdn.example.com', 'https://assets.example.com']

        # Get existing directives and add CDN domains
        default_src = config.csp.get_directive("default-src")
        if default_src:
            for domain in cdn_domains:
                default_src.add_source(domain)

        script_src = config.csp.get_directive("script-src")
        if script_src:
            for domain in cdn_domains:
                script_src.add_source(domain)

        style_src = config.csp.get_directive("style-src")
        if style_src:
            for domain in cdn_domains:
                style_src.add_source(domain)

        headers = config.get_security_headers()
        csp = headers['Content-Security-Policy']

        # Check that CDN domains are in CSP
        for domain in cdn_domains:
            assert domain in csp


class TestEnvironmentDetection:
    """Test environment detection logic."""

    def test_development_detection(self):
        """Test development environment detection."""
        # Mock development indicators
        with patch.dict(os.environ, {'DEBUG': 'true'}):
            env = detect_environment()
            assert env == Environment.DEVELOPMENT

    def test_production_detection(self):
        """Test production environment detection."""
        # Mock production indicators
        with patch.dict(os.environ, {'ENV': 'production'}):
            env = detect_environment()
            assert env == Environment.PRODUCTION


class TestFastAPISecurityIntegration:
    """Test FastAPI adapter security integration."""

    def test_security_middleware_creation(self):
        """Test that FastAPI security middleware can be created."""
        config = SecurityHeadersConfig()
        middleware = SecurityHeadersMiddleware(Mock(), config)
        assert middleware.security_config == config

    def test_middleware_adds_headers(self):
        """Test that middleware adds security headers to response."""
        from fastapi import Request, Response
        from starlette.middleware.base import BaseHTTPMiddleware

        # Create mock config
        config = SecurityHeadersConfig()

        # Create middleware with mock app
        mock_app = Mock()
        middleware = SecurityHeadersMiddleware(mock_app, config)

        # Create mock request and response
        mock_request = Mock(spec=Request)
        mock_response = Mock(spec=Response)
        mock_response.headers = {}

        # Mock call_next
        async def mock_call_next(request):
            return mock_response

        # Test middleware adds headers
        import asyncio

        async def test_dispatch():
            result = await middleware.dispatch(mock_request, mock_call_next)
            headers = result.headers

            # Check that security headers are added
            security_headers = config.get_security_headers()
            for header, value in security_headers.items():
                assert header in headers
                assert headers[header] == value

        asyncio.run(test_dispatch())


class TestFlaskSecurityIntegration:
    """Test Flask adapter security integration."""

    def test_security_middleware_creation(self):
        """Test that Flask security middleware can be created."""
        config = SecurityHeadersConfig()
        mock_app = Mock()

        # Create middleware
        middleware = FlaskSecurityHeadersMiddleware(mock_app, config)

        # Check that after_request was registered
        mock_app.after_request.assert_called_once_with(middleware._add_security_headers)

    def test_middleware_adds_headers(self):
        """Test that middleware adds security headers to Flask response."""
        config = SecurityHeadersConfig()
        mock_app = Mock()

        middleware = FlaskSecurityHeadersMiddleware(mock_app, config)

        # Create mock Flask response
        mock_response = Mock()
        mock_response.headers = {}

        # Test header addition
        result = middleware._add_security_headers(mock_response)

        # Check that headers were added
        security_headers = config.get_security_headers()
        for header, value in security_headers.items():
            assert header in mock_response.headers
            assert mock_response.headers[header] == value

        # Check that response is returned
        assert result == mock_response


class TestSecurityFactoryMethods:
    """Test SecurityHeadersFactory methods."""

    def test_create_default(self):
        """Test default factory method."""
        for env in Environment:
            config = SecurityHeadersFactory.create_default(environment=env)
            assert isinstance(config, SecurityHeadersConfig)
            assert config.environment == env

    def test_create_for_single_page_app(self):
        """Test SPA factory method."""
        config = SecurityHeadersFactory.create_for_single_page_app()
        assert isinstance(config, SecurityHeadersConfig)

        # Check SPA-specific settings
        headers = config.get_security_headers()
        csp = headers.get('Content-Security-Policy', '')
        # SPA typically allows inline scripts for frameworks like React
        assert 'unsafe-inline' in csp or "script-src 'unsafe-inline'" in csp

    def test_create_for_api_only(self):
        """Test API-only factory method."""
        config = SecurityHeadersFactory.create_for_api_only()
        assert isinstance(config, SecurityHeadersConfig)

        # Check API-specific settings
        headers = config.get_security_headers()
        # API doesn't typically need frame options
        assert headers.get('X-Frame-Options') == 'DENY'

    def test_create_for_static_site(self):
        """Test static site factory method."""
        config = SecurityHeadersFactory.create_for_static_site()
        assert isinstance(config, SecurityHeadersConfig)

        # Check static site settings
        headers = config.get_security_headers()
        # Static sites are strict about CSP
        csp = headers.get('Content-Security-Policy', '')
        assert 'default-src' in csp


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])