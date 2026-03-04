"""
WebSocket route support for REROUTE.

This module provides base classes and utilities for implementing
WebSocket routes in REROUTE applications.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class WebSocketRoute(ABC):
    """Base class for WebSocket routes.

    WebSocket routes maintain persistent connections with clients
    and support bidirectional messaging.

    Example:
        ```python
        from reroute import WebSocketRoute

        class ChatWebSocket(WebSocketRoute):
            async def on_connect(self, websocket):
                await websocket.accept()
                await websocket.send_json({"message": "Connected"})

            async def on_message(self, websocket, data):
                await websocket.send_json({"echo": data})

            async def on_disconnect(self, websocket):
                pass
        ```
    """

    # Connection tracking
    _connections: Dict[str, Any] = {}

    @abstractmethod
    async def on_connect(self, websocket: Any):
        """Called when a new WebSocket connection is established.

        Args:
            websocket: The WebSocket connection object
        """
        pass

    @abstractmethod
    async def on_message(self, websocket: Any, data: Any):
        """Called when a message is received from the client.

        Args:
            websocket: The WebSocket connection object
            data: The received message data
        """
        pass

    @abstractmethod
    async def on_disconnect(self, websocket: Any):
        """Called when a WebSocket connection is closed.

        Args:
            websocket: The WebSocket connection object
        """
        pass

    async def on_error(self, websocket: Any, error: Exception):
        """Called when an error occurs on the WebSocket connection.

        Args:
            websocket: The WebSocket connection object
            error: The exception that occurred
        """
        # Default implementation: just log the error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"WebSocket error: {error}")

    def get_connection_id(self, websocket: Any) -> str:
        """Get a unique identifier for the WebSocket connection.

        Args:
            websocket: The WebSocket connection object

        Returns:
            Unique connection ID
        """
        # Try to get ID from different websocket implementations
        if hasattr(websocket, "id"):
            return str(websocket.id)
        elif hasattr(websocket, "socket"):
            return str(id(websocket.socket))
        else:
            return str(id(websocket))

    async def broadcast(self, websocket: Any, message: Any, exclude_self: bool = False):
        """Broadcast a message to all connected clients.

        Args:
            websocket: The current WebSocket connection
            message: Message to broadcast
            exclude_self: Whether to exclude the sender from the broadcast
        """
        conn_id = self.get_connection_id(websocket)

        for client_id, client in self._connections.items():
            if exclude_self and client_id == conn_id:
                continue

            try:
                await self._send_to_client(client, message)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send to client {client_id}: {e}")

    async def _send_to_client(self, websocket: Any, message: Any):
        """Send a message to a specific client.

        Args:
            websocket: The WebSocket connection
            message: Message to send
        """
        # Handle different message types
        if isinstance(message, dict):
            if hasattr(websocket, "send_json"):
                await websocket.send_json(message)
            elif hasattr(websocket, "send"):
                import json
                await websocket.send(json.dumps(message))
        elif isinstance(message, str):
            await websocket.send(message)
        elif isinstance(message, bytes):
            await websocket.send(message)
        else:
            await websocket.send(str(message))

    async def close(self, websocket: Any, code: int = 1000, reason: str = ""):
        """Close the WebSocket connection.

        Args:
            websocket: The WebSocket connection
            code: Closing status code
            reason: Closing reason
        """
        if hasattr(websocket, "close"):
            await websocket.close(code, reason)

        # Remove from connections
        conn_id = self.get_connection_id(websocket)
        if conn_id in self._connections:
            del self._connections[conn_id]


class WebSocketConnectionManager:
    """Manages WebSocket connections for broadcasting and group messaging.

    This class provides utilities for managing multiple WebSocket connections,
    including support for groups/rooms.

    Example:
        ```python
        manager = WebSocketConnectionManager()

        class ChatWebSocket(WebSocketRoute):
            async def on_connect(self, websocket):
                manager.connect(websocket)
                await websocket.accept()

            async def on_message(self, websocket, data):
                await manager.broadcast(data)
        ```
    """

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, Any] = {}
        self.groups: Dict[str, Dict[str, Any]] = {}

    async def connect(self, websocket: Any, connection_id: Optional[str] = None):
        """Add a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            connection_id: Optional custom connection ID
        """
        if connection_id is None:
            connection_id = str(id(websocket))

        self.active_connections[connection_id] = websocket

    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection.

        Args:
            connection_id: The connection ID to remove
        """
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

        # Also remove from all groups
        for group_name, group in self.groups.items():
            if connection_id in group:
                del group[connection_id]

    async def send_personal(self, message: Any, connection_id: str):
        """Send a message to a specific connection.

        Args:
            message: Message to send
            connection_id: Target connection ID
        """
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            await self._send_to_websocket(websocket, message)

    async def broadcast(self, message: Any, exclude: Optional[str] = None):
        """Broadcast a message to all active connections.

        Args:
            message: Message to broadcast
            exclude: Optional connection ID to exclude from broadcast
        """
        for conn_id, websocket in self.active_connections.items():
            if exclude and conn_id == exclude:
                continue
            await self._send_to_websocket(websocket, message)

    async def join_group(self, connection_id: str, group_name: str):
        """Add a connection to a group.

        Args:
            connection_id: The connection ID
            group_name: Name of the group to join
        """
        if group_name not in self.groups:
            self.groups[group_name] = {}

        self.groups[group_name][connection_id] = self.active_connections.get(
            connection_id
        )

    async def leave_group(self, connection_id: str, group_name: str):
        """Remove a connection from a group.

        Args:
            connection_id: The connection ID
            group_name: Name of the group to leave
        """
        if group_name in self.groups and connection_id in self.groups[group_name]:
            del self.groups[group_name][connection_id]

    async def send_to_group(self, message: Any, group_name: str):
        """Send a message to all members of a group.

        Args:
            message: Message to send
            group_name: Name of the target group
        """
        if group_name in self.groups:
            for websocket in self.groups[group_name].values():
                await self._send_to_websocket(websocket, message)

    async def _send_to_websocket(self, websocket: Any, message: Any):
        """Send a message to a WebSocket connection.

        Args:
            websocket: The WebSocket connection
            message: Message to send
        """
        try:
            if isinstance(message, dict):
                if hasattr(websocket, "send_json"):
                    await websocket.send_json(message)
                else:
                    import json
                    await websocket.send(json.dumps(message))
            elif isinstance(message, str):
                await websocket.send(message)
            elif isinstance(message, bytes):
                await websocket.send(message)
            else:
                await websocket.send(str(message))
        except Exception:
            # Connection might be closed
            pass


# Default connection manager instance
default_manager = WebSocketConnectionManager()
