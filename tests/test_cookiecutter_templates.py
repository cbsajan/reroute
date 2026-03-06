"""
Test Cookiecutter template integration.

These tests verify that Cookiecutter templates work correctly
for project generation.
"""

import pytest
from pathlib import Path
from cookiecutter.main import cookiecutter
import tempfile
import shutil


class TestCookiecutterTemplates:
    """Test Cookiecutter template functionality."""

    def test_base_template_from_local(self, tmp_path):
        """
        Test generating a project from the base template.

        Uses the local template directory for testing.
        Marked as integration test since it generates files.
        """
        # Path to local base template
        template_path = Path(__file__).parent.parent / "reroute" / "cookiecutter-templates" / "reroute-base"

        # Skip if template doesn't exist (not yet published to GitHub)
        if not template_path.exists():
            pytest.skip("Base template not found - create GitHub repos first")

        # Generate project
        context = {
            'project_name': 'test-api',
            'description': 'Test API',
            'framework': 'fastapi',
            'host': '127.0.0.1',
            'port': 8000,
            'reload': 'true',
            'include_tests': 'Yes',
            'database': 'none',
            'package_manager': 'uv',
        }

        result = cookiecutter(
            str(template_path),
            no_input=True,
            extra_context=context,
            output_dir=str(tmp_path)
        )

        # Verify project was created
        project_dir = Path(result)
        assert project_dir.exists()
        assert project_dir.name == 'test-api'

        # Verify key files exist
        assert (project_dir / 'main.py').exists()
        assert (project_dir / 'config.py').exists()
        assert (project_dir / 'logger.py').exists()
        assert (project_dir / 'pyproject.toml').exists()
        assert (project_dir / 'requirements.txt').exists()
        assert (project_dir / '.env.example').exists()

        # Verify app structure
        assert (project_dir / 'app' / '__init__.py').exists()
        assert (project_dir / 'app' / 'routes' / '__init__.py').exists()
        assert (project_dir / 'app' / 'routes' / 'root.py').exists()
        assert (project_dir / 'app' / 'routes' / 'hello' / 'page.py').exists()

        # Verify tests directory
        assert (project_dir / 'tests' / '__init__.py').exists()
        assert (project_dir / 'tests' / 'test_main.py').exists()

    def test_base_template_with_database(self, tmp_path):
        """Test base template with PostgreSQL database."""
        template_path = Path(__file__).parent.parent / "reroute" / "cookiecutter-templates" / "reroute-base"

        if not template_path.exists():
            pytest.skip("Base template not found")

        context = {
            'project_name': 'test-db-api',
            'description': 'Test DB API',
            'framework': 'fastapi',
            'host': '127.0.0.1',
            'port': 8000,
            'reload': 'true',
            'include_tests': 'No',
            'database': 'postgresql',
            'package_manager': 'uv',
        }

        result = cookiecutter(
            str(template_path),
            no_input=True,
            extra_context=context,
            output_dir=str(tmp_path)
        )

        project_dir = Path(result)

        # Verify database files exist
        assert (project_dir / 'app' / 'database.py').exists()
        assert (project_dir / 'app' / 'db_models' / '__init__.py').exists()
        assert (project_dir / 'app' / 'db_models' / 'user.py').exists()

        # Verify tests were not created
        assert not (project_dir / 'tests').exists()

    def test_auth_template_from_local(self, tmp_path):
        """
        Test generating a project from the auth template.

        Uses the local template directory for testing.
        Marked as integration test since it generates files.
        """
        template_path = Path(__file__).parent.parent / "reroute" / "cookiecutter-templates" / "reroute-auth"

        if not template_path.exists():
            pytest.skip("Auth template not found - create GitHub repos first")

        context = {
            'project_name': 'test-auth',
            'description': 'Test Auth API',
            'framework': 'fastapi',
            'host': '127.0.0.1',
            'port': 8000,
            'reload': 'true',
            'include_tests': 'Yes',
            'database': 'postgresql',
            'package_manager': 'uv',
            'jwt_secret': 'test-secret-key',
            'jwt_algorithm': 'HS256',
            'access_token_expire_minutes': '30',
            'refresh_token_expire_days': '7',
        }

        result = cookiecutter(
            str(template_path),
            no_input=True,
            extra_context=context,
            output_dir=str(tmp_path)
        )

        project_dir = Path(result)
        assert project_dir.exists()

        # Verify auth-specific files exist
        assert (project_dir / 'app' / 'auth' / '__init__.py').exists()
        assert (project_dir / 'app' / 'auth' / 'jwt.py').exists()
        assert (project_dir / 'app' / 'auth' / 'password.py').exists()
        assert (project_dir / 'app' / 'auth' / 'models.py').exists()

        # Verify auth routes exist
        assert (project_dir / 'app' / 'routes' / 'auth' / 'login.py').exists()
        assert (project_dir / 'app' / 'routes' / 'auth' / 'register.py').exists()
        assert (project_dir / 'app' / 'routes' / 'auth' / 'refresh.py').exists()
        assert (project_dir / 'app' / 'routes' / 'auth' / 'me.py').exists()

    def test_template_content_replacement(self, tmp_path):
        """Test that template variables are properly replaced."""
        template_path = Path(__file__).parent.parent / "reroute" / "cookiecutter-templates" / "reroute-base"

        if not template_path.exists():
            pytest.skip("Base template not found")

        context = {
            'project_name': 'my-special-project',
            'description': 'My Special API',
            'framework': 'fastapi',
            'host': '0.0.0.0',
            'port': 9000,
            'reload': 'true',
            'include_tests': 'No',
            'database': 'none',
            'package_manager': 'uv',
        }

        result = cookiecutter(
            str(template_path),
            no_input=True,
            extra_context=context,
            output_dir=str(tmp_path)
        )

        project_dir = Path(result)

        # Check that project name is in files
        main_py = (project_dir / 'main.py').read_text()
        assert 'my-special-project' in main_py
        assert 'My Special API' in main_py

        config_py = (project_dir / 'config.py').read_text()
        assert 'PORT = 9000' in config_py
        assert 'HOST = "0.0.0.0"' in config_py


