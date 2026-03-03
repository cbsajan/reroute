"""
OpenAPI parser tests.

Tests for parsing OpenAPI 3.0/3.1 and Swagger 2.0 specifications.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from reroute.openapi.parser import (
    OpenAPIParser,
    Parameter,
    Response,
    Operation,
    Schema,
)


# Fixtures
@pytest.fixture
def sample_openapi_3_spec():
    """Sample OpenAPI 3.0 specification."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Sample API",
            "version": "1.0.0",
            "description": "A sample API"
        },
        "servers": [{"url": "https://api.example.com/v1"}],
        "paths": {
            "/users": {
                "get": {
                    "operationId": "getUsers",
                    "summary": "List users",
                    "tags": ["users"],
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "array"}
                                }
                            }
                        }
                    }
                },
                "post": {
                    "operationId": "createUser",
                    "summary": "Create user",
                    "tags": ["users"],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/User"}
                            }
                        }
                    },
                    "responses": {
                        "201": {"description": "Created"}
                    }
                }
            },
            "/users/{id}": {
                "get": {
                    "operationId": "getUser",
                    "summary": "Get user by ID",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Success"}
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "email": {"type": "string", "format": "email"}
                    },
                    "required": ["id", "name"]
                }
            }
        }
    }


@pytest.fixture
def sample_swagger_2_spec():
    """Sample Swagger 2.0 specification."""
    return {
        "swagger": "2.0",
        "info": {
            "title": "Sample API",
            "version": "1.0.0"
        },
        "host": "api.example.com",
        "basePath": "/v1",
        "paths": {
            "/users": {
                "get": {
                    "operationId": "getUsers",
                    "tags": ["users"]
                }
            }
        },
        "definitions": {
            "User": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"}
                }
            }
        }
    }


@pytest.fixture
def temp_openapi_file(tmp_path, sample_openapi_3_spec):
    """Create a temporary OpenAPI spec file."""
    spec_file = tmp_path / "openapi.json"
    spec_file.write_text(json.dumps(sample_openapi_3_spec))
    return spec_file


@pytest.fixture
def temp_yaml_file(tmp_path, sample_openapi_3_spec):
    """Create a temporary YAML spec file."""
    spec_file = tmp_path / "openapi.yaml"
    # Convert to YAML format
    yaml_content = """
openapi: 3.0.0
info:
  title: Sample API
  version: 1.0.0
paths:
  /users:
    get:
      operationId: getUsers
      summary: List users
"""
    spec_file.write_text(yaml_content)
    return spec_file


class OpenAPIParserInitTests:
    """Tests for OpenAPIParser initialization."""

    def test_init_with_path(self):
        """Test parser initialization with file path."""
        parser = OpenAPIParser("test.json")
        assert parser.spec_path == Path("test.json")
        assert parser.spec == {}

    def test_init_with_pathlib_path(self):
        """Test parser initialization with Path object."""
        path = Path("test.json")
        parser = OpenAPIParser(path)
        assert parser.spec_path == path


class ParseSpecTests:
    """Tests for parse_spec method."""

    def test_parse_json_spec(self, temp_openapi_file):
        """Test parsing JSON OpenAPI spec."""
        parser = OpenAPIParser(str(temp_openapi_file))
        spec = parser.parse_spec()
        assert spec["openapi"] == "3.0.0"
        assert spec["info"]["title"] == "Sample API"

    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file raises error."""
        parser = OpenAPIParser("nonexistent.json")
        with pytest.raises(FileNotFoundError, match="OpenAPI spec not found"):
            parser.parse_spec()

    def test_parse_invalid_json(self, tmp_path):
        """Test parsing invalid JSON raises error."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("not valid json {")

        parser = OpenAPIParser(str(invalid_file))
        with pytest.raises(ValueError):
            parser.parse_spec()

    @patch('reroute.openapi.parser.yaml')
    def test_parse_yaml_spec(self, mock_yaml, temp_openapi_file):
        """Test parsing YAML spec when JSON fails."""
        # Make JSON parsing fail
        yaml_content = "openapi: 3.0.0\ninfo:\n  title: Test"
        temp_openapi_file.write_text(yaml_content)

        mock_yaml.safe_load.return_value = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {}
        }

        parser = OpenAPIParser(str(temp_openapi_file))
        spec = parser.parse_spec()
        mock_yaml.safe_load.assert_called_once()
        assert spec["openapi"] == "3.0.0"

    def test_parse_yaml_without_pyyaml_installed(self, tmp_path):
        """Test parsing YAML without pyyaml raises helpful error."""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("openapi: 3.0.0")

        parser = OpenAPIParser(str(yaml_file))

        # Mock yaml import to fail
        with patch('reroute.openapi.parser.yaml', None):
            with patch('builtins.__import__', side_effect=ImportError):
                # Actually, we need to make json.loads fail first
                pass

        # This test is tricky - the actual code catches ImportError
        # Let's test the error message a different way
        yaml_file2 = tmp_path / "test2.yaml"
        yaml_file2.write_text("not: valid: yaml")

        parser2 = OpenAPIParser(str(yaml_file2))
        with pytest.raises(ImportError):
            # Force the code path
            import sys
            sys.modules['yaml'] = None
            parser2.parse_spec()


