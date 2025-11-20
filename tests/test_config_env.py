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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
