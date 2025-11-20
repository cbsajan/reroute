"""
REROUTE CLI - Shared Helper Functions

Utility functions used across CLI commands.
"""

from pathlib import Path
import os


def is_reroute_project() -> bool:
    """Check if current directory is a REROUTE project."""
    app_dir = Path.cwd() / "app" / "routes"
    return app_dir.exists() and app_dir.is_dir()


def create_route_directory(path: str) -> Path:
    """
    Create route directory from path.

    Examples:
        /users -> app/routes/users/
        /api/posts -> app/routes/api/posts/
    """
    # Clean path
    clean_path = path.strip('/').replace('/', os.sep)

    # Create directory
    route_dir = Path.cwd() / "app" / "routes" / clean_path
    route_dir.mkdir(parents=True, exist_ok=True)

    return route_dir


def to_class_name(name: str) -> str:
    """
    Convert name to PascalCase class name.

    Examples:
        users -> UsersRoutes
        user -> UserRoutes
        blog_posts -> BlogPostsRoutes
    """
    # Remove special characters and split
    words = name.replace('_', ' ').replace('-', ' ').split()

    # Convert to PascalCase
    class_name = ''.join(word.capitalize() for word in words)

    # Add 'Routes' suffix if not present
    if not class_name.endswith('Routes'):
        class_name += 'Routes'

    return class_name


def validate_project_name(name: str):
    """
    Validate project name for filesystem compatibility.

    Args:
        name: Project name to validate

    Returns:
        True if valid, error message string if invalid
    """
    import re

    if not name or not name.strip():
        return "Project name cannot be empty"

    # Check minimum length
    if len(name) < 1:
        return "Project name must be at least 1 character"

    # Check for valid characters (alphanumeric, dash, underscore only)
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        return "Project name can only contain letters, numbers, dashes, and underscores"

    # Check it doesn't start with dash or underscore
    if name[0] in '-_':
        return "Project name cannot start with a dash or underscore"

    # Reserved names
    reserved = ['con', 'prn', 'aux', 'nul', 'com1', 'com2', 'com3', 'com4',
                'lpt1', 'lpt2', 'lpt3', 'test', 'tests']
    if name.lower() in reserved:
        return f"'{name}' is a reserved name, please choose another"

    # Check if directory already exists
    project_dir = Path.cwd() / name
    if project_dir.exists():
        return f"Directory '{name}' already exists"

    return True
