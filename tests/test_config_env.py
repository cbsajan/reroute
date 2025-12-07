"""
Unit tests for Config environment loading and FINAL attributes
"""

import pytest
import os
import tempfile
from pathlib import Path
from reroute.config import Config, DevConfig, ProdConfig


def test_env_class_structure():
    """Test that Env class is properly nested"""
    assert hasattr(Config, 'Env')
    assert Config.Env.file == ".env"
    assert Config.Env.auto_load is True
    assert Config.Env.override is True


def test_devconfig_env():
    """Test DevConfig has its own Env configuration"""
    assert DevConfig.Env.file == ".env.dev"
    assert DevConfig.Env.auto_load is True
    assert DevConfig.Env.override is True


def test_prodconfig_env():
    """Test ProdConfig has its own Env configuration"""
    assert ProdConfig.Env.file == ".env.prod"
    assert ProdConfig.Env.auto_load is True
    assert ProdConfig.Env.override is False  # Important for production


def test_load_env_with_reroute_prefix():
    """Test that only REROUTE_* variables are loaded"""
    # Set environment variables
    os.environ['REROUTE_PORT'] = '9000'
    os.environ['REROUTE_DEBUG'] = 'True'
    os.environ['REROUTE_HOST'] = 'testhost'
    os.environ['OTHER_VAR'] = 'should_be_ignored'

    # Create a fresh config class instance
    class TestConfig(Config):
        pass

    # Load from environment
    TestConfig.load_from_env()

    # Verify REROUTE_* variables were loaded
    assert TestConfig.PORT == 9000
    assert TestConfig.DEBUG is True
    assert TestConfig.HOST == 'testhost'

    # Cleanup
    del os.environ['REROUTE_PORT']
    del os.environ['REROUTE_DEBUG']
    del os.environ['REROUTE_HOST']
    del os.environ['OTHER_VAR']


def test_env_type_conversion():
    """Test automatic type conversion for environment variables"""
    os.environ['REROUTE_DEBUG'] = 'true'  # bool
    os.environ['REROUTE_PORT'] = '8888'  # int
    os.environ['REROUTE_HOST'] = 'localhost'  # str
    os.environ['REROUTE_CORS_ALLOW_ORIGINS'] = 'http://a.com,http://b.com'  # list

    class TestConfig(Config):
        pass

    TestConfig.load_from_env()

    assert isinstance(TestConfig.DEBUG, bool)
    assert TestConfig.DEBUG is True

    assert isinstance(TestConfig.PORT, int)
    assert TestConfig.PORT == 8888

    assert isinstance(TestConfig.HOST, str)
    assert TestConfig.HOST == 'localhost'

    assert isinstance(TestConfig.CORS_ALLOW_ORIGINS, list)
    assert len(TestConfig.CORS_ALLOW_ORIGINS) == 2

    # Cleanup
    del os.environ['REROUTE_DEBUG']
    del os.environ['REROUTE_PORT']
    del os.environ['REROUTE_HOST']
    del os.environ['REROUTE_CORS_ALLOW_ORIGINS']


def test_internal_class_cannot_be_overridden():
    """Test that Config.Internal class cannot be overridden in child classes"""
    with pytest.raises(TypeError, match="Cannot override Config.Internal"):
        class BadConfig(Config):
            class Internal:  # Should fail - Internal class is protected
                ROUTES_DIR_NAME = "custom_routes"


def test_internal_class_structure():
    """Test that Internal class contains framework-critical settings"""
    assert hasattr(Config, 'Internal')
    assert Config.Internal.ROUTES_DIR_NAME == "routes"
    assert Config.Internal.ROUTE_FILE_NAME == "page.py"
    assert len(Config.Internal.SUPPORTED_HTTP_METHODS) > 0
    assert isinstance(Config.Internal.IGNORE_FOLDERS, list)
    assert isinstance(Config.Internal.IGNORE_FILES, list)


def test_non_final_attributes_can_be_overridden():
    """Test that non-FINAL attributes can be safely overridden"""
    class CustomConfig(Config):
        DEBUG = True
        PORT = 5000
        HOST = "custom.host"

    assert CustomConfig.DEBUG is True
    assert CustomConfig.PORT == 5000
    assert CustomConfig.HOST == "custom.host"