class ValidateSpecTests:
    """Tests for validate_spec method."""

    def test_validate_valid_openapi_3(self, sample_openapi_3_spec):
        """Test validating valid OpenAPI 3.0 spec."""
        parser = OpenAPIParser("test.json")
        assert parser.validate_spec(sample_openapi_3_spec) is True

    def test_validate_valid_swagger_2(self, sample_swagger_2_spec):
        """Test validating valid Swagger 2.0 spec."""
        parser = OpenAPIParser("test.json")
        assert parser.validate_spec(sample_swagger_2_spec) is True

    def test_validate_missing_version_field(self):
        """Test validation fails without openapi/swagger field."""
        parser = OpenAPIParser("test.json")
        invalid_spec = {"info": {}, "paths": {}}
        with pytest.raises(ValueError, match="missing 'openapi' or 'swagger'"):
            parser.validate_spec(invalid_spec)

    def test_validate_unsupported_version(self):
        """Test validation fails for unsupported version."""
        parser = OpenAPIParser("test.json")
        invalid_spec = {"openapi": "1.0.0", "paths": {}}
        with pytest.raises(ValueError, match="Unsupported OpenAPI version"):
            parser.validate_spec(invalid_spec)

    def test_validate_missing_paths(self):
        """Test validation fails without paths field."""
        parser = OpenAPIParser("test.json")
        invalid_spec = {"openapi": "3.0.0", "info": {}}
        with pytest.raises(ValueError, match="missing 'paths'"):
            parser.validate_spec(invalid_spec)


class ExtractOperationsTests:
    """Tests for extract_operations method."""

    def test_extract_operations_from_spec(self, temp_openapi_file):
        """Test extracting all operations from spec."""
        parser = OpenAPIParser(str(temp_openapi_file))
        parser.parse_spec()
        operations = parser.extract_operations()

        assert len(operations) == 3  # get /users, post /users, get /users/{id}

        # Check first operation
        assert operations[0].path == "/users"
        assert operations[0].method == "get"
        assert operations[0].operation_id == "getUsers"

    def test_extract_operations_without_parsing_first(self):
        """Test extract_operations raises error without parsing."""
        parser = OpenAPIParser("test.json")
        with pytest.raises(ValueError, match="No spec loaded"):
            parser.extract_operations()

    def test_extract_operation_parameters(self, temp_openapi_file):
        """Test parameters are extracted correctly."""
        parser = OpenAPIParser(str(temp_openapi_file))
        parser.parse_spec()
        operations = parser.extract_operations()

        get_users = [op for op in operations if op.operation_id == "getUsers"][0]
        assert len(get_users.parameters) == 1
        assert get_users.parameters[0].name == "limit"
        assert get_users.parameters[0].in_ == "query"
        assert get_users.parameters[0].required is False

    def test_extract_operation_responses(self, temp_openapi_file):
        """Test responses are extracted correctly."""
        parser = OpenAPIParser(str(temp_openapi_file))
        parser.parse_spec()
        operations = parser.extract_operations()

        get_users = [op for op in operations if op.operation_id == "getUsers"][0]
        assert "200" in get_users.responses
        assert get_users.responses["200"].description == "Success"

    def test_extract_operation_tags(self, temp_openapi_file):
        """Test tags are extracted correctly."""
        parser = OpenAPIParser(str(temp_openapi_file))
        parser.parse_spec()
        operations = parser.extract_operations()

        get_users = [op for op in operations if op.operation_id == "getUsers"][0]
        assert "users" in get_users.tags

    def test_extract_all_http_methods(self, tmp_path):
        """Test all HTTP methods are extracted."""
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/resource": {
                    "get": {"operationId": "get"},
                    "post": {"operationId": "post"},
                    "put": {"operationId": "put"},
                    "patch": {"operationId": "patch"},
                    "delete": {"operationId": "delete"},
                    "options": {"operationId": "options"},
                    "head": {"operationId": "head"},
                    "trace": {"operationId": "trace"}
                }
            }
        }
        spec_file = tmp_path / "all-methods.json"
        spec_file.write_text(json.dumps(spec))

        parser = OpenAPIParser(str(spec_file))
        parser.parse_spec()
        operations = parser.extract_operations()

        assert len(operations) == 8
        methods = {op.method for op in operations}
        assert methods == {"get", "post", "put", "patch", "delete", "options", "head", "trace"}


