"""
Route Loader Module

Handles secure dynamic loading of route modules from the app/routes directory.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any, Optional


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

            # Create module spec
            spec = importlib.util.spec_from_file_location(
                module_path.stem,
                module_path
            )

            if spec is None or spec.loader is None:
                return None

            # Load the module
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_path.stem] = module
            spec.loader.exec_module(module)

            return module

        except Exception as e:
            print(f"Error loading module {module_path}: {e}")
            return None

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
            # Resolve to absolute path and check it's within routes_dir
            resolved_path = path.resolve()
            resolved_routes_dir = self.routes_dir.resolve()

            return resolved_routes_dir in resolved_path.parents or resolved_path == resolved_routes_dir
        except Exception:
            return False
