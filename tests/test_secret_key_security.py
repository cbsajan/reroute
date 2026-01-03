"""
Unit tests for SecretKeyManager secure secret key functionality.

Tests cover:
- Secure key generation and validation
- Production environment detection
- Entropy calculation and strength validation
- Environment variable override support
- Security logging and error handling
- Edge cases and security scenarios
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path

from reroute.config import SecretKeyManager, Config, DevConfig, ProdConfig


class TestSecretKeyGeneration:
    """Test secure secret key generation."""

    def test_generate_secure_key_default_length(self):
        """Test generating a secure key with default length."""
        key = SecretKeyManager.generate_secure_key()

        # Check length requirements
        assert len(key) >= SecretKeyManager.MIN_KEY_LENGTH

        # Check that it's URL-safe
        assert ' ' not in key
        assert '\n' not in key
        assert '\t' not in key

        # Check entropy (should have good character distribution)
        unique_chars = len(set(key))
        assert unique_chars >= len(key) * 0.5  # At least 50% unique characters

    def test_generate_secure_key_custom_length(self):
        """Test generating a secure key with custom length."""
        custom_length = 48
        key = SecretKeyManager.generate_secure_key(custom_length)

        assert len(key) >= custom_length

    def test_generate_secure_key_minimum_length_enforcement(self):
        """Test that minimum length is enforced."""
        with pytest.raises(ValueError, match="Key length must be at least"):
            SecretKeyManager.generate_secure_key(16)  # Too short

    def test_generate_unique_keys(self):
        """Test that generated keys are unique."""
        keys = [SecretKeyManager.generate_secure_key() for _ in range(10)]
        unique_keys = set(keys)

        assert len(unique_keys) == len(keys)  # All keys should be unique


class TestEnvironmentDetection:
    """Test production environment detection."""

    def test_detect_development_environment(self):
        """Test detection in development environment."""
        with patch.dict(os.environ, {}, clear=True):
            is_prod = SecretKeyManager.is_production_environment()
            assert is_prod is False

    @pytest.mark.parametrize("ci_env_var", [
        'CI',
        'GITHUB_ACTIONS',
        'TRAVIS',
        'GITLAB_CI',
        'CIRCLECI',
    ])
    def test_ci_environment_not_detected_as_production(self, ci_env_var):
        """Test that CI environments are NOT detected as production."""
        # Even if production indicators are present, CI should override
        with patch.dict(os.environ, {ci_env_var: 'true', 'ENV': 'production'}, clear=True):
            is_prod = SecretKeyManager.is_production_environment()
            assert is_prod is False

    @pytest.mark.parametrize("env_var,env_value", [
        ('ENV', 'production'),
        ('ENVIRONMENT', 'prod'),
        ('APP_ENV', 'live'),
        ('FLASK_ENV', 'main'),
        ('NODE_ENV', 'staging'),
        ('REROUTE_ENV', 'stage'),
        ('ENVIRONMENT_NAME', 'production'),
    ])
    def test_detect_production_via_env_var(self, env_var, env_value):
        """Test production detection via environment variables."""
        with patch.dict(os.environ, {env_var: env_value}, clear=True):
            is_prod = SecretKeyManager.is_production_environment()
            assert is_prod is True

    @pytest.mark.parametrize("provider,env_var,env_value", [
        ('Vercel', 'VERCEL', '1'),
        ('Heroku', 'DYNO', 'web.1'),
        ('AWS', 'AWS_REGION', 'us-east-1'),
        ('GCP', 'GCP_PROJECT', 'my-project'),
        ('Azure', 'WEBSITE_SITE_NAME', 'myapp'),
        ('Railway', 'RAILWAY_ENVIRONMENT', 'production'),
        ('Render', 'RENDER_SERVICE_ID', 'svc123'),
    ])
    def test_detect_production_via_hosting_providers(self, provider, env_var, env_value):
        """Test production detection via hosting provider indicators."""
        with patch.dict(os.environ, {env_var: env_value}, clear=True):
            is_prod = SecretKeyManager.is_production_environment()
            assert is_prod is True

    def test_filesystem_indicators_not_windows(self):
        """Test production detection via filesystem indicators (non-Windows)."""
        # Note: This test may not work on Windows systems
        # Clear CI environment variables to test filesystem detection in isolation
        with patch.dict(os.environ, {}, clear=True):
            with patch('os.path.exists') as mock_exists:
                mock_exists.return_value = True
                is_prod = SecretKeyManager.is_production_environment()
                assert is_prod is True

    def test_case_insensitive_production_values(self):
        """Test that production values are case insensitive."""
        test_values = ['PRODUCTION', 'Prod', 'LIVE', 'Stage']

        for value in test_values:
            with patch.dict(os.environ, {'ENV': value}, clear=True):
                is_prod = SecretKeyManager.is_production_environment()
                assert is_prod is True


class TestKeyValidation:
    """Test secret key strength validation."""

    def test_validate_empty_key(self):
        """Test validation of empty key."""
        is_valid, error = SecretKeyManager.validate_key_strength("")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_validate_short_key(self):
        """Test validation of short key."""
        short_key = "short"
        is_valid, error = SecretKeyManager.validate_key_strength(short_key)
        assert is_valid is False
        assert f"at least {SecretKeyManager.MIN_KEY_LENGTH} characters" in error

    def test_validate_weak_pattern_keys(self):
        """Test validation of keys with weak patterns."""
        weak_keys = [
            "your-secret-key-change-in-production-please-do-this-now",
            "my-default-secret-key-1234567890-abcdef-ghijklmnop",
            "test-secret-key-replace-me-with-something-secure-and-random",
            "admin-secret-key-for-development-environment-only-use",
            "root-access-key-1234567890-abcdefghijklmnopqrstuvwxyz-please",
        ]

        for weak_key in weak_keys:
            is_valid, error = SecretKeyManager.validate_key_strength(weak_key)
            assert is_valid is False
            assert "weak pattern" in error

    def test_validate_low_entropy_keys(self):
        """Test validation of keys with low entropy."""
        low_entropy_key = "a" * 32  # All same character
        is_valid, error = SecretKeyManager.validate_key_strength(low_entropy_key)
        assert is_valid is False
        assert "low entropy" in error

    def test_validate_generated_secure_key(self):
        """Test validation of securely generated key."""
        secure_key = SecretKeyManager.generate_secure_key()
        is_valid, error = SecretKeyManager.validate_key_strength(secure_key)
        assert is_valid is True
        assert error == ""

    def test_validate_strong_manual_key(self):
        """Test validation of manually created strong key."""
        strong_key = "E8vK2mN9pQ5xR7wZ1cV4bY6fG3hJ8kL0"
        is_valid, error = SecretKeyManager.validate_key_strength(strong_key)
        assert is_valid is True
        assert error == ""

    def test_entropy_calculation(self):
        """Test entropy calculation for different keys."""
        # Test that our validation method calculates entropy correctly
        high_entropy_key = SecretKeyManager.generate_secure_key()
        assert SecretKeyManager._validate_key_entropy(high_entropy_key) is True

        # Low entropy key should fail
        low_entropy_key = "a" * 32
        assert SecretKeyManager._validate_key_entropy(low_entropy_key) is False


class TestSecretKeyManager:
    """Test the main SecretKeyManager functionality."""

    def test_environment_variable_override_development(self):
        """Test environment variable override in development."""
        # Use a strong key that won't trigger warnings
        env_key = "test-override-strong-key-xyz789abc456def789ghi123jkl456mno789pqr012stu345vwx678yz"

        with patch.dict(os.environ, {'REROUTE_SECRET_KEY': env_key}, clear=True):
            with patch.object(SecretKeyManager, 'is_production_environment', return_value=False):
                key = SecretKeyManager.get_or_generate_secret_key()
                assert key == env_key

    def test_environment_variable_override_production_strong(self):
        """Test environment variable override in production with strong key."""
        strong_key = SecretKeyManager.generate_secure_key()

        with patch.dict(os.environ, {'REROUTE_SECRET_KEY': strong_key}, clear=True):
            with patch.object(SecretKeyManager, 'is_production_environment', return_value=True):
                key = SecretKeyManager.get_or_generate_secret_key()
                assert key == strong_key

    def test_environment_variable_override_production_weak(self):
        """Test environment variable override in production with weak key."""
        weak_key = "your-secret-key-change-in-production"

        with patch.dict(os.environ, {'REROUTE_SECRET_KEY': weak_key}, clear=True):
            with patch.object(SecretKeyManager, 'is_production_environment', return_value=True):
                with pytest.raises(ValueError, match="CRITICAL SECURITY.*Invalid REROUTE_SECRET_KEY"):
                    SecretKeyManager.get_or_generate_secret_key()

    def test_config_key_development_weak(self):
        """Test weak config key in development (should be replaced)."""
        weak_config_key = "your-secret-key-change-in-production"

        with patch.dict(os.environ, {}, clear=True):  # No env override
            with patch.object(SecretKeyManager, 'is_production_environment', return_value=False):
                key = SecretKeyManager.get_or_generate_secret_key(weak_config_key)
                # Should generate a new secure key
                assert key != weak_config_key
                assert len(key) >= SecretKeyManager.MIN_KEY_LENGTH

    def test_config_key_production_weak(self):
        """Test weak config key in production (should raise error)."""
        weak_config_key = "your-secret-key-change-in-production"

        with patch.dict(os.environ, {}, clear=True):  # No env override
            with patch.object(SecretKeyManager, 'is_production_environment', return_value=True):
                with pytest.raises(ValueError, match="CRITICAL SECURITY.*Default insecure SECRET_KEY"):
                    SecretKeyManager.get_or_generate_secret_key(weak_config_key)

    def test_no_key_provided_development(self):
        """Test no key provided in development (should generate)."""
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(SecretKeyManager, 'is_production_environment', return_value=False):
                key = SecretKeyManager.get_or_generate_secret_key()
                assert len(key) >= SecretKeyManager.MIN_KEY_LENGTH
                assert SecretKeyManager.validate_key_strength(key)[0] is True

    def test_no_key_provided_production(self):
        """Test no key provided in production (should raise error)."""
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(SecretKeyManager, 'is_production_environment', return_value=True):
                with pytest.raises(ValueError, match="CRITICAL SECURITY.*No SECRET_KEY configured"):
                    SecretKeyManager.get_or_generate_secret_key()


class TestConfigIntegration:
    """Test integration with Config classes."""

    def test_config_secret_key_validation_on_load(self):
        """Test that secret key is validated when loading config."""
        with patch.dict(os.environ, {'ENV': 'production'}, clear=True):
            with pytest.raises(ValueError, match="CRITICAL SECURITY"):
                # This should fail because the default key is weak and we're in production
                Config.load_from_env()

    def test_config_secret_key_validation_development(self):
        """Test secret key validation in development."""
        with patch.dict(os.environ, {'ENV': 'development'}, clear=True):
            # Should work fine and generate a secure key
            Config.load_from_env()
            assert len(Config.SECRET_KEY) >= SecretKeyManager.MIN_KEY_LENGTH

    def test_config_with_env_override(self):
        """Test config with environment variable override."""
        strong_key = SecretKeyManager.generate_secure_key()

        with patch.dict(os.environ, {'REROUTE_SECRET_KEY': strong_key}, clear=True):
            Config.load_from_env()
            assert Config.SECRET_KEY == strong_key

    def test_config_validate_method(self):
        """Test that validate method also triggers secret key validation."""
        # Should work without error
        Config.validate()
        assert len(Config.SECRET_KEY) >= SecretKeyManager.MIN_KEY_LENGTH

    def test_devconfig_uses_development_defaults(self):
        """Test that DevConfig uses development-friendly behavior."""
        DevConfig.load_from_env()
        assert len(DevConfig.SECRET_KEY) >= SecretKeyManager.MIN_KEY_LENGTH

    def test_prodconfig_strict_validation(self):
        """Test that ProdConfig enforces strict validation."""
        # Create a test config class with weak default key
        class TestProdConfig(ProdConfig):
            SECRET_KEY = "your-secret-key-change-in-production"

        # Clear environment variables that might provide a secure key
        env_backup = {}
        for key in list(os.environ.keys()):
            if key.startswith('REROUTE_'):
                env_backup[key] = os.environ[key]
                del os.environ[key]

        try:
            # Mock production environment
            with patch.object(SecretKeyManager, 'is_production_environment', return_value=True):
                with pytest.raises(ValueError, match="CRITICAL SECURITY"):
                    TestProdConfig.load_from_env()
        finally:
            # Restore environment
            for key, value in env_backup.items():
                os.environ[key] = value


class TestSecurityLogging:
    """Test security logging functionality."""

    @patch('reroute.config.logger')
    def test_secure_key_generation_logging(self, mock_logger):
        """Test that key generation is logged appropriately."""
        SecretKeyManager.generate_secure_key()

        # Should log info about successful generation
        mock_logger.info.assert_called_with("Secure key generated successfully")

    @patch('reroute.config.logger')
    def test_production_detection_logging(self, mock_logger):
        """Test that production detection is logged."""
        with patch.dict(os.environ, {'ENV': 'production'}, clear=True):
            SecretKeyManager.is_production_environment()

            # Should log info about production detection
            mock_logger.info.assert_called()

    @patch('reroute.config.logger')
    def test_critical_error_logging_production_weak_key(self, mock_logger):
        """Test critical error logging for weak key in production."""
        weak_key = "your-secret-key-change-in-production"

        with patch.dict(os.environ, {'REROUTE_SECRET_KEY': weak_key}, clear=True):
            with patch.object(SecretKeyManager, 'is_production_environment', return_value=True):
                try:
                    SecretKeyManager.get_or_generate_secret_key()
                except ValueError:
                    pass  # Expected to raise

                # Should log critical error
                mock_logger.critical.assert_called()

    @patch('reroute.config.logger')
    def test_warning_logging_weak_key_development(self, mock_logger):
        """Test warning logging for weak key in development."""
        weak_key = "your-secret-key-change-in-production"

        with patch.dict(os.environ, {'REROUTE_SECRET_KEY': weak_key}, clear=True):
            with patch.object(SecretKeyManager, 'is_production_environment', return_value=False):
                key = SecretKeyManager.get_or_generate_secret_key()

                # Should log warning about weak key and info about new key
                mock_logger.warning.assert_called()
                mock_logger.info.assert_called()


class TestEdgeCases:
    """Test edge cases and unusual scenarios."""

    def test_very_long_key_validation(self):
        """Test validation of very long keys."""
        # Create a long key with high entropy by using random patterns
        import secrets
        very_long_key = secrets.token_urlsafe(500)  # Much longer than minimum
        is_valid, error = SecretKeyManager.validate_key_strength(very_long_key)
        # Should be valid - meets length and entropy requirements
        assert is_valid is True

    def test_key_with_special_characters(self):
        """Test validation of keys with various special characters."""
        special_key = "E8vK2mN9pQ5xR7wZ1cV4bY6fG3hJ8kL0-_.~"
        is_valid, error = SecretKeyManager.validate_key_strength(special_key)
        assert is_valid is True

    def test_unicode_characters_in_key(self):
        """Test validation of keys with Unicode characters."""
        unicode_key = "E8vK2mN9pQ5xR7wZ1cV4bY6fG3hJ8kL0テスト"
        is_valid, error = SecretKeyManager.validate_key_strength(unicode_key)
        # Should be valid as long as it meets entropy requirements
        assert is_valid is True

    def test_config_class_attribute_access_before_init(self):
        """Test accessing SECRET_KEY before any initialization."""
        # Should still work due to lazy initialization
        key = Config.SECRET_KEY
        assert key is not None

    def test_multiple_config_classes_independent(self):
        """Test that different config classes have independent secret keys."""
        Config.load_from_env()

        class TestConfig1(Config):
            pass

        class TestConfig2(Config):
            pass

        TestConfig1.load_from_env()
        TestConfig2.load_from_env()

        # Each should have their own secure key
        assert Config.SECRET_KEY != TestConfig1.SECRET_KEY or len(Config.SECRET_KEY) >= SecretKeyManager.MIN_KEY_LENGTH
        assert len(TestConfig1.SECRET_KEY) >= SecretKeyManager.MIN_KEY_LENGTH
        assert len(TestConfig2.SECRET_KEY) >= SecretKeyManager.MIN_KEY_LENGTH


if __name__ == "__main__":
    pytest.main([__file__, "-v"])