"""
WebSocket route tests.

Tests for WebSocket connection handling, message passing,
lifecycle hooks, and connection management.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, Mock

from reroute.core.websocket import (
    WebSocketRoute,
    WebSocketConnectionManager,
    default_manager,
)


# Fixtures
@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    ws = MagicMock()
    ws.id = "test-conn-123"
    ws.send = AsyncMock()
    ws.send_json = AsyncMock()
    ws.close = AsyncMock()
    ws.accept = AsyncMock()
    return ws


@pytest.fixture
def connection_manager():
    """Create a fresh connection manager for each test."""
    return WebSocketConnectionManager()


class WebSocketRouteTests:
    """Tests for WebSocketRoute base class."""

    @pytest.mark.asyncio
    async def test_websocket_route_has_abstract_methods(self):
        """Verify WebSocketRoute defines abstract methods."""
        assert hasattr(WebSocketRoute, 'on_connect')
        assert hasattr(WebSocketRoute, 'on_message')
        assert hasattr(WebSocketRoute, 'on_disconnect')

    @pytest.mark.asyncio
    async def test_get_connection_id_with_id_attribute(self, mock_websocket):
        """Test connection ID extraction when websocket has id attribute."""
        class TestRoute(WebSocketRoute):
            async def on_connect(self, websocket): pass
            async def on_message(self, websocket, data): pass
            async def on_disconnect(self, websocket): pass

        route = TestRoute()
        conn_id = route.get_connection_id(mock_websocket)
        assert conn_id == "test-conn-123"

    @pytest.mark.asyncio
    async def test_get_connection_id_with_socket_attribute(self, mock_websocket):
        """Test connection ID extraction when websocket has socket attribute."""
        delattr(mock_websocket, 'id')
        mock_socket = MagicMock()
        mock_websocket.socket = mock_socket

        class TestRoute(WebSocketRoute):
            async def on_connect(self, websocket): pass
            async def on_message(self, websocket, data): pass
            async def on_disconnect(self, websocket): pass

        route = TestRoute()
        conn_id = route.get_connection_id(mock_websocket)
        assert conn_id == str(id(mock_socket))

    @pytest.mark.asyncio
    async def test_send_to_client_dict_message(self, mock_websocket):
        """Test sending dict message uses send_json."""
        class TestRoute(WebSocketRoute):
            async def on_connect(self, websocket): pass
            async def on_message(self, websocket, data): pass
            async def on_disconnect(self, websocket): pass

        route = TestRoute()
        await route._send_to_client(mock_websocket, {"data": "test"})

        mock_websocket.send_json.assert_called_once_with({"data": "test"})

    @pytest.mark.asyncio
    async def test_send_to_client_string_message(self, mock_websocket):
        """Test sending string message."""
        class TestRoute(WebSocketRoute):
            async def on_connect(self, websocket): pass
            async def on_message(self, websocket, data): pass
            async def on_disconnect(self, websocket): pass

        route = TestRoute()
        await route._send_to_client(mock_websocket, "test message")

        mock_websocket.send.assert_called_once_with("test message")

    @pytest.mark.asyncio
    async def test_send_to_client_bytes_message(self, mock_websocket):
        """Test sending bytes message."""
        class TestRoute(WebSocketRoute):
            async def on_connect(self, websocket): pass
            async def on_message(self, websocket, data): pass
            async def on_disconnect(self, websocket): pass

        route = TestRoute()
        await route._send_to_client(mock_websocket, b"test bytes")

        mock_websocket.send.assert_called_once_with(b"test bytes")

    @pytest.mark.asyncio
    async def test_close_connection(self, mock_websocket):
        """Test closing WebSocket connection."""
        class TestRoute(WebSocketRoute):
            async def on_connect(self, websocket): pass
            async def on_message(self, websocket, data): pass
            async def on_disconnect(self, websocket): pass

        route = TestRoute()
        route._connections["test-conn-123"] = mock_websocket
        await route.close(mock_websocket, code=1000, reason="Normal closure")

        mock_websocket.close.assert_called_once_with(1000, "Normal closure")
        assert "test-conn-123" not in route._connections

    @pytest.mark.asyncio
    async def test_on_error_default_implementation(self, mock_websocket, caplog):
        """Test default on_error implementation logs error."""
        import logging

        class TestRoute(WebSocketRoute):
            async def on_connect(self, websocket): pass
            async def on_message(self, websocket, data): pass
            async def on_disconnect(self, websocket): pass

        route = TestRoute()
        test_error = Exception("Test error")

        with caplog.at_level(logging.ERROR):
            await route.on_error(mock_websocket, test_error)

        assert "WebSocket error" in caplog.text


class WebSocketConnectionManagerTests:
    """Tests for WebSocketConnectionManager."""

    def test_manager_initialization(self, connection_manager):
        """Test manager initializes with empty structures."""
        assert len(connection_manager.active_connections) == 0
        assert len(connection_manager.groups) == 0

    @pytest.mark.asyncio
    async def test_connect_adds_connection(self, connection_manager, mock_websocket):
        """Test connecting adds websocket to active connections."""
        await connection_manager.connect(mock_websocket, "test-id")
        assert "test-id" in connection_manager.active_connections
        assert connection_manager.active_connections["test-id"] == mock_websocket

    @pytest.mark.asyncio
    async def test_connect_without_id_generates_one(self, connection_manager, mock_websocket):
        """Test connect without ID generates one from object id."""
        await connection_manager.connect(mock_websocket)
        # Should have one connection with auto-generated ID
        assert len(connection_manager.active_connections) == 1

    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(self, connection_manager, mock_websocket):
        """Test disconnect removes connection."""
        await connection_manager.connect(mock_websocket, "test-id")
        connection_manager.disconnect("test-id")
        assert "test-id" not in connection_manager.active_connections

    @pytest.mark.asyncio
    async def test_disconnect_removes_from_groups(self, connection_manager, mock_websocket):
        """Test disconnect also removes from all groups."""
        await connection_manager.connect(mock_websocket, "test-id")
        await connection_manager.join_group("test-id", "room1")
        await connection_manager.join_group("test-id", "room2")

        connection_manager.disconnect("test-id")

        assert "test-id" not in connection_manager.active_connections
        assert "test-id" not in connection_manager.groups["room1"]
        assert "test-id" not in connection_manager.groups["room2"]

    @pytest.mark.asyncio
    async def test_send_personal_message(self, connection_manager, mock_websocket):
        """Test sending message to specific connection."""
        await connection_manager.connect(mock_websocket, "test-id")
        await connection_manager.send_personal("Hello", "test-id")

        mock_websocket.send_json.assert_called_once_with("Hello")

    @pytest.mark.asyncio
    async def test_broadcast_to_all(self, connection_manager):
        """Test broadcasting message to all connections."""
        ws1 = MagicMock()
        ws1.id = "ws1"
        ws1.send_json = AsyncMock()
        ws2 = MagicMock()
        ws2.id = "ws2"
        ws2.send_json = AsyncMock()

        await connection_manager.connect(ws1, "ws1")
        await connection_manager.connect(ws2, "ws2")
        await connection_manager.broadcast({"msg": "Hello all"})

        ws1.send_json.assert_called_once_with({"msg": "Hello all"})
        ws2.send_json.assert_called_once_with({"msg": "Hello all"})

    @pytest.mark.asyncio
    async def test_broadcast_exclude_self(self, connection_manager):
        """Test broadcasting excludes specified connection."""
        ws1 = MagicMock()
        ws1.id = "ws1"
        ws1.send_json = AsyncMock()
        ws2 = MagicMock()
        ws2.id = "ws2"
        ws2.send_json = AsyncMock()

        await connection_manager.connect(ws1, "ws1")
        await connection_manager.connect(ws2, "ws2")
        await connection_manager.broadcast({"msg": "Hello"}, exclude="ws1")

        assert not ws1.send_json.called
        ws2.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_join_group(self, connection_manager, mock_websocket):
        """Test joining a group."""
        await connection_manager.connect(mock_websocket, "test-id")
        await connection_manager.join_group("test-id", "room1")

        assert "room1" in connection_manager.groups
        assert "test-id" in connection_manager.groups["room1"]

    @pytest.mark.asyncio
    async def test_leave_group(self, connection_manager, mock_websocket):
        """Test leaving a group."""
        await connection_manager.connect(mock_websocket, "test-id")
        await connection_manager.join_group("test-id", "room1")
        await connection_manager.leave_group("test-id", "room1")

        assert "test-id" not in connection_manager.groups["room1"]

    @pytest.mark.asyncio
    async def test_send_to_group(self, connection_manager):
        """Test sending message to group members."""
        ws1 = MagicMock()
        ws1.id = "ws1"
        ws1.send_json = AsyncMock()
        ws2 = MagicMock()
        ws2.id = "ws2"
        ws2.send_json = AsyncMock()
        ws3 = MagicMock()
        ws3.id = "ws3"
        ws3.send_json = AsyncMock()

        await connection_manager.connect(ws1, "ws1")
        await connection_manager.connect(ws2, "ws2")
        await connection_manager.connect(ws3, "ws3")

        await connection_manager.join_group("ws1", "room1")
        await connection_manager.join_group("ws2", "room1")
        # ws3 not in room1

        await connection_manager.send_to_group({"msg": "Room msg"}, "room1")

        ws1.send_json.assert_called_once()
        ws2.send_json.assert_called_once()
        assert not ws3.send_json.called

    @pytest.mark.asyncio
    async def test_send_to_group_creates_group_if_not_exists(self, connection_manager):
        """Test send_to_group handles non-existent groups gracefully."""
        ws1 = MagicMock()
        ws1.id = "ws1"
        ws1.send_json = AsyncMock()

        await connection_manager.connect(ws1, "ws1")
        await connection_manager.send_to_group({"msg": "Hello"}, "nonexistent")

        # Should not raise error, just do nothing
        assert not ws1.send_json.called


class WebSocketIntegrationTests:
    """Integration tests for WebSocket functionality."""

    @pytest.mark.asyncio
    async def test_broadcast_with_exclude_self(self, connection_manager):
        """Test broadcast excludes sender correctly."""
        connections = []
        for i in range(3):
            ws = MagicMock()
            ws.id = f"ws{i}"
            ws.send_json = AsyncMock()
            connections.append(ws)
            await connection_manager.connect(ws, f"ws{i}")

        # ws0 broadcasts, should not receive own message
        await connection_manager.broadcast({"msg": "test"}, exclude="ws0")

        assert not connections[0].send_json.called
        connections[1].send_json.assert_called_once()
        connections[2].send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_groups_same_connection(self, connection_manager):
        """Test connection can join multiple groups."""
        ws = MagicMock()
        ws.id = "ws1"
        ws.send_json = AsyncMock()

        await connection_manager.connect(ws, "ws1")
        await connection_manager.join_group("ws1", "room1")
        await connection_manager.join_group("ws1", "room2")

        assert "ws1" in connection_manager.groups["room1"]
        assert "ws1" in connection_manager.groups["room2"]

        # Send to room1
        await connection_manager.send_to_group({"msg": "room1"}, "room1")
        assert ws.send_json.call_count == 1

        # Send to room2
        await connection_manager.send_to_group({"msg": "room2"}, "room2")
        assert ws.send_json.call_count == 2


class DefaultManagerTests:
    """Tests for the default connection manager."""

    def test_default_manager_exists(self):
        """Test default manager instance is available."""
        assert default_manager is not None
        assert isinstance(default_manager, WebSocketConnectionManager)

    def test_default_manager_is_singleton(self):
        """Test default_manager is the same instance."""
        from reroute.core.websocket import default_manager as dm2
        assert default_manager is dm2
