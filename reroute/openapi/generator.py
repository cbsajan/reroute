"""
Route code generator from OpenAPI operations.

This module generates REROUTE-compatible route files from
parsed OpenAPI specifications.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, Template

from reroute.openapi.parser import Operation


class RouteGenerator:
    """Generate route files from OpenAPI operations."""

    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize route generator.

        Args:
            template_dir: Custom template directory (uses default if not provided)
        """
        if template_dir is None:
            # Use default templates from reroute package
            from reroute.cli._template_loader import jinja_env
            self.env = jinja_env
        else:
            self.env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                autoescape=False,
            )

    def generate_route_file(
        self,
        operation: Operation,
        output_dir: Path,
        base_path: str = "",
        route_path: str = None,
    ) -> str:
        """Generate a single route file from an operation.

        Args:
            operation: Operation to generate route for
            output_dir: Base output directory for routes
            base_path: Base path to strip from operation path
            route_path: Pre-calculated route path (optional)

        Returns:
            Path to generated file
        """
        # Determine route path and file location
        if route_path is None:
            route_path = operation.path
            if base_path and route_path.startswith(base_path):
                route_path = route_path[len(base_path):]

        # Create file path from route path
        file_path = self._get_file_path_from_route(route_path, operation.method)

        # Generate directory structure
        # file_path is the full path (e.g., "api/upload"), so we create that directory
        full_dir = output_dir / file_path
        full_dir.mkdir(parents=True, exist_ok=True)

        # Generate file content
        template = self.env.get_template("routes/openapi_route.py.j2")
        content = template.render(
            operation=operation,
            route_path=route_path,
            route_name=self._extract_resource_name(route_path),
            class_name=self._generate_class_name(operation, route_path),
        )

        # Write file
        output_file = full_dir / "page.py"
        output_file.write_text(content, encoding="utf-8")

        return str(output_file)

    def generate_crud_route(
        self,
        operations: List[Operation],
        resource_name: str,
        output_dir: Path,
    ) -> str:
        """Generate a CRUD route file from multiple operations.

        Args:
            operations: List of operations for the same resource
            resource_name: Name of the resource (e.g., "users")
            output_dir: Base output directory for routes

        Returns:
            Path to generated file
        """
        # Group operations by method
        ops_by_method = {op.method: op for op in operations}

        # Get route path from first operation
        route_path = operations[0].path if operations else ""

        # Generate file content
        template = self.env.get_template("routes/crud_route.py.j2")
        content = template.render(
            resource_name=resource_name,
            route_path=route_path,
            route_name=resource_name,  # Use resource_name as route_name
            get_operation=ops_by_method.get("get"),
            post_operation=ops_by_method.get("post"),
            put_operation=ops_by_method.get("put"),
            patch_operation=ops_by_method.get("patch"),
            delete_operation=ops_by_method.get("delete"),
            class_name=self._generate_crud_class_name(resource_name),
        )

        # Write file
        output_file = output_dir / resource_name / "page.py"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(content, encoding="utf-8")

        return str(output_file)

    def create_folder_structure(
        self,
        operations: List[Operation],
        base_dir: Path,
        base_path: str = "",
    ) -> Dict[str, List[str]]:
        """Create folder structure for all operations.

        Args:
            operations: List of all operations
            base_dir: Base output directory
            base_path: Base path to strip from operation paths

        Returns:
            Dictionary mapping paths to generated files
        """
        generated = {}

        # Group operations by resource path
        resources = self._group_operations_by_resource(operations)

        for resource_path, resource_ops in resources.items():
            route_path = resource_path
            if base_path and route_path.startswith(base_path):
                route_path = route_path[len(base_path):]

            # Generate route path for this resource
            if len(resource_ops) > 1:
                # Multiple operations - use CRUD template
                resource_name = self._extract_resource_name(route_path)
                output_file = self.generate_crud_route(
                    resource_ops,
                    resource_name,
                    base_dir,
                )
                generated[resource_path] = [output_file]
            else:
                # Single operation - use basic template
                for op in resource_ops:
                    output_file = self.generate_route_file(
                        op,
                        base_dir,
                        base_path,
                        route_path,  # Pass the already-calculated route_path
                    )
                    if resource_path not in generated:
                        generated[resource_path] = []
                    generated[resource_path].append(output_file)

        return generated

    def _get_file_path_from_route(self, route_path: str, method: str) -> Path:
        """Convert route path to file path.

        Args:
            route_path: URL route path (e.g., "/users/{id}")
            method: HTTP method

        Returns:
            Path object for the route file
        """
        # Remove leading slash and convert path separators
        clean_path = route_path.lstrip("/")

        # Replace path parameters with directories
        # /users/{id} -> users/_id
        clean_path = clean_path.replace("{", "_").replace("}", "")

        return Path(clean_path)

    def _generate_class_name(self, operation: Operation, route_path: str) -> str:
        """Generate a class name from operation and path.

        Args:
            operation: Operation object
            route_path: Cleaned route path

        Returns:
            Class name for the route
        """
        # Extract meaningful parts from path
        parts = [p.strip("_") for p in route_path.split("/") if p.strip("_")]

        if not parts:
            parts = ["root"]

        # Capitalize and join
        base_name = "".join(p.capitalize() for p in parts)

        # Add method suffix for single-operation routes
        method_suffix = operation.method.capitalize()
        return f"{base_name}{method_suffix}Route"

    def _generate_crud_class_name(self, resource_name: str) -> str:
        """Generate class name for CRUD route.

        Args:
            resource_name: Resource name (e.g., "users")

        Returns:
            Class name for the CRUD route
        """
        return f"{resource_name.capitalize()}Route"

    def _extract_resource_name(self, route_path: str) -> str:
        """Extract resource name from route path.

        Args:
            route_path: URL route path

        Returns:
            Resource name (e.g., "users" from "/users/{id}")
        """
        parts = [p for p in route_path.split("/") if p and not p.startswith("{")]

        if parts:
            return parts[-1].strip("_")

        return "resource"

    def _group_operations_by_resource(
        self,
        operations: List[Operation],
    ) -> Dict[str, List[Operation]]:
        """Group operations by their exact resource path.

        Only groups multiple methods (GET, POST, PUT, DELETE) on the SAME path.
        Different paths always get separate route files.

        Args:
            operations: List of operations

        Returns:
            Dictionary mapping exact paths to operations
        """
        resources = {}

        for op in operations:
            # Group by exact path, not base path
            # /api/upload and /api/upload/multiple are different resources
            exact_path = op.path

            if exact_path not in resources:
                resources[exact_path] = []
            resources[exact_path].append(op)

        return resources

    def _get_base_resource_path(self, path: str) -> str:
        """Get base resource path from a full path.

        Args:
            path: Full path with possible parameters

        Returns:
            Base resource path
        """
        parts = path.split("/")

        # Find first non-parameter segment
        for i, part in enumerate(parts):
            if not part.startswith("{"):
                if i > 0:
                    return "/".join(parts[:i+1])

        return path

    def generate_imports(self, operation: Operation) -> List[str]:
        """Generate import statements for an operation.

        Args:
            operation: Operation to generate imports for

        Returns:
            List of import statements
        """
        imports = []

        # Always import RouteBase
        imports.append("from reroute import RouteBase")

        # Add Param imports if needed
        if operation.parameters:
            imports.append("from reroute import Param")

        # Add Body import if request body exists
        if operation.request_body:
            imports.append("from reroute import Body")

        # Add response imports
        if operation.responses:
            imports.append("from typing import Optional")
            imports.append("from pydantic import BaseModel")

        return imports
