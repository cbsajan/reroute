"""
Test async handler support in FastAPI adapter.

Verifies that async route methods are properly awaited.
"""

import pytest
import asyncio
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from reroute import FastAPIAdapter, RouteBase, Config


@pytest.fixture
def temp_routes_dir(tmp_path):
    """Create a temporary routes directory for testing."""
    routes_dir = tmp_path / "routes"
    routes_dir.mkdir()
    return tmp_path


@pytest.fixture
def fastapi_app_with_adapter(temp_routes_dir):
    """Create FastAPI app with adapter using temp routes directory."""
    app = FastAPI(title="Async Test")
    adapter = FastAPIAdapter(app, app_dir=str(temp_routes_dir), config=Config)
    return app, adapter


class TestAsyncHandlers:
    """Test async handler functionality."""

    def test_async_get_handler(self, fastapi_app_with_adapter):
        """Test async GET handler is properly awaited."""
        app, adapter = fastapi_app_with_adapter

        # Create test route with async handler
        class AsyncRoute(RouteBase):
            async def get(self):
                """Async GET handler."""
                # Simulate async operation
                await asyncio.sleep(0.01)
                return {"message": "async success", "type": "async"}

        # Register route manually
        route_instance = AsyncRoute()
        adapter._register_fastapi_route(
            path="/test-async",
            method="GET",
            handler=route_instance.get,
            route_instance=route_instance
        )

        # Test the route
        client = TestClient(app)
        response = client.get("/test-async")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "async success"
        assert data["type"] == "async"

    def test_sync_get_handler(self, fastapi_app_with_adapter):
        """Test sync GET handler still works."""
        app, adapter = fastapi_app_with_adapter

        # Create test route with sync handler
        class SyncRoute(RouteBase):
            def get(self):
                """Sync GET handler."""
                return {"message": "sync success", "type": "sync"}

        # Register route manually
        route_instance = SyncRoute()
        adapter._register_fastapi_route(
            path="/test-sync",
            method="GET",
            handler=route_instance.get,
            route_instance=route_instance
        )

        # Test the route
        client = TestClient(app)
        response = client.get("/test-sync")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "sync success"
        assert data["type"] == "sync"

    def test_async_with_params(self, fastapi_app_with_adapter):
        """Test async handler with parameters."""
        from reroute.params import Query

        app, adapter = fastapi_app_with_adapter

        # Create test route with async handler and parameters
        class AsyncParamRoute(RouteBase):
            async def get(self, name: str = Query(default="World")):
                """Async GET handler with query parameter."""
                await asyncio.sleep(0.01)
                return {"greeting": f"Hello {name}", "async": True}

        # Register route manually
        route_instance = AsyncParamRoute()
        adapter._register_fastapi_route(
            path="/test-async-params",
            method="GET",
            handler=route_instance.get,
            route_instance=route_instance
        )

        # Test the route with query param
        client = TestClient(app)
        response = client.get("/test-async-params?name=Alice")

        assert response.status_code == 200
        data = response.json()
        assert data["greeting"] == "Hello Alice"
        assert data["async"] is True

        # Test with default param
        response = client.get("/test-async-params")
        assert response.status_code == 200
        data = response.json()
        assert data["greeting"] == "Hello World"

    def test_async_post_with_body(self, fastapi_app_with_adapter):
        """Test async POST handler with body."""
        from reroute.params import Body
        from pydantic import BaseModel

        class UserCreate(BaseModel):
            name: str
            email: str

        app, adapter = fastapi_app_with_adapter

        # Create test route with async POST handler
        class AsyncPostRoute(RouteBase):
            async def post(self, user: UserCreate = Body()):
                """Async POST handler with body."""
                await asyncio.sleep(0.01)
                return {
                    "created": True,
                    "user": {"name": user.name, "email": user.email},
                    "async": True
                }

        # Register route manually
        route_instance = AsyncPostRoute()
        adapter._register_fastapi_route(
            path="/test-async-post",
            method="POST",
            handler=route_instance.post,
            route_instance=route_instance
        )

        # Test the route
        client = TestClient(app)
        response = client.post(
            "/test-async-post",
            json={"name": "Bob", "email": "bob@example.com"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["created"] is True
        assert data["user"]["name"] == "Bob"
        assert data["user"]["email"] == "bob@example.com"
        assert data["async"] is True

    def test_async_lifecycle_hooks(self, fastapi_app_with_adapter):
        """Test async before_request and after_request hooks."""
        app, adapter = fastapi_app_with_adapter

        # Create test route with async hooks
        class AsyncHooksRoute(RouteBase):
            async def before_request(self):
                """Async before_request hook."""
                await asyncio.sleep(0.01)
                # Don't return anything to continue to handler
                return None

            async def get(self):
                """Async GET handler."""
                await asyncio.sleep(0.01)
                return {"message": "handler executed", "value": 42}

            async def after_request(self, response):
                """Async after_request hook."""
                await asyncio.sleep(0.01)
                # Modify response
                response["modified"] = True
                response["hook"] = "after_request"
                return response

        # Register route manually
        route_instance = AsyncHooksRoute()
        adapter._register_fastapi_route(
            path="/test-async-hooks",
            method="GET",
            handler=route_instance.get,
            route_instance=route_instance
        )

        # Test the route
        client = TestClient(app)
        response = client.get("/test-async-hooks")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "handler executed"
        assert data["value"] == 42
        assert data["modified"] is True
        assert data["hook"] == "after_request"

    def test_mixed_async_sync_hooks(self, fastapi_app_with_adapter):
        """Test mixing sync handler with async hooks."""
        app, adapter = fastapi_app_with_adapter

        # Create test route with sync handler but async hooks
        class MixedRoute(RouteBase):
            async def before_request(self):
                """Async before_request hook."""
                await asyncio.sleep(0.01)
                return None

            def get(self):
                """Sync GET handler."""
                return {"message": "sync handler", "value": 100}

            async def after_request(self, response):
                """Async after_request hook."""
                await asyncio.sleep(0.01)
                response["hooks_async"] = True
                return response

        # Register route manually
        route_instance = MixedRoute()
        adapter._register_fastapi_route(
            path="/test-mixed",
            method="GET",
            handler=route_instance.get,
            route_instance=route_instance
        )

        # Test the route
        client = TestClient(app)
        response = client.get("/test-mixed")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "sync handler"
        assert data["value"] == 100
        assert data["hooks_async"] is True

    def test_async_error_handling(self, fastapi_app_with_adapter):
        """Test async handler error handling."""
        app, adapter = fastapi_app_with_adapter

        # Create test route that raises error
        class AsyncErrorRoute(RouteBase):
            async def get(self):
                """Async GET handler that raises error."""
                await asyncio.sleep(0.01)
                raise ValueError("Test async error")

            def on_error(self, error):
                """Error handler."""
                return {"error_caught": True, "message": str(error)}

        # Register route manually
        route_instance = AsyncErrorRoute()
        adapter._register_fastapi_route(
            path="/test-async-error",
            method="GET",
            handler=route_instance.get,
            route_instance=route_instance
        )

        # Test the route
        client = TestClient(app)
        response = client.get("/test-async-error")

        assert response.status_code == 500
        data = response.json()
        assert data["error_caught"] is True
        assert "Test async error" in data["message"]
