"""
WebSocket Test Client

Run this to test WebSocket functionality:

    python test_websocket_client.py
"""

import asyncio
import websockets
import json
from typing import Any


async def test_websocket():
    """Test WebSocket connection and messaging."""
    uri = "ws://localhost:7376/ws/chat"

    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")

            # Receive welcome message
            welcome = await websocket.recv()
            print(f"Server: {welcome}")

            # Send test messages
            messages = [
                {"type": "chat", "message": "Hello, WebSocket!"},
                {"type": "chat", "message": "Testing REROUTE"},
            ]

            for msg in messages:
                print(f"Sending: {msg}")
                await websocket.send(json.dumps(msg))

                # Receive response
                response = await websocket.recv()
                print(f"Received: {response}")

                # Wait a bit
                await asyncio.sleep(1)

            # Keep connection open to receive broadcasts
            print("\nListening for messages (Ctrl+C to stop)...")
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"Broadcast: {message}")
                except asyncio.TimeoutError:
                    print("Still connected...")

    except websockets.exceptions.ConnectionClosed:
        print("Connection closed by server")
    except ConnectionRefusedError:
        print("Error: Could not connect. Make sure the server is running:")
        print("  cd test_app")
        print("  python main.py")
    except KeyboardInterrupt:
        print("\nDisconnected by user")


async def test_multiple_clients():
    """Test multiple WebSocket clients simultaneously."""
    uri = "ws://localhost:7376/ws/chat"

    async def client(client_id: int):
        async with websockets.connect(uri) as websocket:
            # Receive welcome
            await websocket.recv()

            # Send message
            await websocket.send(json.dumps({
                "type": "chat",
                "message": f"Hello from client {client_id}"
            }))

            # Listen for a bit
            for _ in range(3):
                msg = await websocket.recv()
                print(f"Client {client_id}: {msg}")

    # Run multiple clients
    tasks = [client(i) for i in range(3)]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    print("REROUTE WebSocket Test Client")
    print("="*50)

    # Test single client
    asyncio.run(test_websocket())

    # Uncomment to test multiple clients
    # print("\n\nTesting multiple clients...")
    # asyncio.run(test_multiple_clients())
