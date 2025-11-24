"""
Test validate decorator functionality.

Verifies that validate decorator actually performs validation.
"""

import pytest
from reroute.decorators import validate
from pydantic import BaseModel


class TestValidateDecorator:
    """Test validate decorator."""

    def test_schema_validation_success(self):
        """Test that schema validation passes with correct types."""
        @validate(schema={"name": str, "age": int, "email": str})
        def create_user(data):
            return {"created": True, "user": data}

        # Valid data
        result = create_user(data={"name": "Alice", "age": 30, "email": "alice@example.com"})
        assert result == {"created": True, "user": {"name": "Alice", "age": 30, "email": "alice@example.com"}}

    def test_schema_validation_type_error(self):
        """Test that schema validation fails with wrong types."""
        @validate(schema={"name": str, "age": int})
        def create_user(data):
            return {"created": True}

        # Invalid data - age is string instead of int
        result = create_user(data={"name": "Bob", "age": "thirty"})

        assert isinstance(result, tuple)
        response, status_code = result
        assert status_code == 400
        assert response["error"] == "Validation failed"
        assert "age" in str(response["validation_errors"])

    def test_required_fields_validation_success(self):
        """Test that required fields validation passes."""
        @validate(required_fields=["email", "password"])
        def login(data):
            return {"token": "abc123"}

        # Valid data with required fields
        result = login(data={"email": "user@example.com", "password": "secret"})
        assert result == {"token": "abc123"}

    def test_required_fields_validation_failure(self):
        """Test that required fields validation fails with missing fields."""
        @validate(required_fields=["email", "password"])
        def login(data):
            return {"token": "abc123"}

        # Missing password field
        result = login(data={"email": "user@example.com"})

        assert isinstance(result, tuple)
        response, status_code = result
        assert status_code == 400
        assert response["error"] == "Validation failed"
        assert "password" in response["missing_fields"]

    def test_custom_validator_success(self):
        """Test custom validator function."""
        def email_validator(data):
            """Validator that returns (bool, error_message)."""
            if "email" in data and "@" in data["email"]:
                return (True, None)
            return (False, "Invalid email format")

        @validate(validator_func=email_validator)
        def register(data):
            return {"registered": True}

        # Valid email
        result = register(data={"email": "valid@example.com"})
        assert result == {"registered": True}

    def test_custom_validator_failure(self):
        """Test custom validator function fails."""
        def email_validator(data):
            """Validator that returns (bool, error_message)."""
            if "email" in data and "@" in data["email"]:
                return (True, None)
            return (False, "Invalid email format")

        @validate(validator_func=email_validator)
        def register(data):
            return {"registered": True}

        # Invalid email
        result = register(data={"email": "invalid-email"})

        assert isinstance(result, tuple)
        response, status_code = result
        assert status_code == 400
        assert "Invalid email format" in response["message"]

    def test_combined_validation(self):
        """Test schema + required_fields + custom validator together."""
        def age_validator(data):
            """Check age is valid."""
            age = data.get("age", 0)
            if age < 18:
                return (False, "Must be 18 or older")
            return (True, None)

        @validate(
            schema={"name": str, "age": int, "email": str},
            required_fields=["name", "email"],
            validator_func=age_validator
        )
        def create_account(data):
            return {"account_created": True}

        # Valid data
        result = create_account(data={"name": "John", "age": 25, "email": "john@example.com"})
        assert result == {"account_created": True}

        # Missing required field
        result = create_account(data={"name": "John", "age": 25})
        assert isinstance(result, tuple)
        assert result[1] == 400

        # Wrong type
        result = create_account(data={"name": "John", "age": "25", "email": "john@example.com"})
        assert isinstance(result, tuple)
        assert result[1] == 400

        # Age too young
        result = create_account(data={"name": "Jane", "age": 16, "email": "jane@example.com"})
        assert isinstance(result, tuple)
        response, status_code = result
        assert status_code == 400
        assert "18 or older" in response["message"]

    def test_pydantic_model_extraction(self):
        """Test validation with Pydantic models."""
        class UserModel(BaseModel):
            name: str
            age: int
            email: str

        @validate(schema={"name": str, "age": int})
        def create_user(user: UserModel):
            return {"created": True, "user": user.name}

        # Pass Pydantic model
        user = UserModel(name="Alice", age=30, email="alice@example.com")
        result = create_user(user=user)
        assert result == {"created": True, "user": "Alice"}

    def test_validation_metadata(self):
        """Test that validation decorator stores metadata."""
        @validate(schema={"name": str}, required_fields=["email"])
        def test_func(data):
            return {"ok": True}

        # Check metadata
        assert hasattr(test_func, '_validation_schema')
        assert test_func._validation_schema == {"name": str}
        assert test_func._required_fields == ["email"]

    def test_validator_exception_handling(self):
        """Test that validator exceptions are caught."""
        def bad_validator(data):
            """Validator that raises exception."""
            raise ValueError("Validator crashed")

        @validate(validator_func=bad_validator)
        def create_item(data):
            return {"created": True}

        # Should handle exception gracefully
        result = create_item(data={"name": "Test"})
        assert isinstance(result, tuple)
        response, status_code = result
        assert status_code == 400
        assert "Validator crashed" in response["message"]

    def test_validation_with_method(self):
        """Test validation works with class methods."""
        class UserRoute:
            @validate(schema={"name": str, "age": int})
            def post(self, data):
                """Create user."""
                return {"created": True, "data": data}

        route = UserRoute()
        result = route.post(data={"name": "Bob", "age": 25})
        assert result == {"created": True, "data": {"name": "Bob", "age": 25}}

        # Test with wrong type
        result = route.post(data={"name": "Bob", "age": "twenty"})
        assert isinstance(result, tuple)
        assert result[1] == 400

    def test_no_validation_without_data(self):
        """Test decorator works when no data parameter provided."""
        @validate(schema={"name": str})
        def test_func():
            """Function with no data parameter."""
            return {"ok": True}

        # Should still work (no validation performed)
        result = test_func()
        assert result == {"ok": True}

    def test_custom_validator_simple_bool(self):
        """Test custom validator can return just boolean."""
        def simple_validator(data):
            """Just return bool."""
            return "email" in data

        @validate(validator_func=simple_validator)
        def test_func(data):
            return {"ok": True}

        # Should pass
        result = test_func(data={"email": "test@example.com"})
        assert result == {"ok": True}

        # Should fail
        result = test_func(data={"name": "Test"})
        assert isinstance(result, tuple)
        assert result[1] == 400

    def test_multiple_data_param_names(self):
        """Test decorator finds data under various parameter names."""
        @validate(required_fields=["name"])
        def test_with_body(body):
            return {"ok": True}

        @validate(required_fields=["name"])
        def test_with_json(json):
            return {"ok": True}

        @validate(required_fields=["name"])
        def test_with_payload(payload):
            return {"ok": True}

        # All should find data
        result1 = test_with_body(body={"name": "Test"})
        result2 = test_with_json(json={"name": "Test"})
        result3 = test_with_payload(payload={"name": "Test"})

        assert result1 == {"ok": True}
        assert result2 == {"ok": True}
        assert result3 == {"ok": True}

    def test_partial_schema_validation(self):
        """Test that schema only validates fields it knows about."""
        @validate(schema={"age": int})
        def create_user(data):
            return {"created": True}

        # Extra fields should be ignored
        result = create_user(data={"name": "Alice", "age": 30, "email": "alice@example.com"})
        assert result == {"created": True}

        # But type of specified field must match
        result = create_user(data={"name": "Alice", "age": "thirty"})
        assert isinstance(result, tuple)
        assert result[1] == 400
