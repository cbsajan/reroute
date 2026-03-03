"""
OpenAPI route generator tests.

Tests for generating REROUTE route files from OpenAPI operations.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from reroute.openapi.parser import Operation
from reroute.openapi.generator import RouteGenerator


# Fixtures
@pytest.fixture
def sample_operation():
    """Create a sample Operation object."""
    return Operation(
        path="/users",
        method="get",
        operation_id="getUsers",
        summary="List users",
        tags=["users"],
        parameters=[],
        responses={}
    )


@pytest.fixture
def operation_with_path_param():
    """Create operation with path parameter."""
    from reroute.openapi.parser import Parameter

    return Operation(
        path="/users/{id}",
        method="get",
        operation_id="getUser",
        summary="Get user",
        parameters=[
            Parameter(
                name="id",
                in_="path",
                required=True,
                schema_={"type": "string"}
            )
        ]
    )


@pytest.fixture
def route_generator(tmp_path):
    """Create a RouteGenerator with temp directory."""
    return RouteGenerator()


class RouteGeneratorInitTests:
    """Tests for RouteGenerator initialization."""

    def test_init_default_template_dir(self):
        """Test initialization with default template directory."""
        with patch('reroute.openapi.generator.jinja_env') as mock_env:
            generator = RouteGenerator()
            assert generator.env == mock_env

    def test_init_custom_template_dir(self, tmp_path):
        """Test initialization with custom template directory."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        from jinja2 import Environment, FileSystemLoader
        with patch.object(Environment, '__init__', return_value=None):
            generator = RouteGenerator(template_dir)
            assert generator.template_dir == template_dir


class GenerateRouteFileTests:
    """Tests for generate_route_file method."""

    @pytest.mark.asyncio
    async def test_generate_simple_route(self, route_generator, sample_operation, tmp_path):
        """Test generating a simple route file."""
        with patch.object(route_generator.env, 'get_template') as mock_template:
            mock_template.return_value.render.return_value = "# Generated route"

            output = route_generator.generate_route_file(
                sample_operation,
                tmp_path / "routes"
            )

            # Check template was called with correct context
            mock_template.assert_called_once_with("routes/openapi_route.py.j2")
            context = mock_template.return_value.render.call_args[1]
            assert "operation" in context
            assert "route_path" in context
            assert "class_name" in context

    def test_generate_route_creates_directory(self, route_generator, sample_operation, tmp_path):
        """Test directory creation for route file."""
        with patch.object(route_generator.env, 'get_template') as mock_template:
            mock_template.return_value.render.return_value = "# Route"

            route_generator.generate_route_file(
                sample_operation,
                tmp_path / "routes"
            )

            # Check directory was created
            output_dir = tmp_path / "routes" / "users"
            assert output_dir.exists()
            assert (output_dir / "page.py").exists()

    def test_generate_route_with_base_path(self, route_generator, tmp_path):
        """Test route generation strips base path."""
        operation = Operation(
            path="/api/v1/users",
            method="get",
            operation_id="getUsers"
        )

        with patch.object(route_generator.env, 'get_template') as mock_template:
            mock_template.return_value.render.return_value = "# Route"

            route_generator.generate_route_file(
                operation,
                tmp_path / "routes",
                base_path="/api/v1"
            )

            # Check base path was stripped
            context = mock_template.return_value.render.call_args[1]
            assert context["route_path"] == "/users"

    def test_generate_route_with_path_params(self, route_generator, operation_with_path_param, tmp_path):
        """Test route generation with path parameters."""
        with patch.object(route_generator.env, 'get_template') as mock_template:
            mock_template.return_value.render.return_value = "# Route"

            route_generator.generate_route_file(
                operation_with_path_param,
                tmp_path / "routes"
            )

            # Check directory structure
            output_dir = tmp_path / "routes" / "users" / "_id"
            assert output_dir.exists()


class GenerateCRUDRouteTests:
    """Tests for generate_crud_route method."""

    def test_generate_crud_route(self, route_generator, tmp_path):
        """Test generating CRUD route file."""
        operations = [
            Operation(path="/users", method="get", operation_id="getUsers"),
            Operation(path="/users", method="post", operation_id="createUser"),
        ]

        with patch.object(route_generator.env, 'get_template') as mock_template:
            mock_template.return_value.render.return_value = "# CRUD Route"

            output = route_generator.generate_crud_route(
                operations,
                "users",
                tmp_path / "routes"
            )

            # Check template was called
            mock_template.assert_called_once_with("routes/crud_route.py.j2")
            context = mock_template.return_value.render.call_args[1]
            assert context["resource_name"] == "users"
            assert context["get_operation"] is not None
            assert context["post_operation"] is not None

    def test_generate_crud_creates_file(self, route_generator, tmp_path):
        """Test CRUD file is created in correct location."""
        operations = [
            Operation(path="/users", method="get", operation_id="getUsers"),
        ]

        with patch.object(route_generator.env, 'get_template') as mock_template:
            mock_template.return_value.render.return_value = "# CRUD"

            route_generator.generate_crud_route(
                operations,
                "users",
                tmp_path / "routes"
            )

            output_file = tmp_path / "routes" / "users" / "page.py"
            assert output_file.exists()


