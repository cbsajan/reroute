"""
OpenAPI 3.0+ specification parser.

This module handles parsing and validation of OpenAPI specifications
from both JSON and YAML formats.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Parameter:
    """OpenAPI parameter definition."""
    name: str
    in_: str  # path, query, header, cookie, formData
    required: bool = False
    schema_: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    type_: Optional[str] = None  # For formData parameters: str, int, UploadFile, etc.
    format_: Optional[str] = None  # For file detection: binary, etc.


@dataclass
class Response:
    """OpenAPI response definition."""
    status_code: str
    description: str
    content: Optional[Dict[str, Any]] = None


@dataclass
class Operation:
    """OpenAPI operation definition."""
    path: str
    method: str
    operation_id: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = None
    parameters: List[Parameter] = None
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Response] = None
    security: List[Dict[str, Any]] = None
    has_form_data: bool = False  # True if request body uses multipart/form-data

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.parameters is None:
            self.parameters = []
        if self.responses is None:
            self.responses = {}


@dataclass
class Schema:
    """OpenAPI schema definition."""
    name: str
    type_: str
    properties: Dict[str, Any] = None
    required: List[str] = None
    description: Optional[str] = None
    enum: List[Any] = None
    ref: Optional[str] = None

    def __post_init__(self):
        if self.properties is None:
            self.properties = {}
        if self.required is None:
            self.required = []


class OpenAPIParser:
    """Parse OpenAPI 3.0+ specifications."""

    def __init__(self, spec_path: str):
        """Initialize parser with spec file path.

        Args:
            spec_path: Path to OpenAPI spec file (JSON or YAML)
        """
        self.spec_path = Path(spec_path)
        self.spec: Dict[str, Any] = {}

    def parse_spec(self) -> Dict[str, Any]:
        """Parse OpenAPI specification from file.

        Returns:
            Parsed specification as dictionary

        Raises:
            FileNotFoundError: If spec file doesn't exist
            ValueError: If spec file is invalid
        """
        if not self.spec_path.exists():
            raise FileNotFoundError(f"OpenAPI spec not found: {self.spec_path}")

        content = self.spec_path.read_text(encoding="utf-8")

        # Try JSON first, then YAML
        try:
            self.spec = json.loads(content)
        except json.JSONDecodeError:
            try:
                import yaml
                self.spec = yaml.safe_load(content)
            except ImportError:
                raise ValueError(
                    "YAML format detected but pyyaml not installed. "
                    "Install with: pip install pyyaml"
                )
            except Exception as e:
                raise ValueError(f"Failed to parse YAML spec: {e}")

        self.validate_spec(self.spec)
        return self.spec

    def validate_spec(self, spec: Dict[str, Any]) -> bool:
        """Validate OpenAPI specification structure.

        Args:
            spec: Parsed specification dictionary

        Returns:
            True if valid

        Raises:
            ValueError: If spec is invalid
        """
        if "openapi" not in spec and "swagger" not in spec:
            raise ValueError(
                "Invalid OpenAPI spec: missing 'openapi' or 'swagger' field"
            )

        version = spec.get("openapi", spec.get("swagger", ""))
        if not version.startswith(("3.", "2.")):
            raise ValueError(
                f"Unsupported OpenAPI version: {version}. "
                "Only 2.x and 3.x are supported."
            )

        if "paths" not in spec:
            raise ValueError("Invalid OpenAPI spec: missing 'paths' field")

        return True

    def extract_operations(self, spec: Optional[Dict[str, Any]] = None) -> List[Operation]:
        """Extract all operations from OpenAPI spec.

        Args:
            spec: Parsed specification (uses self.spec if not provided)

        Returns:
            List of Operation objects
        """
        if spec is None:
            spec = self.spec

        if not spec:
            raise ValueError("No spec loaded. Call parse_spec() first.")

        operations = []
        paths = spec.get("paths", {})

        for path, path_item in paths.items():
            for method in ["get", "post", "put", "patch", "delete", "options", "head", "trace"]:
                if method in path_item:
                    op_spec = path_item[method]
                    operation = self._parse_operation(path, method, op_spec)
                    operations.append(operation)

        return operations

    def _parse_operation(self, path: str, method: str, spec: Dict[str, Any]) -> Operation:
        """Parse a single operation from spec.

        Args:
            path: URL path
            method: HTTP method
            spec: Operation specification

        Returns:
            Operation object
        """
        # Parse parameters
        parameters = []
        for param_spec in spec.get("parameters", []):
            param = Parameter(
                name=param_spec["name"],
                in_=param_spec["in"],
                required=param_spec.get("required", False),
                schema_=param_spec.get("schema"),
                description=param_spec.get("description"),
            )
            parameters.append(param)

        # Extract formData parameters from requestBody
        request_body = spec.get("requestBody")
        has_form_data = False

        if request_body:
            content = request_body.get("content", {})
            form_data_spec = content.get("multipart/form-data") or content.get("application/x-www-form-urlencoded")

            if form_data_spec:
                has_form_data = True
                schema = form_data_spec.get("schema", {})
                properties = schema.get("properties", {})
                required_fields = schema.get("required", [])

                for prop_name, prop_spec in properties.items():
                    # Determine type
                    prop_type = prop_spec.get("type", "string")
                    prop_format = prop_spec.get("format", "")

                    # Check if items have format="binary" (for array of files)
                    items_spec = prop_spec.get("items", {})
                    items_format = items_spec.get("format", "")

                    # Determine if this is a file upload
                    is_file = (
                        prop_format == "binary" or
                        items_format == "binary" or
                        prop_name.lower() in ["file", "files", "avatar", "attachment", "document"]
                    )

                    # Determine the parameter type
                    if prop_type == "array":
                        if is_file and items_format == "binary":
                            # Array of files
                            param_type = "List[UploadFile]"
                        else:
                            # Array of other types
                            item_type = items_spec.get("type", "str")
                            type_map = {
                                "string": "str",
                                "integer": "int",
                                "number": "float",
                                "boolean": "bool",
                            }
                            mapped_item_type = type_map.get(item_type, "str")
                            param_type = f"List[{mapped_item_type}]"
                    elif is_file:
                        # Single file
                        param_type = "UploadFile"
                    elif prop_type == "object":
                        # Object types come as JSON strings in form data
                        # Use str type and let handler parse with json.loads()
                        param_type = "str"
                    else:
                        # Other types
                        type_map = {
                            "string": "str",
                            "integer": "int",
                            "number": "float",
                            "boolean": "bool",
                            "array": "List",
                        }
                        param_type = type_map.get(prop_type, "str")

                    param = Parameter(
                        name=prop_name,
                        in_="formData",
                        required=prop_name in required_fields,
                        type_=param_type,
                        format_=prop_format,
                        description=prop_spec.get("description"),
                    )
                    parameters.append(param)

        # Parse responses
        responses = {}
        for status_code, resp_spec in spec.get("responses", {}).items():
            response = Response(
                status_code=status_code,
                description=resp_spec.get("description", ""),
                content=resp_spec.get("content"),
            )
            responses[status_code] = response

        return Operation(
            path=path,
            method=method.lower(),
            operation_id=spec.get("operationId"),
            summary=spec.get("summary"),
            description=spec.get("description"),
            tags=spec.get("tags", []),
            parameters=parameters,
            request_body=spec.get("requestBody"),
            responses=responses,
            security=spec.get("security"),
            has_form_data=has_form_data,
        )

    def extract_schemas(self, spec: Optional[Dict[str, Any]] = None) -> Dict[str, Schema]:
        """Extract all schemas from OpenAPI spec components.

        Args:
            spec: Parsed specification (uses self.spec if not provided)

        Returns:
            Dictionary mapping schema names to Schema objects
        """
        if spec is None:
            spec = self.spec

        if not spec:
            raise ValueError("No spec loaded. Call parse_spec() first.")

        schemas = {}
        components = spec.get("components", {})
        definitions = spec.get("definitions", {})

        # OpenAPI 3.x uses components/schemas
        for name, schema_spec in components.get("schemas", {}).items():
            schema = self._parse_schema(name, schema_spec)
            schemas[name] = schema

        # Swagger 2.x uses definitions
        for name, schema_spec in definitions.items():
            schema = self._parse_schema(name, schema_spec)
            schemas[name] = schema

        return schemas

    def _parse_schema(self, name: str, spec: Dict[str, Any]) -> Schema:
        """Parse a single schema from spec.

        Args:
            name: Schema name
            spec: Schema specification

        Returns:
            Schema object
        """
        return Schema(
            name=name,
            type_=spec.get("type", "object"),
            properties=spec.get("properties", {}),
            required=spec.get("required", []),
            description=spec.get("description"),
            enum=spec.get("enum"),
            ref=spec.get("$ref"),
        )

    def get_base_path(self, spec: Optional[Dict[str, Any]] = None) -> str:
        """Get base path from server configuration.

        Args:
            spec: Parsed specification (uses self.spec if not provided)

        Returns:
            Base URL path (e.g., "/api/v1")
        """
        if spec is None:
            spec = self.spec

        # OpenAPI 3.x
        servers = spec.get("servers", [])
        if servers:
            url = servers[0].get("url", "")
            # Extract path from URL
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.path

        # Swagger 2.x
        host = spec.get("host", "")
        base_path = spec.get("basePath", "")
        return base_path

    def get_info(self, spec: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get info section from spec.

        Args:
            spec: Parsed specification (uses self.spec if not provided)

        Returns:
            Dictionary with title, version, description, etc.
        """
        if spec is None:
            spec = self.spec

        return spec.get("info", {})
