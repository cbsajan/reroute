"""
Database Connection Manager for REROUTE

Provides singleton database connection with connection pooling.
"""

from typing import Optional
from contextlib import contextmanager
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker, Session


class DatabaseManager:
    """
    Manages database connections with connection pooling

    Usage:
        from reroute.db import db

        # Setup (usually in main.py)
        db.setup('postgresql://user:pass@localhost/mydb')

        # Use in routes
        with db.session() as session:
            users = session.query(User).all()
    """

    _instance = None
    _engine = None
    _session_factory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def setup(
        self,
        database_url: str,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        echo: bool = False
    ):
        """
        Initialize database connection

        Args:
            database_url: SQLAlchemy database URL
            pool_size: Number of connections to keep in pool
            max_overflow: Max connections to create beyond pool_size
            pool_timeout: Timeout in seconds for getting connection
            echo: Log all SQL queries

        Example:
            db.setup('postgresql://user:pass@localhost/mydb')
            db.setup('sqlite:///./app.db', echo=True)
        """
        self._engine = create_engine(
            database_url,
            poolclass=pool.QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            echo=echo
        )
        self._session_factory = sessionmaker(bind=self._engine)

    @contextmanager
    def session(self) -> Session:
        """
        Context manager for database sessions with automatic commit/rollback

        Usage:
            with db.session() as session:
                user = session.query(User).first()
                # Auto-commits on success, rolls back on exception
        """
        if self._session_factory is None:
            raise RuntimeError(
                "Database not initialized. Call db.setup(database_url) first."
            )

        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_session(self) -> Session:
        """
        Get a new session (manual management required)

        Returns:
            SQLAlchemy Session object

        Note:
            You must manually commit/rollback and close this session.
            Prefer using the session() context manager instead.
        """
        if self._session_factory is None:
            raise RuntimeError(
                "Database not initialized. Call db.setup(database_url) first."
            )
        return self._session_factory()

    @property
    def engine(self):
        """Get the SQLAlchemy engine"""
        return self._engine


# Global instance
db = DatabaseManager()