class CreateFolderStructureTests:
    """Tests for create_folder_structure method."""

    def test_create_structure_single_operation(self, route_generator, sample_operation, tmp_path):
        """Test creating structure for single operation."""
        with patch.object(route_generator, 'generate_route_file', return_value="test.py"):
            generated = route_generator.create_folder_structure(
                [sample_operation],
                tmp_path / "routes"
            )

            assert len(generated) == 1
            assert "/users" in generated

    def test_create_structure_multiple_operations_same_resource(self, route_generator, tmp_path):
        """Test grouping multiple operations for same resource."""
        operations = [
            Operation(path="/users", method="get", operation_id="getUsers"),
            Operation(path="/users", method="post", operation_id="createUser"),
            Operation(path="/users", method="put", operation_id="updateUser"),
        ]

        with patch.object(route_generator, 'generate_crud_route', return_value="users/page.py"):
            generated = route_generator.create_folder_structure(
                operations,
                tmp_path / "routes"
            )

            # Should group into single CRUD file
            assert "/users" in generated
            assert len(generated["/users"]) == 1

    def test_create_structure_with_base_path(self, route_generator, tmp_path):
        """Test structure creation strips base path."""
        operations = [
            Operation(path="/api/v1/users", method="get", operation_id="getUsers"),
        ]

        with patch.object(route_generator, 'generate_route_file', return_value="test.py") as mock:
            route_generator.create_folder_structure(
                operations,
                tmp_path / "routes",
                base_path="/api/v1"
            )

            # Check base_path was passed
            call_args = mock.call_args
            assert call_args[0][0].path == "/api/v1/users"
            assert call_args[0][2] == "/api/v1"


class HelperMethodTests:
    """Tests for helper methods."""

    def test_get_file_path_from_route(self, route_generator):
        """Test converting route path to file path."""
        result = route_generator._get_file_path_from_route("/users", "get")
        assert str(result) == "users"

    def test_get_file_path_with_path_params(self, route_generator):
        """Test file path with path parameters."""
        result = route_generator._get_file_path_from_route("/users/{id}", "get")
        assert str(result) == "users/_id"

    def test_get_file_path_with_nested_params(self, route_generator):
        """Test file path with nested parameters."""
        result = route_generator._get_file_path_from_route("/users/{id}/posts/{post_id}", "get")
        assert "users" in str(result)
        assert "_id" in str(result)
        assert "_post_id" in str(result)

    def test_generate_class_name(self, route_generator, sample_operation):
        """Test class name generation."""
        name = route_generator._generate_class_name(sample_operation, "/users")
        assert name == "UsersGetRoute"

    def test_generate_class_name_with_path_param(self, route_generator, operation_with_path_param):
        """Test class name with path parameter."""
        name = route_generator._generate_class_name(operation_with_path_param, "/users/{id}")
        assert name == "UsersGetRoute"  # Parameters are stripped

    def test_generate_crud_class_name(self, route_generator):
        """Test CRUD class name generation."""
        name = route_generator._generate_crud_class_name("users")
        assert name == "UsersRoute"

    def test_extract_resource_name(self, route_generator):
        """Test resource name extraction."""
        name = route_generator._extract_resource_name("/users/{id}/posts")
        assert name == "posts"

    def test_extract_resource_name_simple(self, route_generator):
        """Test resource name from simple path."""
        name = route_generator._extract_resource_name("/users")
        assert name == "users"

    def test_group_operations_by_resource(self, route_generator):
        """Test grouping operations by resource."""
        operations = [
            Operation(path="/users", method="get", operation_id="getUsers"),
            Operation(path="/users/{id}", method="get", operation_id="getUser"),
            Operation(path="/posts", method="get", operation_id="getPosts"),
        ]

        grouped = route_generator._group_operations_by_resource(operations)

        assert "/users" in grouped
        assert "/posts" in grouped
        assert len(grouped["/users"]) == 2
        assert len(grouped["/posts"]) == 1

    def test_get_base_resource_path(self, route_generator):
        """Test getting base resource path."""
        path = route_generator._get_base_resource_path("/users/{id}/posts")
        assert path == "/users"

    def test_get_base_resource_path_no_params(self, route_generator):
        """Test base path for route without parameters."""
        path = route_generator._get_base_resource_path("/users")
        assert path == "/users"


class GenerateImportsTests:
    """Tests for generate_imports method."""

    def test_generate_imports_basic(self, route_generator, sample_operation):
        """Test generating basic imports."""
        imports = route_generator.generate_imports(sample_operation)
        assert "from reroute import RouteBase" in imports

    def test_generate_imports_with_parameters(self, route_generator):
        """Test imports with parameters."""
        from reroute.openapi.parser import Parameter

        operation = Operation(
            path="/users",
            method="get",
            parameters=[Parameter(name="id", in_="path", required=True)]
        )

        imports = route_generator.generate_imports(operation)
        assert "from reroute import Param" in imports

    def test_generate_imports_with_request_body(self, route_generator):
        """Test imports with request body."""
        operation = Operation(
            path="/users",
            method="post",
            request_body={"content": {"application/json": {"schema": {}}}}
        )

        imports = route_generator.generate_imports(operation)
        assert "from reroute import Body" in imports

    def test_generate_imports_with_responses(self, route_generator):
        """Test imports with responses."""
        from reroute.openapi.parser import Response

        operation = Operation(
            path="/users",
            method="get",
            responses={"200": Response(status_code="200", description="OK")}
        )

        imports = route_generator.generate_imports(operation)
        assert "from typing import Optional" in imports
        assert "from pydantic import BaseModel" in imports
