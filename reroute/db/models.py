"""
Base Model Class for REROUTE

Provides Django-style base model with common fields and CRUD methods.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, DateTime, inspect, asc, desc
from sqlalchemy.exc import InvalidRequestError
import re
import logging

Base = declarative_base()


class SecurityValidationError(Exception):
    """Raised when a security validation fails."""
    pass


class Model(Base):
    """
    Base model class with common fields and CRUD methods

    All models should inherit from this class to get:
    - id, created_at, updated_at fields
    - CRUD methods (create, get_by_id, update, delete)
    - to_dict() for JSON serialization

    Example:
        from reroute.db.models import Model
        from sqlalchemy import Column, String

        class User(Model):
            __tablename__ = 'users'

            name = Column(String(100), nullable=False)
            email = Column(String(100), unique=True)
    """

    __abstract__ = True

    # Common fields for all models
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    @classmethod
    def _get_allowed_columns(cls) -> Set[str]:
        """
        Get a set of allowed column names for this model.

        Returns:
            Set of valid column names that can be used for ordering

        Security Note:
            This method creates a whitelist of valid column names to prevent
            SQL injection attacks via malicious order_by parameters.
        """
        try:
            # Get all column attributes from the model
            mapper = inspect(cls).mapper
            return {col.key for col in mapper.column_attrs}
        except Exception as e:
            # If we can't get columns, return empty set for safety
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to get columns for model {cls.__name__}: {e}")
            return set()

    @classmethod
    def _validate_order_by_parameter(cls, order_by: str) -> tuple[str, str]:
        """
        Validate and parse order_by parameter safely.

        Args:
            order_by: Order by parameter (e.g., "name", "created_at desc", "name asc")

        Returns:
            Tuple of (column_name, direction) where direction is "asc" or "desc"

        Raises:
            SecurityValidationError: If parameter contains malicious content
            ValueError: If parameter format is invalid

        Security Note:
            This method implements defense-in-depth with multiple validation layers:
            1. Pattern matching to detect SQL injection attempts
            2. Whitelist validation against actual model columns
            3. Direction validation (only 'asc' or 'desc' allowed)
            4. Length limits to prevent buffer overflow attacks
            5. Comprehensive security logging
        """
        if not order_by or not isinstance(order_by, str):
            raise ValueError("order_by parameter must be a non-empty string")

        # Length limit to prevent buffer overflow
        if len(order_by) > 100:
            raise SecurityValidationError("order_by parameter exceeds maximum length")

        # Store original for logging purposes
        original_order_by = order_by.strip()

        # Check for whitespace-only strings
        if not original_order_by:
            raise ValueError("order_by parameter must be a non-empty string")

        # Normalize the input for validation (but keep original for validation)
        normalized = original_order_by.lower()

        # Security: Check for common SQL injection patterns
        dangerous_patterns = [
            r';', r'--', r'/\*', r'\*/', r'drop\s+', r'delete\s+',
            r'insert\s+', r'update\s+', r'union\s+', r'select\s+',
            r'exec\s*\(', r'xp_', r'sp_', r'1\s*=\s*1', r'or\s+1\s*=\s*1',
            r'and\s+1\s*=\s*1', r'\'\s*or\s*', r'\'\s*and\s*', r'<script',
            r'javascript:', r'eval\s*\(', r'benchmark\s*\(', r'sleep\s*\(',
            r'pg_sleep\s*\(', r'waitfor\s+delay', r'convert\s*\(',
            r'cast\s*\(', r'char\s*\(', r'ascii\s*\(', r'concat\s*\(',
            r'substring\s*\(', r'len\s*\(', r'length\s*\(', r'load_file',
            r'into\s+outfile', r'into\s+dumpfile', r'information_schema',
            r'mysql\.sys', r'pg_catalog', r'sys\.objects', r'sys\.columns',
            # Additional patterns for string-based injections
            r'\'\s*=\s*\'', r'or\s*\'\s*=\s*\'', r'and\s*\'\s*=\s*\'',
            r'or\s*\'x\'\s*=\s*\'x', r'or\s*\'1\'\s*=\s*\'1'
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, normalized, re.IGNORECASE):
                # Log injection attempt
                cls._log_security_event(
                    "SQL_INJECTION_ATTEMPT",
                    f"Malicious pattern detected in order_by: {pattern}",
                    {"order_by": original_order_by, "pattern": pattern}
                )
                raise SecurityValidationError(f"Invalid characters or SQL injection attempt detected in order_by parameter")

        # First, check if the entire string contains spaces which indicates invalid format
        # Column names themselves should not contain spaces
        if ' ' in original_order_by:
            # If it contains spaces, check if it follows the "column direction" pattern
            parts = original_order_by.split()
            if len(parts) == 2:
                # Check if direction is valid
                if parts[1].lower() in ('asc', 'desc'):
                    # This is valid: "column asc" or "column desc"
                    column = parts[0].strip()
                    direction_input = parts[1].strip().lower()
                else:
                    # Invalid direction
                    raise ValueError("Direction must be 'asc' or 'desc'")
            else:
                # Too many parts - invalid format
                raise ValueError("order_by format should be 'column' or 'column direction'")
        else:
            # No spaces, treat entire string as column name
            column = original_order_by
            direction_input = "asc"

        # Validate column name format (before checking against whitelist)
        if not column:
            raise SecurityValidationError("Invalid column name format")

        # Check if column has invalid characters
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', column):
            raise SecurityValidationError("Invalid column name format")

        # Validate direction
        if direction_input not in ('asc', 'desc'):
            raise ValueError("Direction must be 'asc' or 'desc'")

        # Whitelist validation: Check if column exists in model
        allowed_columns = cls._get_allowed_columns()
        if column.lower() not in allowed_columns:
            cls._log_security_event(
                "INVALID_COLUMN_ACCESS",
                f"Attempted to order by non-existent column: {column}",
                {"order_by": original_order_by, "requested_column": column, "allowed_columns": list(allowed_columns)}
            )
            raise ValueError(
                f"Invalid order_by column: '{column}'. "
                f"Valid columns are: {', '.join(sorted(allowed_columns))}"
            )

        return column.lower(), direction_input

    @classmethod
    def _log_security_event(cls, event_type: str, message: str, details: dict = None):
        """
        Log security events for monitoring and incident response.

        Args:
            event_type: Type of security event
            message: Security event message
            details: Additional event details
        """
        try:
            from reroute.logging import security_logger
            security_logger.log_injection_attempt(
                injection_type="SQL",
                payload=message,
                context=f"{cls.__name__}: {event_type}",
                **(details or {})
            )
        except ImportError:
            # Fallback to standard logging if security logger not available
            logger = logging.getLogger(__name__)
            logger.warning(f"Security Event [{event_type}]: {message}")

    @classmethod
    def _apply_secure_ordering(cls, query, order_by: str):
        """
        Apply secure ordering to a SQLAlchemy query.

        Args:
            query: SQLAlchemy query object
            order_by: Order by parameter (e.g., "name", "created_at desc")

        Returns:
            Query with secure ordering applied

        Raises:
            SecurityValidationError: If parameter is malicious
            ValueError: If parameter format is invalid

        Security Note:
            This method uses SQLAlchemy's built-in secure ordering functions
            (asc() and desc()) instead of raw string concatenation to prevent
            SQL injection attacks.
        """
        if not order_by:
            return query

        # Validate and parse the order_by parameter
        column, direction = cls._validate_order_by_parameter(order_by)

        try:
            # Get the column attribute safely
            column_attr = getattr(cls, column)

            # Apply secure ordering using SQLAlchemy's asc() and desc() functions
            if direction == "desc":
                query = query.order_by(desc(column_attr))
            else:  # asc
                query = query.order_by(asc(column_attr))

        except InvalidRequestError as e:
            # This could happen if the column is not orderable
            cls._log_security_event(
                "INVALID_ORDERING",
                f"Failed to apply ordering on column: {column}",
                {"order_by": order_by, "error": str(e)}
            )
            raise ValueError(f"Cannot order by column '{column}': {str(e)}")
        except AttributeError:
            # This shouldn't happen due to our whitelist validation, but let's be safe
            cls._log_security_event(
                "ATTRIBUTE_ERROR",
                f"Column attribute not found: {column}",
                {"order_by": order_by}
            )
            raise ValueError(f"Column '{column}' is not a valid orderable attribute")

        return query

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model instance to dictionary

        Returns:
            Dictionary with all column values

        Example:
            user = User.get_by_id(session, 1)
            return user.to_dict()  # {'id': 1, 'name': 'John', ...}
        """
        return {
            c.key: getattr(self, c.key)
            for c in inspect(self).mapper.column_attrs
        }

    @classmethod
    def create(cls, session, **kwargs):
        """
        Create a new record

        Args:
            session: SQLAlchemy session
            **kwargs: Field values

        Returns:
            Created instance

        Example:
            user = User.create(session, name="John", email="john@example.com")
        """
        instance = cls(**kwargs)
        session.add(instance)
        session.flush()
        return instance

    @classmethod
    def get_by_id(cls, session, id: int):
        """
        Get record by ID

        Args:
            session: SQLAlchemy session
            id: Record ID

        Returns:
            Model instance or None

        Example:
            user = User.get_by_id(session, 1)
        """
        return session.query(cls).filter_by(id=id).first()

    @classmethod
    def get_all(
        cls,
        session,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[str] = None
    ) -> List:
        """
        Get all records with pagination (SECURE VERSION)

        Args:
            session: SQLAlchemy session
            limit: Maximum number of records (must be positive, max 1000)
            offset: Number of records to skip (must be non-negative)
            order_by: Column name to order by with optional direction
                     (e.g., "name", "created_at desc", "name asc")

        Returns:
            List of model instances

        Raises:
            ValueError: If order_by is invalid, or limit/offset are out of range
            SecurityValidationError: If malicious SQL injection attempt detected

        Example:
            users = User.get_all(session, limit=10, offset=0)
            users = User.get_all(session, order_by='created_at desc')
            users = User.get_all(session, order_by='name asc')
        """
        # Validate pagination parameters for security
        if not isinstance(limit, int) or limit <= 0 or limit > 1000:
            raise ValueError("limit must be a positive integer not exceeding 1000")
        if not isinstance(offset, int) or offset < 0:
            raise ValueError("offset must be a non-negative integer")

        query = session.query(cls)

        # Apply secure ordering if specified
        if order_by:
            query = cls._apply_secure_ordering(query, order_by)

        return query.limit(limit).offset(offset).all()

    def update(self, session, **kwargs):
        """
        Update record

        Args:
            session: SQLAlchemy session
            **kwargs: Fields to update

        Returns:
            Updated instance

        Example:
            user.update(session, name="Jane", email="jane@example.com")
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        session.flush()
        return self

    def delete(self, session):
        """
        Delete record

        Args:
            session: SQLAlchemy session

        Example:
            user.delete(session)
        """
        session.delete(self)
        session.flush()

    @classmethod
    def count(cls, session) -> int:
        """
        Count total records

        Args:
            session: SQLAlchemy session

        Returns:
            Number of records

        Example:
            total_users = User.count(session)
        """
        return session.query(cls).count()

    @classmethod
    def exists(cls, session, **filters) -> bool:
        """
        Check if record exists

        Args:
            session: SQLAlchemy session
            **filters: Filter conditions

        Returns:
            True if exists, False otherwise

        Example:
            if User.exists(session, email="john@example.com"):
                print("Email already taken")
        """
        return session.query(cls).filter_by(**filters).first() is not None

    def __repr__(self):
        """String representation"""
        return f"<{self.__class__.__name__}(id={self.id})>"
