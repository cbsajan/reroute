"""
Unit tests for reroute.security.crypto module.
"""

import pytest
import time
from reroute.security.crypto import (
    hash_password,
    verify_password,
    generate_jwt_token,
    verify_jwt_token,
    decode_jwt_token,
    generate_secret_key,
    generate_reset_token,
    generate_api_key,
    generate_session_id,
    Argon2Config,
)


class TestPasswordHashing:
    """Test password hashing with Argon2."""

    def test_hash_password(self):
        """Test basic password hashing."""
        password = "my_secure_password"
        hashed = hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert hashed.startswith("$argon2id$")

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "my_secure_password"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification fails with wrong password."""
        password = "my_secure_password"
        wrong_password = "wrong_password"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_hash_uniqueness(self):
        """Test same password produces different hashes."""
        password = "my_secure_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes should be different (different salts)
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_hash_with_pepper(self):
        """Test password hashing with pepper."""
        password = "my_secure_password"
        pepper = "my_secret_pepper"

        hash1 = hash_password(password, pepper=pepper)
        hash2 = hash_password(password, pepper=pepper)
        hash3 = hash_password(password)  # No pepper

        # With pepper should produce different hash
        assert hash1 != hash3
        # Same pepper should verify correctly
        assert verify_password(password, hash1, pepper=pepper) is True
        # Wrong pepper should fail
        assert verify_password(password, hash1) is False

    def test_hash_custom_config(self):
        """Test password hashing with custom Argon2 configuration."""
        password = "my_secure_password"
        config = Argon2Config(
            time_cost=2,
            memory_cost=32768,  # 32 MB
            parallelism=2
        )

        hashed = hash_password(password, config=config)
        assert hashed is not None
        assert verify_password(password, hashed) is True

    def test_hash_empty_password(self):
        """Test that empty password raises error."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            hash_password("")

    @pytest.mark.parametrize("password", [
        "short",
        " ",
        "a" * 1000,
        "password!@#$%^&*()",
        "ünïcödé",
        "משפט בעברית",
        "\n\t\r",
    ])
    def test_password_edge_cases(self, password):
        """Test password hashing with edge cases."""
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True


class TestJWTTokens:
    """Test JWT token generation and verification."""

    def test_generate_jwt_token(self):
        """Test basic JWT token generation."""
        payload = {"user_id": 123, "email": "user@example.com"}
        secret = "test_secret"
        token = generate_jwt_token(payload, secret)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_jwt_token_valid(self):
        """Test JWT verification with valid token."""
        payload = {"user_id": 123, "email": "user@example.com"}
        secret = "test_secret"
        token = generate_jwt_token(payload, secret)

        decoded = verify_jwt_token(token, secret)
        assert decoded["user_id"] == 123
        assert decoded["email"] == "user@example.com"
        assert "exp" in decoded
        assert "iat" in decoded

    def test_verify_jwt_token_invalid(self):
        """Test JWT verification fails with invalid token."""
        payload = {"user_id": 123}
        secret = "test_secret"
        token = generate_jwt_token(payload, secret)

        # Wrong secret
        with pytest.raises(Exception):
            verify_jwt_token(token, "wrong_secret")

        # Invalid token format
        with pytest.raises(Exception):
            verify_jwt_token("invalid_token", secret)

    def test_jwt_expiry(self):
        """Test JWT token expiry."""
        payload = {"user_id": 123}
        secret = "test_secret"

        # Create token with 1 second expiry
        token = generate_jwt_token(payload, secret, expiry_seconds=1)

        # Should verify immediately
        decoded = verify_jwt_token(token, secret)
        assert decoded["user_id"] == 123

        # Wait for expiry
        time.sleep(2)

        # Should fail after expiry
        with pytest.raises(Exception):
            verify_jwt_token(token, secret)

    def test_jwt_custom_payload(self):
        """Test JWT with custom payload."""
        payload = {
            "user_id": 123,
            "email": "user@example.com",
            "role": "admin"
        }
        secret = "test_secret"
        token = generate_jwt_token(payload, secret, expiry_seconds=3600)

        decoded = verify_jwt_token(token, secret)
        assert decoded["user_id"] == 123
        assert decoded["email"] == "user@example.com"
        assert decoded["role"] == "admin"

    def test_jwt_additional_claims(self):
        """Test JWT with additional standard claims."""
        payload = {"user_id": 123}
        secret = "test_secret"
        additional = {
            "iss": "my-app",
            "aud": "my-api",
            "sub": "user123"
        }

        token = generate_jwt_token(
            payload,
            secret,
            additional_claims=additional
        )

        decoded = verify_jwt_token(
            token,
            secret,
            issuer="my-app",
            audience="my-api"
        )
        assert decoded["user_id"] == 123
        assert decoded["iss"] == "my-app"
        assert decoded["aud"] == "my-api"
        assert decoded["sub"] == "user123"

    def test_jwt_empty_secret(self):
        """Test that empty secret raises error."""
        with pytest.raises(ValueError, match="Secret key cannot be empty"):
            generate_jwt_token({"user_id": 123}, "")

    def test_decode_jwt_token_no_verification(self):
        """Test JWT decoding without verification."""
        payload = {"user_id": 123, "email": "user@example.com"}
        secret = "test_secret"
        token = generate_jwt_token(payload, secret)

        # Decode without verification
        decoded = decode_jwt_token(token, verify=False)
        assert decoded["user_id"] == 123
        assert decoded["email"] == "user@example.com"


