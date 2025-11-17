"""
WebSocket Manager for real-time progress updates.
"""
from fastapi import WebSocket
from typing import Dict, List
import json


class WebSocketManager:
    """
    Manages WebSocket connections for real-time progress updates.

    Tracks active connections per session and broadcasts progress messages.
    """

    def __init__(self):
        # Dictionary mapping session_id to list of WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection to register
            session_id: The session ID this connection is tracking
        """
        await websocket.accept()

        if session_id not in self.active_connections:
            self.active_connections[session_id] = []

        self.active_connections[session_id].append(websocket)

    async def disconnect(self, websocket: WebSocket, session_id: str):
        """
        Remove a WebSocket connection.

        Args:
            websocket: The WebSocket connection to remove
            session_id: The session ID this connection was tracking
        """
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)

            # Clean up empty session lists
            if len(self.active_connections[session_id]) == 0:
                del self.active_connections[session_id]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        Send a message to a specific WebSocket connection.

        Args:
            message: Dictionary message to send (will be converted to JSON)
            websocket: The WebSocket connection to send to
        """
        await websocket.send_text(json.dumps(message))

    async def send_progress(self, session_id: str, message: dict):
        """
        Broadcast a progress update to all connections tracking a session.

        Args:
            session_id: The session ID to broadcast to
            message: Dictionary message to broadcast (will be converted to JSON)
        """
        if session_id in self.active_connections:
            # Add session_id to message if not present
            if "session_id" not in message:
                message["session_id"] = session_id

            # Broadcast to all connections for this session
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    # Connection might be closed, we'll remove it on disconnect
                    print(f"Error sending to WebSocket: {e}")

    async def broadcast_status(self, session_id: str, status: str, progress: int = 0, details: str = "", elapsed_time: float = None, total_cost: float = None, items: list = None):
        """
        Helper method to broadcast a standardized status update.

        Args:
            session_id: The session ID to broadcast to
            status: Status string (e.g., "generating_images", "completed")
            progress: Progress percentage (0-100)
            details: Additional details about the status
            elapsed_time: Optional elapsed time in seconds
            total_cost: Optional total cost in USD
            items: Optional list of status items showing cumulative progress
                   Format: [{"id": str, "name": str, "status": "pending"|"processing"|"completed", "type": "image"|"audio"}]
        """
        message = {
            "type": "status_update",
            "status": status,
            "progress": progress,
            "details": details
        }

        if elapsed_time is not None:
            message["elapsed_time"] = round(elapsed_time, 1)

        if total_cost is not None:
            message["total_cost"] = round(total_cost, 4)

        if items is not None:
            message["items"] = items

        await self.send_progress(session_id, message)
