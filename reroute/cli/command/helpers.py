"""
Shared helper functions for CLI commands
"""

import re
from pathlib import Path


def validate_project_name(text: str) -> bool | str:
    """
    Validate project name

    Args:
        text: Project name to validate

    Returns:
        True if valid, error message string if invalid
    """
    if not text:
        return "Project name cannot be empty"

    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', text):
        return "Project name must start with a letter and contain only letters, numbers, hyphens, and underscores"

    if len(text) > 50:
        return "Project name must be 50 characters or less"

    reserved_names = ['test', 'tests', 'src', 'lib', 'bin', 'config']
    if text.lower() in reserved_names:
        return f"'{text}' is a reserved name, please choose another"

    return True


def validate_model_name(text: str) -> bool | str:
    """
    Validate model name (PascalCase)

    Args:
        text: Model name to validate

    Returns:
        True if valid, error message string if invalid
    """
    if not text:
        return "Model name cannot be empty"

    if not re.match(r'^[A-Z][a-zA-Z0-9]*$', text):
        return "Model name must be in PascalCase (e.g., User, ProductCategory)"

    if len(text) > 50:
        return "Model name must be 50 characters or less"

    return True


def get_database_defaults(db_type: str) -> dict:
    """
    Get default configuration for database type

    Args:
        db_type: Database type (postgresql, mysql, mongodb, sqlite)

    Returns:
        Dictionary with default port and URL template
    """
    defaults = {
        'postgresql': {
            'port': 5432,
            'url_template': 'postgresql://user:password@localhost:5432/{db_name}',
            'driver': 'psycopg2-binary'
        },
        'mysql': {
            'port': 3306,
            'url_template': 'mysql+pymysql://user:password@localhost:3306/{db_name}',
            'driver': 'pymysql'
        },
        'mongodb': {
            'port': 27017,
            'url_template': 'mongodb://user:password@localhost:27017/{db_name}',
            'driver': 'pymongo'
        },
        'sqlite': {
            'port': None,
            'url_template': 'sqlite:///./{db_name}.db',
            'driver': None  # Built into Python
        }
    }

    return defaults.get(db_type, defaults['sqlite'])


def create_directory_structure(base_path: Path, *paths):
    """
    Create directory structure

    Args:
        base_path: Base directory path
        *paths: Additional paths to create under base_path
    """
    base_path.mkdir(parents=True, exist_ok=True)

    for path in paths:
        (base_path / path).mkdir(parents=True, exist_ok=True)
