"""
Security Test Suite for SQL Injection Protection

Tests the enhanced security features implemented in the Model class
to prevent SQL injection attacks via order_by parameter.

Critical Test Coverage:
- SQL injection attempt detection and logging
- Parameter validation and sanitization
- Whitelist-based column validation
- Direction validation (asc/desc)
- Error handling and security logging
- Edge cases and boundary conditions
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

# Import the secure model classes
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from reroute.db.models import Model, Base, SecurityValidationError


class TestUser(Model):
    """Test model for security testing."""
    __tablename__ = 'test_users'

    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    age = Column(Integer)


class TestSecurityValidation:
    """Test security validation methods."""

    @pytest.fixture
    def session(self):
        """Create test database session."""
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        return Session()

    def test_get_allowed_columns_success(self):
        """Test successful column whitelist retrieval."""
        columns = TestUser._get_allowed_columns()
        expected_columns = {'id', 'name', 'email', 'age', 'created_at', 'updated_at'}
        assert columns == expected_columns

    def test_validate_order_by_valid_parameters(self):
        """Test validation of legitimate order_by parameters."""
        # Test basic column names
        assert TestUser._validate_order_by_parameter("name") == ("name", "asc")
        assert TestUser._validate_order_by_parameter("email") == ("email", "asc")

        # Test with direction
        assert TestUser._validate_order_by_parameter("name asc") == ("name", "asc")
        assert TestUser._validate_order_by_parameter("created_at desc") == ("created_at", "desc")

        # Test case insensitivity and spaces
        assert TestUser._validate_order_by_parameter("  NAME  DESC  ") == ("name", "desc")

    def test_validate_order_by_invalid_direction(self):
        """Test rejection of invalid direction parameters."""
        with pytest.raises(ValueError, match="Direction must be 'asc' or 'desc'"):
            TestUser._validate_order_by_parameter("name invalid")

        with pytest.raises(ValueError, match="Direction must be 'asc' or 'desc'"):
            TestUser._validate_order_by_parameter("name ascending")

    def test_validate_order_by_invalid_format(self):
        """Test rejection of malformed order_by parameters."""
        with pytest.raises(ValueError, match="order_by format should be"):
            TestUser._validate_order_by_parameter("name desc extra")

        with pytest.raises(ValueError, match="order_by format should be"):
            TestUser._validate_order_by_parameter("name desc invalid another")

    def test_validate_order_by_invalid_column_names(self):
        """Test rejection of invalid column name formats."""
        with pytest.raises(SecurityValidationError, match="Invalid column name format"):
            TestUser._validate_order_by_parameter("123name")

        with pytest.raises(SecurityValidationError, match="Invalid column name format"):
            TestUser._validate_order_by_parameter("name-with-dash")

        with pytest.raises(SecurityValidationError, match="Invalid column name format"):
            TestUser._validate_order_by_parameter("name with space")

        # This should be caught as SQL injection, not just invalid format
        with pytest.raises(SecurityValidationError, match="SQL injection attempt"):
            TestUser._validate_order_by_parameter("name;semicolon")

    def test_validate_order_by_nonexistent_columns(self):
        """Test rejection of non-existent column names."""
        with pytest.raises(ValueError, match="Invalid order_by column"):
            TestUser._validate_order_by_parameter("nonexistent")

        with pytest.raises(ValueError, match="Invalid order_by column"):
            TestUser._validate_order_by_parameter("password desc")

        # Check that error message includes valid columns
        try:
            TestUser._validate_order_by_parameter("fake_column")
        except ValueError as e:
            assert "id" in str(e)
            assert "name" in str(e)
            assert "email" in str(e)

    def test_validate_order_by_sql_injection_attempts(self):
        """Test detection and rejection of SQL injection attempts."""
        injection_attempts = [
            # Basic SQL injection
            "'; DROP TABLE users; --",
            "name'; DELETE FROM users; --",
            "name OR 1=1",
            "name AND 1=1",
            "name UNION SELECT * FROM users",

            # Advanced injection attempts
            "name; SELECT pg_sleep(5); --",
            "name'; WAITFOR DELAY '00:00:05'; --",
            "name OR '1'='1",
            "name' OR 'x'='x",

            # Information schema attempts
            "information_schema.tables",
            "sys.objects",
            "pg_catalog.pg_tables",
            "mysql.sys.user",

            # Function-based attacks
            "BENCHMARK(1000000,MD5(1))",
            "SLEEP(5)",
            "pg_sleep(5)",

            # Script injection
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "eval('malicious code')",

            # File operations
            "LOAD_FILE('/etc/passwd')",
            "INTO OUTFILE '/tmp/malicious.txt'",

            # Conversion functions
            "CONVERT('data', SQL_INT)",
            "CAST('data' AS SQL_INT)",
            "CHAR(65,66,67)",
            "ASCII('test')",

            # String functions
            "SUBSTRING(password,1,1)",
            "LEN(password)",
            "LENGTH(password)",
            "CONCAT(user,password)",
        ]

        for injection in injection_attempts:
            with pytest.raises(SecurityValidationError, match="SQL injection attempt"):
                TestUser._validate_order_by_parameter(injection)

    def test_validate_order_by_parameter_length_limits(self):
        """Test protection against buffer overflow attempts."""
        # Create a very long parameter
        long_param = "a" * 101
        with pytest.raises(SecurityValidationError, match="exceeds maximum length"):
            TestUser._validate_order_by_parameter(long_param)

        # Acceptable length should work
        acceptable_param = "a" * 100
        # This should fail due to column format, not length
        with pytest.raises(SecurityValidationError, match="Invalid column name format"):
            TestUser._validate_order_by_parameter(acceptable_param)

    def test_validate_order_by_empty_and_none_parameters(self):
        """Test handling of empty and None parameters."""
        with pytest.raises(ValueError, match="must be a non-empty string"):
            TestUser._validate_order_by_parameter("")

        with pytest.raises(ValueError, match="must be a non-empty string"):
            TestUser._validate_order_by_parameter(None)

        with pytest.raises(ValueError, match="must be a non-empty string"):
            TestUser._validate_order_by_parameter("   ")

    def test_log_security_event_with_security_logger(self):
        """Test security event logging with proper logger."""
        with patch('reroute.db.models.security_logger') as mock_logger:
            TestUser._log_security_event(
                "TEST_EVENT",
                "Test security event",
                {"detail": "test"}
            )
            mock_logger.log_injection_attempt.assert_called_once_with(
                injection_type="SQL",
                payload="Test security event",
                context="TestUser: TEST_EVENT",
                detail="test"
            )

    def test_log_security_event_fallback_logging(self):
        """Test fallback logging when security logger is unavailable."""
        with patch('reroute.db.models.security_logger', side_effect=ImportError):
            with patch('reroute.db.models.logging.getLogger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger

                TestUser._log_security_event(
                    "TEST_EVENT",
                    "Test security event",
                    {"detail": "test"}
                )

                mock_logger.warning.assert_called_once_with(
                    "Security Event [TEST_EVENT]: Test security event"
                )

    def test_apply_secure_ordering_success(self):
        """Test successful application of secure ordering."""
        mock_query = Mock()

        # Test basic ordering
        result = TestUser._apply_secure_ordering(mock_query, "name")
        # Should call order_by with asc()
        mock_query.order_by.assert_called_once()

        # Test with direction
        mock_query.reset_mock()
        result = TestUser._apply_secure_ordering(mock_query, "email desc")
        mock_query.order_by.assert_called_once()

        # Test with None parameter
        mock_query.reset_mock()
        result = TestUser._apply_secure_ordering(mock_query, None)
        mock_query.order_by.assert_not_called()
        assert result == mock_query

    def test_apply_secure_ordering_sql_injection_protection(self):
        """Test that apply_secure_ordering blocks SQL injection."""
        mock_query = Mock()

        with pytest.raises(SecurityValidationError):
            TestUser._apply_secure_ordering(mock_query, "'; DROP TABLE users; --")

        with pytest.raises(SecurityValidationError):
            TestUser._apply_secure_ordering(mock_query, "name OR 1=1")

    def test_apply_secure_ordering_attribute_error_handling(self):
        """Test handling of SQLAlchemy attribute errors."""
        mock_query = Mock()

        # Mock a case where column doesn't exist (shouldn't happen due to whitelist)
        with patch.object(TestUser, '_validate_order_by_parameter', return_value=('fake_column', 'asc')):
            with pytest.raises(ValueError, match="not a valid orderable attribute"):
                TestUser._apply_secure_ordering(mock_query, "fake_column")

    def test_get_all_security_validation(self, session):
        """Test security validation in get_all method."""
        # Create test data
        TestUser.create(session, name="John", email="john@example.com", age=25)
        TestUser.create(session, name="Jane", email="jane@example.com", age=30)
        session.commit()

        # Test valid parameters
        users = TestUser.get_all(session, limit=10, offset=0, order_by="name asc")
        assert len(users) == 2

        # Test pagination validation
        with pytest.raises(ValueError, match="limit must be a positive integer"):
            TestUser.get_all(session, limit=0)

        with pytest.raises(ValueError, match="limit must be a positive integer"):
            TestUser.get_all(session, limit=-1)

        with pytest.raises(ValueError, match="limit must be a positive integer"):
            TestUser.get_all(session, limit=1001)

        with pytest.raises(ValueError, match="offset must be a non-negative integer"):
            TestUser.get_all(session, offset=-1)

        # Test SQL injection protection
        with pytest.raises(SecurityValidationError):
            TestUser.get_all(session, order_by="'; DROP TABLE test_users; --")

    def test_get_all_injection_attempts_logged(self, session):
        """Test that injection attempts are properly logged."""
        with patch.object(TestUser, '_log_security_event') as mock_log:
            with pytest.raises(SecurityValidationError):
                TestUser.get_all(session, order_by="name OR 1=1")

            # Verify security event was logged
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            assert args[0] == "SQL_INJECTION_ATTEMPT"
            assert "Malicious pattern detected" in args[1]

    def test_comprehensive_injection_pattern_detection(self):
        """Test comprehensive detection of various injection patterns."""
        # Test patterns that should be blocked
        blocked_patterns = [
            # SQL keywords
            "column DROP",
            "column DELETE",
            "column INSERT",
            "column UPDATE",
            "column UNION",
            "column SELECT",
            "column EXEC(",
            "column xp_",
            "column sp_",

            # Boolean-based injection
            "column or 1=1",
            "column and 1=1",
            "column 'or '1'='1",
            "column 'and '1'='1",

            # Time-based injection
            "column benchmark(",
            "column sleep(",
            "column pg_sleep(",
            "column waitfor delay",

            # System function calls
            "column convert(",
            "column cast(",
            "column char(",
            "column ascii(",
            "column concat(",
            "column substring(",
            "column len(",
            "column length(",

            # System table access
            "column information_schema",
            "column mysql.sys",
            "column pg_catalog",
            "column sys.objects",
            "column load_file",
            "column into outfile",
            "column into dumpfile",
        ]

        for pattern in blocked_patterns:
            with pytest.raises(SecurityValidationError,
                              match=f"SQL injection attempt detected"):
                TestUser._validate_order_by_parameter(pattern)


class TestSecurityIntegration:
    """Integration tests for security features."""

    @pytest.fixture
    def session(self):
        """Create test database session."""
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        return Session()

    def test_end_to_end_security_protection(self, session):
        """Test end-to-end security protection in real usage."""
        # Create test data
        users = [
            TestUser.create(session, name="Alice", email="alice@example.com", age=28),
            TestUser.create(session, name="Bob", email="bob@example.com", age=32),
            TestUser.create(session, name="Charlie", email="charlie@example.com", age=25),
        ]
        session.commit()

        # Test legitimate ordering works
        results = TestUser.get_all(session, order_by="name asc")
        assert [u.name for u in results] == ["Alice", "Bob", "Charlie"]

        results = TestUser.get_all(session, order_by="age desc")
        assert [u.name for u in results] == ["Bob", "Alice", "Charlie"]

        # Test malicious attempts are blocked
        injection_attempts = [
            "name; DROP TABLE test_users; --",
            "name' OR '1'='1",
            "age UNION SELECT password FROM users",
            "name; SELECT pg_sleep(5); --"
        ]

        for injection in injection_attempts:
            with pytest.raises((SecurityValidationError, ValueError)):
                TestUser.get_all(session, order_by=injection)

        # Verify data integrity after all attempts
        remaining_users = TestUser.get_all(session)
        assert len(remaining_users) == 3
        assert all(u.email for u in remaining_users)

    def test_security_event_monitoring_integration(self, session):
        """Test integration with security event monitoring."""
        with patch('reroute.db.models.security_logger') as mock_logger:
            # Try multiple injection attempts
            injection_attempts = [
                "name OR 1=1",
                "'; DROP TABLE users; --",
                "invalid_column"
            ]

            for injection in injection_attempts:
                try:
                    TestUser.get_all(session, order_by=injection)
                except (SecurityValidationError, ValueError):
                    pass  # Expected

            # Verify security events were logged
            assert mock_logger.log_injection_attempt.call_count >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])