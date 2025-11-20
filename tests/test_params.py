"""
Unit tests for parameter injection system
"""

import pytest
from reroute.params import Query, Path, Header, Body, Cookie, Form, File, ParamBase


def test_query_param_creation():
    """Test Query parameter instantiation"""
    param = Query(10, description="Test parameter", ge=0, le=100)
    assert param.default == 10
    assert param.description == "Test parameter"
    assert param.ge == 0
    assert param.le == 100
    assert not param.required


def test_query_param_required():
    """Test required Query parameter"""
    param = Query(..., description="Required parameter")
    assert param.default is ...
    assert param.required is True


def test_header_param():
    """Test Header parameter"""
    param = Header(..., description="Authorization header")
    assert isinstance(param, ParamBase)
    assert param.required is True


def test_body_param():
    """Test Body parameter with embed"""
    param = Body(..., embed=True, media_type="application/json")
    assert param.embed is True
    assert param.media_type == "application/json"


def test_path_param():
    """Test Path parameter"""
    param = Path(..., description="Resource ID", gt=0)
    assert param.gt == 0
    assert param.required is True


def test_param_validation_fields():
    """Test parameter validation fields"""
    param = Query(
        None,
        description="Test",
        min_length=5,
        max_length=50,
        regex=r"^\w+$",
        example="test_value"
    )
    assert param.min_length == 5
    assert param.max_length == 50
    assert param.regex == r"^\w+$"
    assert param.example == "test_value"


def test_cookie_param():
    """Test Cookie parameter"""
    param = Cookie("default_value", description="Session cookie")
    assert param.default == "default_value"
    assert not param.required


def test_form_param():
    """Test Form parameter"""
    param = Form(..., description="Form field")
    assert param.required is True


def test_file_param():
    """Test File parameter"""
    param = File(..., description="Upload file")
    assert param.required is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