class TestSecureRandomGeneration:
    """Test secure random token generation."""

    def test_generate_secret_key(self):
        """Test secret key generation."""
        key = generate_secret_key()

        assert key is not None
        assert isinstance(key, str)
        assert len(key) == 64  # 32 bytes = 64 hex chars

    def test_generate_secret_key_custom_length(self):
        """Test secret key generation with custom length."""
        key16 = generate_secret_key(16)
        key64 = generate_secret_key(64)

        assert len(key16) == 32  # 16 bytes = 32 hex chars
        assert len(key64) == 128  # 64 bytes = 128 hex chars

    def test_generate_secret_key_minimum_length(self):
        """Test that minimum length is enforced."""
        with pytest.raises(ValueError, match="at least 16 bytes"):
            generate_secret_key(8)

    def test_generate_reset_token(self):
        """Test reset token generation."""
        token = generate_reset_token()

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_api_key(self):
        """Test API key generation."""
        key = generate_api_key()

        assert key is not None
        assert isinstance(key, str)
        assert key.startswith("ruk_")

    def test_generate_api_key_custom_prefix(self):
        """Test API key generation with custom prefix."""
        key = generate_api_key(prefix="test")

        assert key.startswith("test_")

    def test_generate_session_id(self):
        """Test session ID generation."""
        session_id = generate_session_id()

        assert session_id is not None
        assert isinstance(session_id, str)
        assert len(session_id) > 0

    def test_token_uniqueness(self):
        """Test generated tokens are unique."""
        tokens = [generate_secret_key() for _ in range(100)]

        # All tokens should be unique
        assert len(set(tokens)) == 100

    @pytest.mark.parametrize("length", [16, 32, 64, 128])
    def test_token_length(self, length):
        """Test token length parameter."""
        key = generate_secret_key(length)
        expected_length = length * 2  # Hex encoding
        assert len(key) == expected_length


class TestSecurityAttacks:
    """Test security against common attacks."""

    def test_timing_attack_resistance(self):
        """Test password verification is timing-attack resistant."""
        password = "my_secure_password"
        hashed = hash_password(password)

        # Take multiple measurements to reduce noise
        iterations = 50

        # Time correct password verification
        start = time.time()
        for _ in range(iterations):
            verify_password(password, hashed)
        time_correct = (time.time() - start) / iterations

        # Time incorrect password verification
        start = time.time()
        for _ in range(iterations):
            verify_password("wrong_password", hashed)
        time_incorrect = (time.time() - start) / iterations

        # Times should be similar (within 50ms per operation)
        # This is a basic test; real timing attacks need more samples
        # Using relaxed threshold for CI stability
        assert abs(time_correct - time_incorrect) < 0.05

    def test_jwt_algorithm_confusion(self):
        """Test JWT algorithm confusion attack prevention."""
        payload = {"user_id": 123}
        secret = "test_secret"

        # Generate token with HS256
        token = generate_jwt_token(payload, secret, algorithm="HS256")

        # Try to verify with different algorithm list (should fail)
        # This tests that we're enforcing algorithm specification
        with pytest.raises(Exception):
            verify_jwt_token(token, secret, algorithms=["RS256"])

    def test_token_predictability(self):
        """Test tokens are not predictable."""
        # Generate multiple tokens
        tokens = [generate_secret_key() for _ in range(10)]

        # Check that tokens don't follow obvious patterns
        # All tokens should be different
        assert len(set(tokens)) == 10

        # Check that tokens don't contain predictable sequences
        for token in tokens:
            # Token should be hex-encoded
            assert all(c in "0123456789abcdef" for c in token)

    def test_password_hash_not_reversible(self):
        """Test that password hashes cannot be reversed."""
        password = "my_secure_password"
        hashed = hash_password(password)

        # Hash should not contain password
        assert password not in hashed

    def test_jwt_without_signature_check_fails(self):
        """Test that JWTs without proper verification fail."""
        payload = {"user_id": 123}
        secret = "test_secret"
        token = generate_jwt_token(payload, secret)

        # Tamper with token
        tampered_token = token[:-10] + "tampered"

        # Should fail verification
        with pytest.raises(Exception):
            verify_jwt_token(tampered_token, secret)
