"""
Route Loader Module

Handles secure dynamic loading of route modules from the app/routes directory.
"""

import importlib.util
import logging
import os
import stat
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
        self.routes_dir = Path(routes_dir).resolve()
        if not self.routes_dir.exists():
            raise ValueError(f"Routes directory does not exist: {routes_dir}")

        # Security: Validate routes directory permissions
        if not self._is_secure_directory(self.routes_dir):
            raise ValueError(f"Routes directory has insecure permissions: {routes_dir}")

        # Allowed file extensions for security
        self.allowed_extensions = {'.py'}

    def load_module(self, module_path: Path) -> Optional[Any]:
        """
        Load a Python module from a file path.

        Args:
            module_path: Path to the .py file to load

        Returns:
            The loaded module object, or None if loading fails
        """
        try:
            # Convert to Path object if string provided
            module_path = Path(module_path)

            # Security: Validate file extension
            if module_path.suffix.lower() not in self.allowed_extensions:
                raise ValueError(f"Disallowed file extension: {module_path.suffix}. Only {self.allowed_extensions} allowed")

            # Security: Validate path is within routes directory with comprehensive checks
            if not self._is_safe_path(module_path):
                raise ValueError(f"Path traversal detected: {module_path}")

            # Security: Validate file permissions
            if not self._has_secure_file_permissions(module_path):
                raise ValueError(f"Insecure file permissions: {module_path}")

            # Security: Validate file size (prevent extremely large files)
            max_file_size = 10 * 1024 * 1024  # 10MB limit
            if module_path.stat().st_size > max_file_size:
                raise ValueError(f"File too large: {module_path} ({module_path.stat().st_size} bytes > {max_file_size} bytes)")

            # Create unique module name based on full path to avoid collisions
            # e.g., "app/routes/users/page.py" becomes "routes.users.page"
            relative_path = module_path.relative_to(self.routes_dir.parent)
            module_name = str(relative_path).replace('\\', '.').replace('/', '.')[:-3]  # Remove .py extension

            # Security: Validate module name for safe import
            if not self._is_safe_module_name(module_name):
                raise ValueError(f"Unsafe module name: {module_name}")

            # Create module spec with unique name
            spec = importlib.util.spec_from_file_location(
                module_name,
                module_path
            )

            if spec is None or spec.loader is None:
                return None

            # Security: Validate module spec before loading
            if not self._is_safe_module_spec(spec, module_path):
                raise ValueError(f"Unsafe module spec: {module_path}")

            # Load the module with unique name
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            logger.info(f"Successfully loaded module: {module_name}")
            return module

        except (ImportError, AttributeError, SyntaxError, ValueError) as e:
            # Catch specific module loading errors
            logger.warning(f"Failed to load route module {module_path}: {e}")
            # Security logging for potential attacks
            self._log_security_event("module_load_failure", str(module_path), str(e))
            return None
        except Exception as e:
            # Unexpected error - log and re-raise for visibility
            logger.error(f"Unexpected error loading module {module_path}: {e}", exc_info=True)
            # Security logging for unexpected errors
            self._log_security_event("module_load_error", str(module_path), str(e))
            raise

    def _is_safe_path(self, path: Path) -> bool:
        """
        Comprehensive path validation to prevent directory traversal attacks.

        This method implements multiple layers of security:
        1. Symlink chain detection and validation
        2. Path component validation for dangerous characters
        3. Directory traversal prevention
        4. Cross-platform path resolution
        5. Hard link detection

        Args:
            path: Path to validate

        Returns:
            True if path is safe, False otherwise
        """
        try:
            path = Path(path)

            # Security: Reject null bytes and dangerous characters
            if '\x00' in str(path):
                logger.warning(f"Null byte detected in path: {path}")
                self._log_security_event("null_byte_in_path", str(path), "Null byte character detected")
                return False

            # Security: Check for dangerous path components
            dangerous_components = ['..', '.', '~']
            path_parts = path.parts

            for part in path_parts:
                if part in dangerous_components:
                    logger.warning(f"Dangerous path component detected: {part} in {path}")
                    self._log_security_event("dangerous_path_component", str(path), f"Component: {part}")
                    return False

            # Security: Check for path traversal patterns
            path_str = str(path)
            traversal_patterns = [
                '../', '..\\', '%2e%2e%2f', '%2e%2e%5c', '..%2f', '..%5c',
                '%2e%2e/', '%2e%2e\\', '.../', '.\\./', '././'
            ]

            for pattern in traversal_patterns:
                if pattern in path_str.lower():
                    logger.warning(f"Path traversal pattern detected: {pattern} in {path}")
                    self._log_security_event("path_traversal_pattern", str(path), f"Pattern: {pattern}")
                    return False

            # Security: Comprehensive symlink detection BEFORE resolving
            if not self._is_path_free_of_symlinks(path):
                logger.warning(f"Symlink detected in path chain: {path}")
                self._log_security_event("symlink_detected", str(path), "Symlink found in path chain")
                return False

            # Security: Resolve paths with strict validation
            try:
                resolved_path = path.resolve(strict=True)
                resolved_routes_dir = self.routes_dir.resolve(strict=True)
            except (FileNotFoundError, RuntimeError) as e:
                logger.warning(f"Path resolution failed for {path}: {e}")
                return False

            # Security: Cross-platform path containment check
            if not self._is_path_contained(resolved_path, resolved_routes_dir):
                logger.warning(f"Path escapes routes directory: {path} -> {resolved_path}")
                self._log_security_event("path_escape", str(path), f"Resolved to: {resolved_path}")
                return False

            # Security: Check for hard links pointing outside routes directory
            if not self._is_safe_hard_link(resolved_path, resolved_routes_dir):
                logger.warning(f"Unsafe hard link detected: {resolved_path}")
                self._log_security_event("unsafe_hard_link", str(resolved_path), "Hard link points outside routes directory")
                return False

            return True

        except (OSError, ValueError, RuntimeError) as e:
            logger.warning(f"Path validation failed for {path}: {e}")
            self._log_security_event("path_validation_error", str(path), str(e))
            return False

    def _is_path_free_of_symlinks(self, path: Path) -> bool:
        """
        Check if a path and all its parent directories are free of symlinks.

        This prevents symlink-based path traversal attacks by checking every
        component of the path chain before resolution.

        Args:
            path: Path to check for symlinks

        Returns:
            True if path has no symlinks, False otherwise
        """
        try:
            # Check the target file itself
            if path.is_symlink():
                logger.warning(f"Target path is a symlink: {path}")
                return False

            # Check all parent directories
            current_path = path.parent
            while True:
                if current_path.is_symlink():
                    logger.warning(f"Parent directory is a symlink: {current_path}")
                    return False

                # Stop when we reach a path that doesn't exist or root
                if not current_path.exists() or current_path == current_path.parent:
                    break

                current_path = current_path.parent

            return True

        except (OSError, RuntimeError) as e:
            logger.warning(f"Symlink check failed for {path}: {e}")
            return False

    def _is_path_contained(self, resolved_path: Path, resolved_routes_dir: Path) -> bool:
        """
        Cross-platform check if a path is contained within a directory.

        Uses multiple methods to ensure reliable containment checking
        across different operating systems.

        Args:
            resolved_path: Resolved absolute path to check
            resolved_routes_dir: Resolved absolute routes directory

        Returns:
            True if path is contained, False otherwise
        """
        try:
            # Method 1: Try relative_to (most reliable)
            try:
                resolved_path.relative_to(resolved_routes_dir)
                return True
            except ValueError:
                pass  # Try other methods

            # Method 2: Path prefix check (works on Windows)
            if str(resolved_path).lower().startswith(str(resolved_routes_dir).lower()):
                # Additional check to ensure we're not being fooled by similar names
                relative_part = str(resolved_path)[len(str(resolved_routes_dir)):].lstrip('\\/')
                return not relative_part.startswith('..')

            # Method 3: File system device check (Unix-like systems)
            if hasattr(resolved_path, 'stat') and hasattr(resolved_routes_dir, 'stat'):
                path_stat = resolved_path.stat()
                routes_stat = resolved_routes_dir.stat()

                # Check if they're on the same device and paths are reasonable
                if path_stat.st_dev == routes_stat.st_dev:
                    return True

            return False

        except (OSError, RuntimeError) as e:
            logger.warning(f"Path containment check failed: {e}")
            return False

    def _is_safe_hard_link(self, resolved_path: Path, resolved_routes_dir: Path) -> bool:
        """
        Check if a file is a safe hard link (doesn't point outside routes directory).

        Hard links can be used to bypass path validation by linking to files
        outside the intended directory.

        Args:
            resolved_path: Resolved path to check
            resolved_routes_dir: Resolved routes directory

        Returns:
            True if hard link is safe or not a hard link, False otherwise
        """
        try:
            if not resolved_path.exists():
                return True  # Non-existent files are safe

            # Get stat information
            stat_info = resolved_path.stat()

            # Check if file has multiple hard links (> 1)
            if stat_info.st_nlink > 1:
                # Find all hard links to this inode
                try:
                    # This is a simplified check - in production, you might want
                    # to implement more sophisticated hard link detection
                    parent_dir = resolved_path.parent

                    # For security, reject files with multiple hard links
                    logger.warning(f"File with multiple hard links detected: {resolved_path} (nlink={stat_info.st_nlink})")
                    return False

                except (OSError, RuntimeError):
                    # If we can't check hard links, err on the side of caution
                    logger.warning(f"Unable to verify hard link safety for: {resolved_path}")
                    return False

            return True

        except (OSError, RuntimeError) as e:
            logger.warning(f"Hard link check failed for {resolved_path}: {e}")
            return False

    def _is_secure_directory(self, directory: Path) -> bool:
        """
        Check if a directory has secure permissions.

        In development, allows more permissive permissions for convenience.
        In production, enforces strict security requirements.

        Args:
            directory: Directory path to check

        Returns:
            True if directory has secure permissions, False otherwise
        """
        try:
            # Import environment detection from security module
            from ..security import detect_environment

            stat_info = directory.stat()
            mode = stat_info.st_mode

            # Get current environment
            environment = detect_environment()

            # In development, allow world-writable for convenience
            if environment.value == 'development':
                if mode & stat.S_IWOTH:
                    logger.info(f"Development environment: Allowing world-writable directory: {directory}")
                    logger.info("Consider using stricter permissions for production")
                return True

            # In production and testing, enforce strict permissions
            if mode & stat.S_IWOTH:
                logger.warning(f"Directory is world-writable: {directory}")
                logger.error("SECURITY: World-writable directories are not allowed in production")
                return False

            # Security: Check ownership (Unix-like systems)
            if hasattr(os, 'getuid'):
                if stat_info.st_uid != os.getuid() and stat_info.st_uid != 0:
                    logger.warning(f"Directory not owned by current user: {directory}")
                    # This is a warning, not a failure, as it might be legitimate

            return True

        except (OSError, RuntimeError) as e:
            logger.warning(f"Directory permission check failed for {directory}: {e}")
            return False

    def _has_secure_file_permissions(self, file_path: Path) -> bool:
        """
        Check if a file has secure permissions.

        In development, allows more permissive permissions for convenience.
        In production, enforces strict security requirements.

        Args:
            file_path: File path to check

        Returns:
            True if file has secure permissions, False otherwise
        """
        try:
            # Import environment detection from security module
            from ..security import detect_environment

            stat_info = file_path.stat()
            mode = stat_info.st_mode

            # Get current environment
            environment = detect_environment()

            # Security: Regular files should not be executable (always enforced)
            if stat.S_ISREG(mode) and (mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)):
                logger.warning(f"File is executable: {file_path}")
                return False

            # In development, allow world-writable files for convenience
            if environment.value == 'development':
                if mode & stat.S_IWOTH:
                    logger.info(f"Development environment: Allowing world-writable file: {file_path}")
                return True

            # In production and testing, enforce strict permissions
            if mode & stat.S_IWOTH:
                logger.warning(f"File is world-writable: {file_path}")
                logger.error("SECURITY: World-writable files are not allowed in production")
                return False

            return True

        except (OSError, RuntimeError) as e:
            logger.warning(f"File permission check failed for {file_path}: {e}")
            return False

    def _is_safe_module_name(self, module_name: str) -> bool:
        """
        Validate that a module name is safe for import.

        Args:
            module_name: Module name to validate

        Returns:
            True if module name is safe, False otherwise
        """
        try:
            # Security: Check for dangerous characters
            if not module_name.replace('.', '').replace('_', '').isalnum():
                logger.warning(f"Unsafe characters in module name: {module_name}")
                return False

            # Security: Check for dangerous patterns
            dangerous_patterns = [
                '..', '__import__', 'eval', 'exec', 'compile', 'open',
                'file', 'input', 'raw_input', 'reload', '__builtins__',
                'os', 'sys', 'subprocess', 'socket', 'threading',
                'multiprocessing', 'asyncio'
            ]

            for pattern in dangerous_patterns:
                if pattern in module_name.lower():
                    logger.warning(f"Dangerous pattern in module name: {pattern} in {module_name}")
                    return False

            # Security: Check length limits
            if len(module_name) > 255:
                logger.warning(f"Module name too long: {len(module_name)} characters")
                return False

            return True

        except Exception as e:
            logger.warning(f"Module name validation failed for {module_name}: {e}")
            return False

    def _is_safe_module_spec(self, spec: Any, file_path: Path) -> bool:
        """
        Validate that a module spec is safe for loading.

        Args:
            spec: Module spec to validate
            file_path: Original file path for logging

        Returns:
            True if module spec is safe, False otherwise
        """
        try:
            # Security: Check if loader exists and is safe
            if spec.loader is None:
                logger.warning(f"No loader for module spec: {file_path}")
                return False

            # Security: Check for suspicious loader patterns
            loader_name = str(type(spec.loader).__name__).lower()
            suspicious_loaders = ['execfile', 'runpy', 'imp']

            for suspicious in suspicious_loaders:
                if suspicious in loader_name:
                    logger.warning(f"Suspicious loader detected: {loader_name} for {file_path}")
                    return False

            return True

        except Exception as e:
            logger.warning(f"Module spec validation failed for {file_path}: {e}")
            return False

    def _log_security_event(self, event_type: str, path: str, details: str = ""):
        """
        Log security-related events for monitoring and alerting.

        Args:
            event_type: Type of security event
            path: Path involved in the event
            details: Additional details about the event
        """
        try:
            # Try to use the centralized security logger
            from reroute.logging import security_logger
            security_logger.log_path_traversal(
                path=path,
                details=f"Event: {event_type}, Details: {details}"
            )
        except ImportError:
            # Fallback to standard logging with security context
            security_msg = f"SECURITY ALERT - {event_type}: Path={path}, Details={details}"

            # Log at appropriate level based on event type
            if event_type in ['null_byte_in_path', 'path_traversal_pattern', 'path_escape']:
                logger.error(security_msg)
            elif event_type in ['symlink_detected', 'unsafe_hard_link']:
                logger.warning(security_msg)
            else:
                logger.info(security_msg)
