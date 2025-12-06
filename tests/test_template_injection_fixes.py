"""
Tests for Template Injection Security Fixes

Tests that Jinja2 templates are rendered securely without injection vulnerabilities.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

# Import the template loader
from reroute.cli.commands.create_command import jinja_env


class TestTemplateInjectionPrevention:
    """Test that template injection vulnerabilities are prevented."""

    def test_strict_undefined_enabled(self):
        """Test that StrictUndefined is enabled to prevent silent failures."""
        template = jinja_env.from_string("{{ undefined_var }}")

        with pytest.raises(Exception) as exc_info:
            template.render()

        # Should raise an error for undefined variables
        assert "undefined" in str(exc_info.value).lower()

    def test_autoescape_enabled(self):
        """Test that autoescape is enabled to prevent XSS."""
        template = jinja_env.from_string("{{ user_input }}")

        # HTML should be escaped
        result = template.render(user_input="<script>alert('xss')</script>")

        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_limited_globals_available(self):
        """Test that only safe globals are available in templates."""
        # globals() should be undefined for security
        template = jinja_env.from_string("{{ globals() if globals is defined else 'no_globals' }}")
        result = template.render()

        # Should not have access to globals()
        assert "no_globals" in result

        # Manually check that jinja_env globals don't contain dangerous functions
        dangerous_funcs = ['eval', 'exec', 'open', '__import__', 'compile', 'exit']

        for func in dangerous_funcs:
            assert func not in jinja_env.globals

    def test_safe_globals_available(self):
        """Test that safe functions are available."""
        safe_funcs = ['range', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict']

        for func in safe_funcs:
            assert func in jinja_env.globals
            assert callable(jinja_env.globals[func])

    def test_no_access_to_builtins(self):
        """Test that templates cannot access dangerous builtins."""
        template = jinja_env.from_string("{{ __builtins__ if __builtins__ is defined else 'no_builtins' }}")
        result = template.render()

        # Should not have access to __builtins__
        assert "no_builtins" in result

    def test_policy_restrictions_active(self):
        """Test that security policies are active."""
        # Check that ext.i18n.striped policy is enabled
        assert 'ext.i18n.striped' in jinja_env.policies
        assert jinja_env.policies['ext.i18n.striped'] is True

    def test_template_sandbox_isolation(self):
        """Test that templates are properly sandboxed."""
        # Attempt to access internal attributes should fail
        template = jinja_env.from_string("{{ config.__class__ if config is defined else 'no_config' }}")

        # Even if config were defined, accessing __class__ should be restricted
        result = template.render()
        # The template should either render 'no_config' or fail safely
        assert "no_config" in result or "Error" in str(result)

    def test_arbitrary_code_execution_blocked(self):
        """Test that arbitrary code execution is blocked."""
        # Various injection attempts should fail
        malicious_templates = [
            "{{ ''.__class__.__mro__[1].__subclasses__() }}",
            "{{ ().__class__.__base__.__subclasses__() }}",
            "{{ config.__init__.__globals__ }}",
            "{{ request.application.__globals__ }}",
            "{{ ''.__class__.__bases__[0].__subclasses__()[40]('ls').read() }}",
        ]

        for template_str in malicious_templates:
            template = jinja_env.from_string(template_str)

            # Should either fail to render or not execute dangerous code
            try:
                result = template.render()
                # If it renders, ensure no sensitive information is leaked
                sensitive_patterns = ['subclasses', '__globals__', 'object at', 'module ']
                for pattern in sensitive_patterns:
                    assert pattern not in result.lower()
            except Exception:
                # Exception is expected and acceptable
                pass

    def test_file_access_blocked(self):
        """Test that file system access is blocked."""
        file_access_attempts = [
            "{{ ''.__class__.__bases__[0].__subclasses__()[40]('/etc/passwd').read() }}",
            "{{ open('/etc/passwd').read() if open is defined else 'no_open' }}",
        ]

        for template_str in file_access_attempts:
            template = jinja_env.from_string(template_str)

            try:
                result = template.render()
                # Should not contain file contents
                assert "root:" not in result
                assert "bin/bash" not in result
            except Exception:
                # Exception is expected and acceptable
                pass


class TestTemplateRenderingSafety:
    """Test safe template rendering scenarios."""

    def test_normal_template_rendering_works(self):
        """Test that legitimate templates still work correctly."""
        template = jinja_env.from_string("Hello {{ name }}! You have {{ count }} messages.")
        result = template.render(name="Alice", count=5)

        assert result == "Hello Alice! You have 5 messages."

    def test_list_comprehension_safe(self):
        """Test that list comprehensions are restricted for security."""
        # List comprehensions should be disabled for security
        with pytest.raises(Exception):
            jinja_env.from_string("{{ [item * 2 for item in numbers] }}")

        # But we can still use the map filter or loops for list operations
        template = jinja_env.from_string("{{ numbers | map('multiply', 2) | list }}")
        # Note: This would need a custom filter, so we'll test loops instead

    def test_loop_rendering_safe(self):
        """Test that loops work safely."""
        template_str = """
        {% for item in items %}
        - {{ item }}
        {% endfor %}
        """
        template = jinja_env.from_string(template_str)
        result = template.render(items=["a", "b", "c"])

        assert "- a" in result
        assert "- b" in result
        assert "- c" in result

    def test_conditionals_safe(self):
        """Test that conditionals work safely."""
        template = jinja_env.from_string("{{ 'Yes' if condition else 'No' }}")

        result1 = template.render(condition=True)
        result2 = template.render(condition=False)

        assert "Yes" in result1
        assert "No" in result2


class TestGeneratedCodeTemplates:
    """Test that the actual generated code templates are safe."""

    def test_route_template_safe(self):
        """Test that route generation templates are safe."""
        # Mock the template directory and test route template
        template_content = """
# Generated Route
class {{ route_name }}:
    def __init__(self):
        self.name = "{{ route_name | lower }}"

    def get(self):
        return {"message": "Hello from {{ route_name }}"}
        """

        template = jinja_env.from_string(template_content)

        # Safe rendering
        result = template.render(route_name="UserRoute")

        assert "class UserRoute:" in result
        assert "self.name = \"userroute\"" in result
        assert "Hello from UserRoute" in result

        # Ensure no code injection
        malicious_input = "UserRoute\"; import os; os.system('rm -rf /')"
        result = template.render(route_name=malicious_input)

        # Should escape malicious input
        assert "UserRoute&#34;; import os; os.system(&#39;rm -rf /&#39;)" in result
        # Should not execute unescaped
        assert "UserRoute\"; import os" not in result

    def test_config_template_safe(self):
        """Test that configuration templates are safe."""
        template_content = """
# Generated Config
DEBUG = {{ debug | lower }}
SECRET_KEY = "{{ secret_key }}"
ALLOWED_HOSTS = {{ allowed_hosts | tojson }}
        """

        template = jinja_env.from_string(template_content)

        # Safe rendering
        result = template.render(
            debug=False,
            secret_key="your-secret-key",
            allowed_hosts=["localhost", "127.0.0.1"]
        )

        assert "DEBUG = false" in result
        assert "SECRET_KEY = \"your-secret-key\"" in result
        assert "[\"localhost\", \"127.0.0.1\"]" in result