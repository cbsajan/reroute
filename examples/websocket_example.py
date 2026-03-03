# WebSocket Route Example
# Copy to: test_app/routes/ws/page.py

from reroute import WebSocketRoute
from reroute.core.websocket import default_manager
from typing import Dict, Any


class ChatWebSocket(WebSocketRoute):
    """WebSocket chat route for testing."""

    tag = "WebSocket"
    summary = "Real-time chat WebSocket"

    async def on_connect(self, websocket):
        """Handle new WebSocket connection."""
        await websocket.accept()
        conn_id = self.get_connection_id(websocket)

        # Add to connection manager
        await default_manager.connect(websocket, conn_id)

        # Send welcome message
        await websocket.send_json({
            "type": "system",
            "message": "Connected to chat",
            "connection_id": conn_id
        })

        # Broadcast to all users
        await default_manager.broadcast({
            "type": "system",
            "message": f"User {conn_id} joined"
        }, exclude=conn_id)

    async def on_message(self, websocket, data: Any):
        """Handle incoming message."""
        conn_id = self.get_connection_id(websocket)

        # Broadcast message to all connected users
        await default_manager.broadcast({
            "type": "chat",
            "sender": conn_id,
            "message": data
        }, exclude=conn_id)

        # Echo back to sender
        await websocket.send_json({
            "type": "echo",
            "message": data
        })

    async def on_disconnect(self, websocket):
        """Handle WebSocket disconnection."""
        conn_id = self.get_connection_id(websocket)

        # Remove from manager
        default_manager.disconnect(conn_id)

        # Notify others
        await default_manager.broadcast({
            "type": "system",
            "message": f"User {conn_id} left"
        })