class ExtractSchemasTests:
    """Tests for extract_schemas method."""

    def test_extract_schemas_from_openapi_3(self, temp_openapi_file):
        """Test extracting schemas from OpenAPI 3.0 components."""
        parser = OpenAPIParser(str(temp_openapi_file))
        parser.parse_spec()
        schemas = parser.extract_schemas()

        assert "User" in schemas
        assert schemas["User"].type_ == "object"
        assert "id" in schemas["User"].properties
        assert "name" in schemas["User"].required

    def test_extract_schemas_from_swagger_2(self, tmp_path, sample_swagger_2_spec):
        """Test extracting schemas from Swagger 2.0 definitions."""
        spec_file = tmp_path / "swagger.json"
        spec_file.write_text(json.dumps(sample_swagger_2_spec))

        parser = OpenAPIParser(str(spec_file))
        parser.parse_spec()
        schemas = parser.extract_schemas()

        assert "User" in schemas
        assert schemas["User"].type_ == "object"

    def test_extract_schemas_without_parsing_first(self):
        """Test extract_schemas raises error without parsing."""
        parser = OpenAPIParser("test.json")
        with pytest.raises(ValueError, match="No spec loaded"):
            parser.extract_schemas()


class GetBasePathTests:
    """Tests for get_base_path method."""

    def test_get_base_path_from_openapi_3_servers(self, temp_openapi_file):
        """Test extracting base path from OpenAPI 3.0 servers."""
        parser = OpenAPIParser(str(temp_openapi_file))
        parser.parse_spec()
        base_path = parser.get_base_path()
        assert base_path == "/v1"

    def test_get_base_path_from_swagger_2(self, tmp_path, sample_swagger_2_spec):
        """Test extracting base path from Swagger 2.0."""
        spec_file = tmp_path / "swagger.json"
        spec_file.write_text(json.dumps(sample_swagger_2_spec))

        parser = OpenAPIParser(str(spec_file))
        parser.parse_spec()
        base_path = parser.get_base_path()
        assert base_path == "/v1"

    def test_get_base_path_empty(self, tmp_path):
        """Test base path when none specified."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {}
        }
        spec_file = tmp_path / "no-basepath.json"
        spec_file.write_text(json.dumps(spec))

        parser = OpenAPIParser(str(spec_file))
        parser.parse_spec()
        base_path = parser.get_base_path()
        assert base_path == ""


class GetInfoTests:
    """Tests for get_info method."""

    def test_get_info(self, temp_openapi_file):
        """Test extracting info section."""
        parser = OpenAPIParser(str(temp_openapi_file))
        parser.parse_spec()
        info = parser.get_info()

        assert info["title"] == "Sample API"
        assert info["version"] == "1.0.0"
        assert info["description"] == "A sample API"


class SchemaTests:
    """Tests for Schema dataclass."""

    def test_schema_creation(self):
        """Test creating a Schema object."""
        schema = Schema(
            name="User",
            type_="object",
            properties={"id": {"type": "string"}},
            required=["id"]
        )
        assert schema.name == "User"
        assert schema.type_ == "object"
        assert "id" in schema.properties
        assert "id" in schema.required

    def test_schema_with_defaults(self):
        """Test Schema with default values."""
        schema = Schema(name="Test", type_="string")
        assert schema.properties == {}
        assert schema.required == []


class ParameterTests:
    """Tests for Parameter dataclass."""

    def test_parameter_creation(self):
        """Test creating a Parameter object."""
        param = Parameter(
            name="id",
            in_="path",
            required=True,
            schema_={"type": "string"},
            description="User ID"
        )
        assert param.name == "id"
        assert param.in_ == "path"
        assert param.required is True


class ResponseTests:
    """Tests for Response dataclass."""

    def test_response_creation(self):
        """Test creating a Response object."""
        response = Response(
            status_code="200",
            description="Success",
            content={"application/json": {"schema": {"type": "object"}}}
        )
        assert response.status_code == "200"
        assert response.description == "Success"


class OperationTests:
    """Tests for Operation dataclass."""

    def test_operation_creation(self):
        """Test creating an Operation object."""
        op = Operation(
            path="/users",
            method="get",
            operation_id="getUsers",
            tags=["users"]
        )
        assert op.path == "/users"
        assert op.method == "get"
        assert op.tags == ["users"]

    def test_operation_defaults(self):
        """Test Operation default values."""
        op = Operation(path="/test", method="get")
        assert op.tags == []
        assert op.parameters == []
        assert op.responses == {}
