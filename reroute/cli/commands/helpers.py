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
        UserProfile -> UserProfileRoutes (preserves existing PascalCase)
    """
    import re

    # Strip leading underscores first (they're not valid for class names)
    name = name.lstrip('_')

    if not name:
        raise ValueError("Name cannot be empty or consist only of underscores")

    # Check if name contains separators (underscore, dash, space)
    has_separators = bool(re.search(r'[_\-\s]', name))

    if has_separators:
        # Split by separators and convert to PascalCase
        words = name.replace('_', ' ').replace('-', ' ').split()
        class_name = ''.join(word.capitalize() for word in words)
    else:
        # No separators - preserve the original casing (already PascalCase or single word)
        # Just capitalize first letter if it's lowercase
        if name and name[0].islower():
            class_name = name[0].upper() + name[1:]
        else:
            class_name = name

    # Remove any non-alphanumeric characters (except underscore)
    class_name = re.sub(r'[^\w]', '', class_name)

    # Ensure it starts with a letter (not number or underscore)
    # Class names should always start with a letter
    if not class_name or not class_name[0].isalpha():
        raise ValueError(f"'{name}' cannot be converted to a valid class name (class names must start with a letter)")

    # Add 'Routes' suffix if not present
    if not class_name.endswith('Routes'):
        class_name += 'Routes'

    # Validate it's a valid Python identifier
    if not class_name.isidentifier():
        raise ValueError(f"'{class_name}' is not a valid Python class name")

    return class_name


def auto_name_from_path(path: str) -> str:
    """
    Auto-generate a route name from a path.

    Examples:
        /user -> User
        /user/profile -> UserProfile
        /api/v1/posts -> ApiV1Posts
        /blog-posts -> BlogPosts

    Args:
        path: Route path (e.g., /user/profile)

    Returns:
        Generated name in PascalCase (e.g., UserProfile)

    Raises:
        ValueError: If path is empty or contains no valid segments
    """
    import re

    # Validate path is not empty
    if not path or not path.strip():
        raise ValueError("Path cannot be empty")

    # Remove leading/trailing slashes and split by /
    parts = path.strip('/').split('/')

    # If after stripping we have nothing, it was just "/"
    if not parts or (len(parts) == 1 and not parts[0]):
        raise ValueError("Path must contain at least one segment (e.g., /user, /api/posts)")

    # Clean each part: remove special chars, convert to title case
    cleaned_parts = []
    for part in parts:
        # Replace hyphens and underscores with spaces, then capitalize
        words = part.replace('-', ' ').replace('_', ' ').split()
        cleaned_part = ''.join(word.capitalize() for word in words)
        if cleaned_part:  # Skip empty parts
            cleaned_parts.append(cleaned_part)

    # If no valid parts after cleaning
    if not cleaned_parts:
        raise ValueError("Path must contain valid alphanumeric segments")

    # Join all parts
    name = ''.join(cleaned_parts)

    # Remove any non-alphanumeric characters (except underscore)
    name = re.sub(r'[^\w]', '', name)

    # Ensure it starts with a letter (class names should not start with numbers/underscores)
    # If it starts with a number, prepend 'Route' to make it valid
    if name and not name[0].isalpha():
        name = 'Route' + name

    # Final validation
    if not name or not name[0].isalpha():
        raise ValueError("Could not generate a valid class name from path")

    return name


def check_class_name_duplicate(class_name: str, route_dir: Path) -> bool:
    """
    Check if a class name already exists in the route file.

    Args:
        class_name: Class name to check (e.g., "UserProfileRoutes")
        route_dir: Directory where page.py will be created

    Returns:
        True if duplicate found, False otherwise
    """
    page_file = route_dir / "page.py"

    if not page_file.exists():
        return False

    try:
        content = page_file.read_text()
        # Check if class name exists in file
        return f"class {class_name}" in content
    except Exception:
        return False


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


def validate_path_realtime(text: str) -> bool:
    """
    Real-time validation for path input (for InquirerPy).
    Returns True if valid, False if invalid.

    Args:
        text: Path text to validate

    Returns:
        True if valid, False if invalid
    """
    if not text or not text.strip():
        return False
    if not text.startswith('/'):
        return False
    if len(text) > 1 and text.endswith('/'):
        return False
    if '//' in text:
        return False
    return True


def validate_route_path(ctx, param, value):
    """
    Validate route path for Click commands.
    Only validates when a value is provided (not None).

    Args:
        ctx: Click context
        param: Click parameter
        value: Path value to validate

    Returns:
        The validated path

    Raises:
        click.BadParameter: If path is invalid
    """
    import click

    # If no value provided, return None (will be prompted later with InquirerPy)
    if value is None:
        return None

    if not value.strip():
        raise click.BadParameter("Path cannot be empty")

    # Must start with /
    if not value.startswith('/'):
        raise click.BadParameter("Path must start with / (e.g., /user, /api/posts)")

    # Must not end with / (unless it's just "/")
    if len(value) > 1 and value.endswith('/'):
        raise click.BadParameter("Path must not end with / (e.g., use /user not /user/)")

    # Remove leading/trailing slashes for validation
    clean_path = value.strip('/')

    # Check if path has at least one segment
    if not clean_path:
        raise click.BadParameter("Path must contain at least one segment (e.g., /user, /api/posts)")

    # Check for double slashes
    if '//' in value:
        raise click.BadParameter("Path cannot contain consecutive slashes")

    # Check for path traversal attempts
    if '/..' in value or '/./' in value:
        raise click.BadParameter("Path cannot contain relative path segments (. or ..)")

    # Check for reserved Python names in path segments
    path_segments = clean_path.split('/')
    reserved_python = ['__init__', '__pycache__', '__main__', '__file__']
    for segment in path_segments:
        if segment in reserved_python:
            raise click.BadParameter(f"Path cannot contain reserved Python name: {segment}")

    # Check for invalid filesystem characters (Windows compatibility)
    invalid_chars = '<>:"|?*'
    for char in invalid_chars:
        if char in value:
            raise click.BadParameter(f"Path cannot contain invalid character: {char}")

    # Check path length (Windows MAX_PATH is typically 260 chars)
    # Leave room for project path + app/routes/ + page.py
    if len(value) > 100:
        raise click.BadParameter("Path is too long (maximum 100 characters)")

    # Try to generate a name from it to see if it's valid
    try:
        from .helpers import auto_name_from_path
        auto_name_from_path(value)
    except ValueError as e:
        raise click.BadParameter(str(e))

    return value