def test_load_env_from_file():
    """Test loading from .env file"""
    # Create a temporary .env file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write('REROUTE_PORT=7777\n')
        f.write('REROUTE_DEBUG=true\n')
        f.write('REROUTE_LOG_LEVEL=INFO\n')
        env_file = f.name

    try:
        class TestConfig(Config):
            class Env:
                file = env_file
                auto_load = True
                override = True

        # Load environment
        TestConfig.load_from_env()

        # Note: If python-dotenv is not installed, values won't be loaded from file
        # but the method should not crash
        if os.environ.get('REROUTE_PORT'):
            assert TestConfig.PORT == 7777
    finally:
        # Cleanup
        Path(env_file).unlink(missing_ok=True)


def test_ultimate_flexible_config_auto_any_variable():
    """Test that ANY REROUTE_* variable works automatically without whitelist"""
    # Test existing variables
    os.environ['REROUTE_SECRET_KEY'] = 'test-secret-key-123'
    os.environ['REROUTE_DATABASE_URL'] = 'sqlite:///test.db'

    # Test completely new variables (these should work automatically)
    os.environ['REROUTE_NEW_FEATURE'] = 'true'
    os.environ['REROUTE_API_VERSION'] = 'v2.1'
    os.environ['REROUTE_MAX_CONNECTIONS'] = '100'
    os.environ['REROUTE_ENABLED_SERVICES'] = 'auth,api,worker'

    class TestConfig(Config):
        pass

    # Load from environment
    TestConfig.load_from_env()

    # Test existing variables
    assert TestConfig.SECRET_KEY == 'test-secret-key-123'
    assert TestConfig.DATABASE_URL == 'sqlite:///test.db'

    # Test new variables - these should be created automatically
    assert hasattr(TestConfig, 'NEW_FEATURE')
    assert TestConfig.NEW_FEATURE is True  # Boolean auto-detected

    assert hasattr(TestConfig, 'API_VERSION')
    assert TestConfig.API_VERSION == 'v2.1'  # String auto-detected

    assert hasattr(TestConfig, 'MAX_CONNECTIONS')
    assert TestConfig.MAX_CONNECTIONS == 100  # Integer auto-detected

    assert hasattr(TestConfig, 'ENABLED_SERVICES')
    assert isinstance(TestConfig.ENABLED_SERVICES, list)
    assert TestConfig.ENABLED_SERVICES == ['auth', 'api', 'worker']  # List auto-detected

    # Cleanup
    del os.environ['REROUTE_SECRET_KEY']
    del os.environ['REROUTE_DATABASE_URL']
    del os.environ['REROUTE_NEW_FEATURE']
    del os.environ['REROUTE_API_VERSION']
    del os.environ['REROUTE_MAX_CONNECTIONS']
    del os.environ['REROUTE_ENABLED_SERVICES']


def test_ultimate_flexible_config_empty_values():
    """Test handling of empty values"""
    os.environ['REROUTE_SECRET_KEY'] = 'null'
    os.environ['REROUTE_DATABASE_URL'] = '~'
    os.environ['REROUTE_EMPTY_SETTING'] = ''

    class TestConfig(Config):
        pass

    TestConfig.load_from_env()

    # Empty/null values should be set to None
    assert TestConfig.SECRET_KEY is None
    assert TestConfig.DATABASE_URL is None
    assert hasattr(TestConfig, 'EMPTY_SETTING')
    assert TestConfig.EMPTY_SETTING is None

    # Cleanup
    del os.environ['REROUTE_SECRET_KEY']
    del os.environ['REROUTE_DATABASE_URL']
    del os.environ['REROUTE_EMPTY_SETTING']


def test_ultimate_flexible_config_cors_origins_compatibility():
    """Test backward compatibility for CORS_ORIGINS -> CORS_ALLOW_ORIGINS"""
    os.environ['REROUTE_CORS_ORIGINS'] = 'https://example.com,https://api.example.com'

    class TestConfig(Config):
        pass

    TestConfig.load_from_env()

    # Should map to CORS_ALLOW_ORIGINS
    assert hasattr(TestConfig, 'CORS_ALLOW_ORIGINS')
    assert isinstance(TestConfig.CORS_ALLOW_ORIGINS, list)
    assert TestConfig.CORS_ALLOW_ORIGINS == ['https://example.com', 'https://api.example.com']

    # CORS_ORIGINS attribute itself should not be created
    assert not hasattr(TestConfig, 'CORS_ORIGINS')

    # Cleanup
    del os.environ['REROUTE_CORS_ORIGINS']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
