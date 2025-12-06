from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import your models here
from reroute.db.models import Base
# from app.models import *  # Import all your models

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata
target_metadata = Base.metadata

# Get database URL from environment
# SECURITY: Database URL must be explicitly configured
database_url = os.getenv('REROUTE_DATABASE_URL')
if not database_url:
    raise RuntimeError(
        "REROUTE_DATABASE_URL environment variable is required\n"
        "Please set it in your .env file or environment:\n"
        "  For PostgreSQL: postgresql://user:pass@localhost:5432/dbname\n"
        "  For MySQL: mysql+pymysql://user:pass@localhost:3306/dbname\n"
        "  For SQLite: sqlite:///./app.db"
    )
config.set_main_option('sqlalchemy.url', database_url)


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    raise RuntimeError("Offline mode not supported")
else:
    run_migrations_online()
