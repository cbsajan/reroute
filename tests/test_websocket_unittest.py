"""
WebSocket tests using unittest (no pytest required).

Run with:
    python -m unittest tests.test_websocket_unittest
    python run_tests.py --test websocket_unittest
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from reroute.core.websocket import (
    WebSocketRoute,
    WebSocketConnectionManager,
    default_manager,
)


class TestWebSocketRoute(unittest.TestCase):
    """Tests for WebSocketRoute base class."""

    def test_websocket_route_has_abstract_methods(self):
        """Verify WebSocketRoute defines abstract methods."""
        self.assertTrue(hasattr(WebSocketRoute, 'on_connect'))
        self.assertTrue(hasattr(WebSocketRoute, 'on_message'))
        self.assertTrue(hasattr(WebSocketRoute, 'on_disconnect'))

    def test_get_connection_id_with_id_attribute(self):
        """Test connection ID extraction when websocket has id attribute."""
        class TestRoute(WebSocketRoute):
            async def on_connect(self, websocket): pass
            async def on_message(self, websocket, data): pass
            async def on_disconnect(self, websocket): pass

        route = TestRoute()
        mock_ws = MagicMock()
        mock_ws.id = "test-conn-123"

        conn_id = route.get_connection_id(mock_ws)
        self.assertEqual(conn_id, "test-conn-123")

    def test_get_connection_id_with_socket_attribute(self):
        """Test connection ID extraction when websocket has socket attribute."""
        class TestRoute(WebSocketRoute):
            async def on_connect(self, websocket): pass
            async def on_message(self, websocket, data): pass
            async def on_disconnect(self, websocket): pass

        route = TestRoute()
        mock_ws = MagicMock()
        del mock_ws.id
        mock_socket = MagicMock()
        mock_ws.socket = mock_socket

        conn_id = route.get_connection_id(mock_ws)
        self.assertEqual(conn_id, str(id(mock_socket)))

    def test_get_connection_id_fallback(self):
        """Test connection ID falls back to object id."""
        class TestRoute(WebSocketRoute):
            async def on_connect(self, websocket): pass
            async def on_message(self, websocket, data): pass
            async def on_disconnect(self, websocket): pass

        route = TestRoute()
        mock_ws = MagicMock()
        del mock_ws.id
        del mock_ws.socket

        conn_id = route.get_connection_id(mock_ws)
        self.assertEqual(conn_id, str(id(mock_ws)))


class TestWebSocketConnectionManager(unittest.TestCase):
    """Tests for WebSocketConnectionManager."""

    def setUp(self):
        """Set up fresh manager for each test."""
        self.manager = WebSocketConnectionManager()

    def test_manager_initialization(self):
        """Test manager initializes with empty structures."""
        self.assertEqual(len(self.manager.active_connections), 0)
        self.assertEqual(len(self.manager.groups), 0)

    def test_default_manager_exists(self):
        """Test default manager instance is available."""
        self.assertIsNotNone(default_manager)
        self.assertIsInstance(default_manager, WebSocketConnectionManager)

    def test_default_manager_is_singleton(self):
        """Test default_manager is the same instance."""
        from reroute.core.websocket import default_manager as dm2
        self.assertIs(default_manager, dm2)


class TestWebSocketRouteSendMethods(unittest.TestCase):
    """Tests for WebSocket send methods."""

    def setUp(self):
        """Set up test route and mock websocket."""
        class TestRoute(WebSocketRoute):
            async def on_connect(self, websocket): pass
            async def on_message(self, websocket, data): pass
            async def on_disconnect(self, websocket): pass

        self.route = TestRoute()
        self.mock_ws = MagicMock()
        self.mock_ws.send = AsyncMock()
        self.mock_ws.send_json = AsyncMock()
        self.mock_ws.close = AsyncMock()

    def test_send_to_client_dict_message(self):
        """Test sending dict message uses send_json."""
        # Note: This test requires async execution
        # For unittest without pytest-asyncio, we test the logic directly
        import asyncio

        async def run_test():
            await self.route._send_to_client(self.mock_ws, {"data": "test"})
            self.mock_ws.send_json.assert_called_once_with({"data": "test"})

        asyncio.run(run_test())

    def test_send_to_client_string_message(self):
        """Test sending string message."""
        import asyncio

        async def run_test():
            await self.route._send_to_client(self.mock_ws, "test")
            self.mock_ws.send.assert_called_once_with("test")

        asyncio.run(run_test())

    def test_close_connection(self):
        """Test closing WebSocket connection."""
        import asyncio

        async def run_test():
            # Set mock id to match the key used in _connections
            self.mock_ws.id = "test-123"
            self.route._connections["test-123"] = self.mock_ws
            await self.route.close(self.mock_ws, code=1000, reason="Closed")
            self.mock_ws.close.assert_called_once_with(1000, "Closed")
            self.assertNotIn("test-123", self.route._connections)

        asyncio.run(run_test())


class TestConnectionManagerMethods(unittest.TestCase):
    """Tests for ConnectionManager methods."""

    def setUp(self):
        """Set up manager and mocks."""
        self.manager = WebSocketConnectionManager()
        self.mock_ws = MagicMock()
        self.mock_ws.send_json = AsyncMock()
        self.mock_ws.send = AsyncMock()

    def test_connect_adds_connection(self):
        """Test connecting adds websocket."""
        import asyncio

        async def run_test():
            await self.manager.connect(self.mock_ws, "test-id")
            self.assertIn("test-id", self.manager.active_connections)
            self.assertEqual(self.manager.active_connections["test-id"], self.mock_ws)

        asyncio.run(run_test())

    def test_disconnect_removes_connection(self):
        """Test disconnect removes connection."""
        import asyncio

        async def run_test():
            await self.manager.connect(self.mock_ws, "test-id")
            self.manager.disconnect("test-id")
            self.assertNotIn("test-id", self.manager.active_connections)

        asyncio.run(run_test())

    def test_send_personal_message(self):
        """Test sending message to specific connection."""
        import asyncio

        async def run_test():
            await self.manager.connect(self.mock_ws, "test-id")
            await self.manager.send_personal({"message": "Hello"}, "test-id")
            self.mock_ws.send_json.assert_called_once_with({"message": "Hello"})

        asyncio.run(run_test())

    def test_broadcast_to_all(self):
        """Test broadcasting to all connections."""
        import asyncio

        async def run_test():
            ws1 = MagicMock()
            ws1.send_json = AsyncMock()
            ws2 = MagicMock()
            ws2.send_json = AsyncMock()

            await self.manager.connect(ws1, "ws1")
            await self.manager.connect(ws2, "ws2")
            await self.manager.broadcast({"msg": "Hello"})

            ws1.send_json.assert_called_once()
            ws2.send_json.assert_called_once()

        asyncio.run(run_test())

    def test_join_group(self):
        """Test joining a group."""
        import asyncio

        async def run_test():
            await self.manager.connect(self.mock_ws, "test-id")
            await self.manager.join_group("test-id", "room1")
            self.assertIn("room1", self.manager.groups)
            self.assertIn("test-id", self.manager.groups["room1"])

        asyncio.run(run_test())

    def test_leave_group(self):
        """Test leaving a group."""
        import asyncio

        async def run_test():
            await self.manager.connect(self.mock_ws, "test-id")
            await self.manager.join_group("test-id", "room1")
            await self.manager.leave_group("test-id", "room1")
            self.assertNotIn("test-id", self.manager.groups["room1"])

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