class TestTemplateRegistry:
    """Test template registry functionality."""

    def test_builtin_templates_registry(self):
        """Test that built-in templates are defined."""
        from reroute.cli.commands.init_command import BUILTIN_TEMPLATES

        assert isinstance(BUILTIN_TEMPLATES, dict)
        assert 'base' in BUILTIN_TEMPLATES
        assert 'auth' in BUILTIN_TEMPLATES
        assert BUILTIN_TEMPLATES['base'].startswith('gh:')
        assert BUILTIN_TEMPLATES['auth'].startswith('gh:')

    def test_template_url_format(self):
        """Test that template URLs follow expected format."""
        from reroute.cli.commands.init_command import BUILTIN_TEMPLATES

        for name, url in BUILTIN_TEMPLATES.items():
            # Should start with gh: for GitHub shorthand
            assert url.startswith('gh:'), f"Template {name} URL should start with 'gh:'"

            # Should have at least username/repo
            parts = url[3:].split('/')
            assert len(parts) >= 2, f"Template {name} URL should be format 'gh:user/repo'"


@pytest.mark.skipif(
    not (Path(__file__).parent.parent / "reroute" / "cookiecutter-templates" / "reroute-base").exists(),
    reason="Local templates not available"
)
class TestTemplateGenerationIntegration:
    """Integration tests for full template generation."""

    def test_full_project_generation(self, tmp_path):
        """
        Test complete project generation with all options.

        This is a comprehensive integration test.
        """
        template_path = Path(__file__).parent.parent / "reroute" / "cookiecutter-templates" / "reroute-base"

        context = {
            'project_name': 'full-test-project',
            'description': 'Full Test Project',
            'framework': 'fastapi',
            'host': '127.0.0.1',
            'port': 7376,
            'reload': 'true',
            'include_tests': 'Yes',
            'database': 'postgresql',
            'package_manager': 'uv',
        }

        result = cookiecutter(
            str(template_path),
            no_input=True,
            extra_context=context,
            output_dir=str(tmp_path)
        )

        project_dir = Path(result)

        # Verify all expected files and directories
        expected_files = [
            'main.py',
            'config.py',
            'logger.py',
            'pyproject.toml',
            'requirements.txt',
            '.env.example',
            'app/__init__.py',
            'app/routes/__init__.py',
            'app/routes/root.py',
            'app/routes/hello/page.py',
            'app/database.py',
            'app/db_models/__init__.py',
            'app/db_models/user.py',
            'tests/__init__.py',
            'tests/test_main.py',
        ]

        for file_path in expected_files:
            full_path = project_dir / file_path
            assert full_path.exists(), f"Expected file {file_path} not found"

        # Verify main.py is valid Python
        main_py = (project_dir / 'main.py').read_text()
        assert 'from fastapi import FastAPI' in main_py
        assert 'from reroute.adapters import FastAPIAdapter' in main_py
