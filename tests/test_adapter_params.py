"""
Unit tests for FastAPI adapter parameter extraction
"""

import pytest
import inspect
from pathlib import Path as PathType
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from reroute.params import Query, Path, Header, Body
from reroute.adapters.fastapi import FastAPIAdapter


@pytest.fixture
def temp_app_dir(tmp_path):
    """Create temporary app directory structure for testing"""
    # Create routes directory directly in tmp_path
    # Since Router looks for app_dir / ROUTES_DIR_NAME
    routes_dir = tmp_path / "routes"
    routes_dir.mkdir(parents=True)
    (routes_dir / "__init__.py").write_text("")
    return tmp_path


class MockRequest:
    """Mock FastAPI Request for testing"""
    def __init__(self, query_params=None, path_params=None, headers=None, cookies=None, body=None):
        self.query_params = query_params or {}
        self.path_params = path_params or {}
        self.headers = headers or {}
        self.cookies = cookies or {}
        self._body = body

    async def json(self):
        return self._body or {}

    async def form(self):
        return {}


@pytest.mark.asyncio
async def test_extract_query_params(temp_app_dir):
    """Test extraction of query parameters"""
    from fastapi import FastAPI
    app = FastAPI()
    adapter = FastAPIAdapter(app, app_dir=temp_app_dir)

    # Define a test handler with query parameters
    def test_handler(
        limit: int = Query(10, description="Limit"),
        offset: int = Query(0, description="Offset"),
        search: str = Query(None, description="Search")
    ):
        return {"limit": limit, "offset": offset, "search": search}

    # Create mock request
    request = MockRequest(query_params={"limit": "20", "offset": "5", "search": "test"})

    # Extract parameters
    params = await adapter._extract_request_data(request, test_handler)

    # Verify extraction
    assert params["limit"] == "20"
    assert params["offset"] == "5"
    assert params["search"] == "test"


@pytest.mark.asyncio
async def test_extract_query_params_with_defaults(temp_app_dir):
    """Test query parameters use defaults when not provided"""
    from fastapi import FastAPI
    app = FastAPI()
    adapter = FastAPIAdapter(app, app_dir=temp_app_dir)

    def test_handler(
        limit: int = Query(10, description="Limit"),
        offset: int = Query(0, description="Offset")
    ):
        return {"limit": limit, "offset": offset}

    # Create mock request with no query params
    request = MockRequest(query_params={})

    # Extract parameters
    params = await adapter._extract_request_data(request, test_handler)

    # Verify defaults are used
    assert params["limit"] == 10
    assert params["offset"] == 0


@pytest.mark.asyncio
async def test_extract_required_param_missing(temp_app_dir):
    """Test that missing required parameters raise error"""
    from fastapi import FastAPI
    app = FastAPI()
    adapter = FastAPIAdapter(app, app_dir=temp_app_dir)

    def test_handler(
        id: int = Query(..., description="Required ID")
    ):
        return {"id": id}

    # Create mock request without required param
    request = MockRequest(query_params={})

    # Should raise ValueError for missing required parameter
    with pytest.raises(ValueError, match="Required query parameter 'id' is missing"):
        await adapter._extract_request_data(request, test_handler)


@pytest.mark.asyncio
async def test_extract_header_params(temp_app_dir):
    """Test extraction of header parameters"""
    from fastapi import FastAPI
    app = FastAPI()
    adapter = FastAPIAdapter(app, app_dir=temp_app_dir)

    def test_handler(
        authorization: str = Header(..., description="Auth header"),
        user_agent: str = Header(None, description="User agent")
    ):
        return {"auth": authorization, "user_agent": user_agent}

    # Create mock request with headers
    request = MockRequest(headers={"authorization": "Bearer token123", "user-agent": "TestClient"})

    # Extract parameters
    params = await adapter._extract_request_data(request, test_handler)

    # Verify extraction
    assert params["authorization"] == "Bearer token123"
    assert params["user_agent"] == "TestClient"


@pytest.mark.asyncio
async def test_extract_path_params(temp_app_dir):
    """Test extraction of path parameters"""
    from fastapi import FastAPI
    app = FastAPI()
    adapter = FastAPIAdapter(app, app_dir=temp_app_dir)

    def test_handler(
        id: int = Path(..., description="Resource ID")
    ):
        return {"id": id}

    # Create mock request with path params
    request = MockRequest(path_params={"id": 123})

    # Extract parameters
    params = await adapter._extract_request_data(request, test_handler)

    # Verify extraction
    assert params["id"] == 123


@pytest.mark.asyncio
async def test_extract_body_params(temp_app_dir):
    """Test extraction of body parameters"""
    from fastapi import FastAPI
    from pydantic import BaseModel

    app = FastAPI()
    adapter = FastAPIAdapter(app, app_dir=temp_app_dir)

    class TestModel(BaseModel):
        name: str
        age: int

    def test_handler(
        user: TestModel = Body(..., description="User data")
    ):
        return {"user": user}

    # Create mock request with body
    request = MockRequest(body={"name": "John", "age": 30})

    # Extract parameters
    params = await adapter._extract_request_data(request, test_handler)

    # Verify extraction and Pydantic model instantiation
    assert "user" in params
    assert isinstance(params["user"], TestModel)
    assert params["user"].name == "John"
    assert params["user"].age == 30


@pytest.mark.asyncio
async def test_mixed_params(temp_app_dir):
    """Test extraction of mixed parameter types"""
    from fastapi import FastAPI
    app = FastAPI()
    adapter = FastAPIAdapter(app, app_dir=temp_app_dir)

    def test_handler(
        id: int = Path(..., description="Resource ID"),
        limit: int = Query(10, description="Limit"),
        authorization: str = Header(..., description="Auth")
    ):
        return {"id": id, "limit": limit, "auth": authorization}

    # Create mock request with all parameter types
    request = MockRequest(
        path_params={"id": 42},
        query_params={"limit": "20"},
        headers={"authorization": "Bearer xyz"}
    )

    # Extract parameters
    params = await adapter._extract_request_data(request, test_handler)

    # Verify all parameters extracted
    assert params["id"] == 42
    assert params["limit"] == "20"
    assert params["authorization"] == "Bearer xyz"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
