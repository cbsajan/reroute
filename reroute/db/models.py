"""
Base Model Class for REROUTE

Provides Django-style base model with common fields and CRUD methods.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, DateTime, inspect

Base = declarative_base()


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
        Get all records with pagination

        Args:
            session: SQLAlchemy session
            limit: Maximum number of records
            offset: Number of records to skip
            order_by: Column name to order by (must be a valid column)

        Returns:
            List of model instances

        Raises:
            ValueError: If order_by is not a valid column name

        Example:
            users = User.get_all(session, limit=10, offset=0)
            users = User.get_all(session, order_by='created_at')
        """
        query = session.query(cls)

        if order_by:
            # Security: Validate that order_by is an actual column attribute
            # This prevents SQL injection via arbitrary attribute access
            valid_columns = {col.key for col in inspect(cls).mapper.column_attrs}

            if order_by not in valid_columns:
                # Security logging: Log potential SQL injection attempt
                try:
                    from reroute.logging import security_logger
                    security_logger.log_injection_attempt(
                        injection_type="SQL",
                        payload=order_by,
                        context=f"Invalid order_by in {cls.__name__}.get_all()"
                    )
                except ImportError:
                    pass

                raise ValueError(
                    f"Invalid order_by column: '{order_by}'. "
                    f"Valid columns are: {', '.join(sorted(valid_columns))}"
                )

            query = query.order_by(getattr(cls, order_by))

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
