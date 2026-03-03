"""
Pydantic model generator from OpenAPI schemas.

This module generates Pydantic model classes from OpenAPI
schema definitions found in the components/definitions section.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union
from datetime import datetime, date

from jinja2 import Environment
from pydantic import BaseModel, Field, EmailStr, AnyUrl


class ModelGenerator:
    """Generate Pydantic models from OpenAPI schemas."""

    def __init__(self, template_env: Optional[Environment] = None):
        """Initialize model generator.

        Args:
            template_env: Jinja2 environment (uses default if not provided)
        """
        if template_env is None:
            from reroute.cli._template_loader import jinja_env
            self.env = jinja_env
        else:
            self.env = template_env

        # Type mapping from OpenAPI to Python/Pydantic
        self.type_map = {
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "array": "List",
            "object": "dict",
        }

    def generate_model(
        self,
        schema_spec: Dict[str, Any],
        name: str,
        output_path: Optional[Path] = None,
    ) -> str:
        """Generate a Pydantic model from an OpenAPI schema.

        Args:
            schema_spec: OpenAPI schema definition (raw dict)
            name: Name for the model class
            output_path: Optional file path to write model to

        Returns:
            Generated model code as string
        """
        properties = schema_spec.get("properties", {})
        required = schema_spec.get("required", [])

        fields = []
        for prop_name, prop_spec in properties.items():
            field_def = self._generate_field(prop_name, prop_spec, prop_name in required)
            fields.append(field_def)

        model_code = self._generate_model_class(name, fields, schema_spec)

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(model_code, encoding="utf-8")

        return model_code

    def generate_models_file(
        self,
        schemas: Dict[str, Dict[str, Any]],
        output_path: Path,
    ) -> None:
        """Generate a models file from multiple schemas.

        Args:
            schemas: Dictionary of schema definitions
            output_path: Path to write the models file
        """
        models = []

        for name, schema_spec in schemas.items():
            model_code = self.generate_model(schema_spec, name)
            models.append(model_code)

        # Combine all models into one file
        template = self.env.get_template("models/openapi_models.py.j2")
        content = template.render(models=models)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

    def _generate_field(
        self,
        name: str,
        spec: Dict[str, Any],
        required: bool = False,
    ) -> str:
        """Generate a single field definition.

        Args:
            name: Field name
            spec: Property specification
            required: Whether field is required

        Returns:
            Field definition as string
        """
        # Get type
        field_type = self._get_python_type(spec)

        # Handle arrays
        if spec.get("type") == "array":
            items_spec = spec.get("items", {})
            item_type = self._get_python_type(items_spec)
            field_type = f"List[{item_type}]"

        # Handle references
        if "$ref" in spec:
            ref_name = self._extract_ref_name(spec["$ref"])
            field_type = ref_name

        # Build Field() definition with metadata
        field_parts = []

        # Description
        description = spec.get("description")
        if description:
            field_parts.append(f'description="{description}"')

        # Example value from spec
        if "example" in spec:
            example = repr(spec["example"])
            field_parts.append(f"example={example}")

        # Build the field definition
        if field_parts:
            field_args = ", ".join(field_parts)
            if required:
                field = f'    {name}: {field_type} = Field({field_args})'
            else:
                field = f'    {name}: {field_type} = Field(default=None, {field_args})'
        else:
            if required:
                field = f'    {name}: {field_type}'
            else:
                field = f'    {name}: {field_type} = None'

        return field

    def _get_python_type(self, spec: Dict[str, Any]) -> str:
        """Convert OpenAPI type to Python type.

        Args:
            spec: Property specification

        Returns:
            Python type as string
        """
        # Handle enum
        if "enum" in spec:
            values = ", ".join(repr(v) for v in spec["enum"])
            return f"Literal[{values}]"

        # Handle references
        if "$ref" in spec:
            return self._extract_ref_name(spec["$ref"])

        # Handle basic types with format
        openapi_type = spec.get("type", "string")
        format_ = spec.get("format", "")

        # Type with format
        if openapi_type == "string":
            if format_ == "date-time":
                return "datetime"
            elif format_ == "date":
                return "date"
            elif format_ == "email":
                return "EmailStr"
            elif format_ == "uuid":
                return "UUID"  # UUID is a standard Python type
            elif format_ == "uri":
                return "AnyUrl"
            elif format_ == "binary":
                return "bytes"

        # Array with items
        if openapi_type == "array":
            items_spec = spec.get("items", {})
            item_type = self._get_python_type(items_spec)
            return f"List[{item_type}]"

        # Basic type mapping
        return self.type_map.get(openapi_type, "Any")

    def _extract_ref_name(self, ref: str) -> str:
        """Extract schema name from $ref.

        Args:
            ref: $ref value (e.g., "#/components/schemas/User")

        Returns:
            Schema name
        """
        parts = ref.split("/")
        return parts[-1]

    def _generate_model_class(
        self,
        name: str,
        fields: List[str],
        schema_spec: Dict[str, Any],
    ) -> str:
        """Generate a complete model class.

        Args:
            name: Model class name
            fields: List of field definitions
            schema_spec: Original schema specification

        Returns:
            Model class code
        """
        # Class definition
        lines = [f"class {name}(BaseModel):"]

        # Add docstring if description exists
        if schema_spec.get("description"):
            lines.append(f'    """{schema_spec["description"]}"""')
        else:
            lines.append(f'    """{name} model."""')

        # Add configuration
        lines.append("")
        lines.append("    class Config:")
        lines.append('        """Pydantic config."""')
        lines.append("        from_attributes = True")
        lines.append("")

        # Add fields
        lines.extend(fields)

        return "\n".join(lines) + "\n"

    def handle_nested_schemas(self, schema: Dict[str, Any]) -> str:
        """Handle nested object schemas.

        Args:
            schema: Schema definition

        Returns:
            Type definition for nested schema
        """
        if "properties" in schema:
            # Inline object definition
            fields = []
            for name, prop_spec in schema["properties"].items():
                field_def = self._generate_field(
                    name,
                    prop_spec,
                    name in schema.get("required", []),
                )
                fields.append(field_def)

            return "\n".join(fields)

        # Array of objects
        if schema.get("type") == "array":
            items_spec = schema.get("items", {})
            return f"List[{self.handle_nested_schemas(items_spec)}]"

        # Simple type
        return self._get_python_type(schema)

    def generate_request_model(
        self,
        operation: Dict[str, Any],
        name: str,
    ) -> str:
        """Generate a request model from operation request body.

        Args:
            operation: OpenAPI operation specification
            name: Name for the model class

        Returns:
            Generated request model code
        """
        request_body = operation.get("requestBody", {})
        content = request_body.get("content", {})

        # Try to get JSON schema
        json_content = content.get("application/json", {})
        schema = json_content.get("schema", {})

        if not schema:
            return None

        return self.generate_model(schema, name)

    def generate_response_model(
        self,
        operation: Dict[str, Any],
        name: str,
        status_code: str = "200",
    ) -> str:
        """Generate a response model from operation response.

        Args:
            operation: OpenAPI operation specification
            name: Name for the model class
            status_code: Response status code

        Returns:
            Generated response model code
        """
        responses = operation.get("responses", {})
        response = responses.get(status_code, {})
        content = response.get("content", {})

        # Try to get JSON schema
        json_content = content.get("application/json", {})
        schema = json_content.get("schema", {})

        if not schema:
            return None

        return self.generate_model(schema, name)

    def generate_all_models_for_operation(
        self,
        operation: Dict[str, Any],
        operation_name: str,
        output_dir: Path,
    ) -> Dict[str, str]:
        """Generate all models (request/response) for an operation.

        Args:
            operation: OpenAPI operation specification
            operation_name: Name for the operation
            output_dir: Directory to write models to

        Returns:
            Dictionary mapping model types to file paths
        """
        generated = {}

        # Request model
        request_model = self.generate_request_model(
            operation,
            f"{operation_name}Request",
        )
        if request_model:
            request_path = output_dir / f"{operation_name}_request.py"
            request_path.write_text(request_model, encoding="utf-8")
            generated["request"] = str(request_path)

        # Response model
        response_model = self.generate_response_model(
            operation,
            f"{operation_name}Response",
        )
        if response_model:
            response_path = output_dir / f"{operation_name}_response.py"
            response_path.write_text(response_model, encoding="utf-8")
            generated["response"] = str(response_path)

        return generated


def _get_template_env() -> Environment:
    """Get the Jinja2 template environment.

    Returns:
        Jinja2 Environment configured for REROUTE templates
    """
    from reroute.cli._template_loader import jinja_env
    return jinja_env
