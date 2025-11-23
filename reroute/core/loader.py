"""
Route Loader Module

Handles secure dynamic loading of route modules from the app/routes directory.
"""

import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class RouteLoader:
    """
    Securely loads route modules from the filesystem.

    In the minimal version, this provides basic module loading.
    Security features like sandboxing will be added in the full version.
    """

    def __init__(self, routes_dir: Path):
        """
        Initialize the RouteLoader.

        Args:
            routes_dir: Path to the routes directory (e.g., app/routes)
        """
        self.routes_dir = Path(routes_dir)
        if not self.routes_dir.exists():
            raise ValueError(f"Routes directory does not exist: {routes_dir}")

    def load_module(self, module_path: Path) -> Optional[Any]:
        """
        Load a Python module from a file path.

        Args:
            module_path: Path to the .py file to load

        Returns:
            The loaded module object, or None if loading fails
        """
        try:
            # Validate path is within routes directory
            if not self._is_safe_path(module_path):
                raise ValueError(f"Path traversal detected: {module_path}")

            # Create unique module name based on full path to avoid collisions
            # e.g., "app/routes/users/page.py" becomes "routes.users.page"
            relative_path = module_path.relative_to(self.routes_dir.parent)
            module_name = str(relative_path).replace('\\', '.').replace('/', '.')[:-3]  # Remove .py extension

            # Create module spec with unique name
            spec = importlib.util.spec_from_file_location(
                module_name,
                module_path
            )

            if spec is None or spec.loader is None:
                return None

            # Load the module with unique name
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            return module

        except (ImportError, AttributeError, SyntaxError, ValueError) as e:
            # Catch specific module loading errors
            logger.warning(f"Failed to load route module {module_path}: {e}")
            return None
        except Exception as e:
            # Unexpected error - log and re-raise for visibility
            logger.error(f"Unexpected error loading module {module_path}: {e}", exc_info=True)
            raise

    def _is_safe_path(self, path: Path) -> bool:
        """
        Validate that a path is within the routes directory.
        Prevents directory traversal attacks.

        Args:
            path: Path to validate

        Returns:
            True if path is safe, False otherwise
        """
        try:
            # Resolve both paths to absolute (strict=True raises if path doesn't exist)
            resolved_path = path.resolve(strict=True)
            resolved_routes_dir = self.routes_dir.resolve(strict=True)

            # Check for symlinks in the path
            if resolved_path.is_symlink() or any(p.is_symlink() for p in resolved_path.parents):
                return False

            # Ensure path is within routes_dir using relative_to
            # This will raise ValueError if path is not within routes_dir
            try:
                resolved_path.relative_to(resolved_routes_dir)
                return True
            except ValueError:
                return False

        except (OSError, ValueError, RuntimeError):
            # Catch specific exceptions: file not found, permission denied, etc.
            return False
