"""
WebSocket Manager for real-time progress updates.
"""
from fastapi import WebSocket
from typing import Dict, List, Optional
import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.database import WebSocketConnection as WSConnectionModel

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections for real-time progress updates.

    Tracks active connections per session and broadcasts progress messages.
    Uses both in-memory storage (for fast access) and database (for cross-worker communication).
    """

    def __init__(self):
        # Dictionary mapping session_id to list of WebSocket connections (in-memory, per worker)
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Connections that have not registered a session_id yet (API Gateway flow)
        self.pending_connections: Dict[str, WebSocket] = {}
        # Map connection_id -> session_id (used for cleanup)
        self.connection_sessions: Dict[str, Optional[str]] = {}

    async def connect(self, websocket: WebSocket, session_id: Optional[str], connection_id: Optional[str] = None):
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection to register
            session_id: The session ID this connection is tracking
            connection_id: Optional unique connection ID (auto-generated if not provided)
        """
        await websocket.accept()

        if connection_id is None:
            import secrets
            connection_id = f"ws_{secrets.token_urlsafe(16)}"

        self.connection_sessions[connection_id] = session_id

        if session_id:
            if session_id not in self.active_connections:
                self.active_connections[session_id] = []

            self.active_connections[session_id].append(websocket)
            self._persist_connection(connection_id, session_id)
            logger.info(
                "WebSocket connected for session %s. Total connections: %s",
                session_id,
                len(self.active_connections[session_id]),
            )
        else:
            # Defer registration until we receive a register message
            self.pending_connections[connection_id] = websocket
            logger.info("WebSocket connected without session_id. Awaiting registration. connection_id=%s", connection_id)

        return connection_id

    async def disconnect(self, websocket: WebSocket, session_id: Optional[str], connection_id: Optional[str] = None):
        """
        Remove a WebSocket connection.

        Args:
            websocket: The WebSocket connection to remove
            session_id: The session ID this connection was tracking
            connection_id: Optional connection ID to remove from database
        """
        if connection_id and session_id is None:
            session_id = self.connection_sessions.get(connection_id)

        if session_id and session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)

            # Clean up empty session lists
            if len(self.active_connections[session_id]) == 0:
                del self.active_connections[session_id]
        
        if connection_id and connection_id in self.pending_connections:
            # Pending connection closed before registration
            self.pending_connections.pop(connection_id, None)

        # Remove connection/session mapping
        if connection_id and connection_id in self.connection_sessions:
            self.connection_sessions.pop(connection_id, None)

        # Remove from database
        if connection_id and session_id:
            db: Session = SessionLocal()
            try:
                ws_conn = db.query(WSConnectionModel).filter(
                    WSConnectionModel.connection_id == connection_id
                ).first()
                if ws_conn:
                    ws_conn.disconnected_at = datetime.utcnow()
                    db.commit()
                    logger.info(f"Marked WebSocket connection {connection_id} as disconnected")
            except Exception as e:
                logger.error(f"Failed to update WebSocket connection in database: {e}")
                db.rollback()
            finally:
                db.close()

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        Send a message to a specific WebSocket connection.

        Args:
            message: Dictionary message to send (will be converted to JSON)
            websocket: The WebSocket connection to send to
        """
        await websocket.send_text(json.dumps(message))

    def has_connection(self, session_id: str) -> bool:
        """
        Check if there are any active WebSocket connections for a session.
        Checks both in-memory connections and database.

        Args:
            session_id: The session ID to check

        Returns:
            True if there are active connections, False otherwise
        """
        # Check in-memory connections first (fast)
        if session_id in self.active_connections and len(self.active_connections[session_id]) > 0:
            return True
        
        # Check database for cross-worker connections
        # Note: This may fail if session_id doesn't exist, but we handle gracefully
        db: Session = SessionLocal()
        try:
            active_count = db.query(WSConnectionModel).filter(
                WSConnectionModel.session_id == session_id,
                WSConnectionModel.disconnected_at.is_(None)
            ).count()
            return active_count > 0
        except Exception as e:
            # Log but don't fail - return False to indicate no connection found
            logger.debug(f"Failed to check WebSocket connections in database (non-critical): {e}")
            return False
        finally:
            db.close()

    async def wait_for_connection(self, session_id: str, max_wait: float = 5.0, check_interval: float = 0.2) -> bool:
        """
        Wait for a WebSocket connection to be established for a session.
        Useful when starting agents to ensure WebSocket is ready.

        Args:
            session_id: The session ID to wait for
            max_wait: Maximum time to wait in seconds
            check_interval: Interval between checks in seconds

        Returns:
            True if connection found, False if timeout
        """
        import asyncio
        elapsed = 0.0
        while elapsed < max_wait:
            if self.has_connection(session_id):
                logger.info(f"WebSocket connection found for session {session_id} after {elapsed:.2f}s")
                return True
            await asyncio.sleep(check_interval)
            elapsed += check_interval
        
        logger.warning(f"No WebSocket connection found for session {session_id} after {max_wait}s")
        return False

    async def send_progress(self, session_id: str, message: dict):
        """
        Broadcast a progress update to all connections tracking a session.

        Args:
            session_id: The session ID to broadcast to
            message: Dictionary message to broadcast (will be converted to JSON)
        """
        # Add session_id to message if not present
        if "session_id" not in message:
            message["session_id"] = session_id

        # Send to in-memory connections (this worker)
        if session_id in self.active_connections:
            connections = self.active_connections[session_id]
            logger.info(f"Sending WebSocket message to {len(connections)} connection(s) for session {session_id}: {message.get('agentnumber', 'unknown')} - {message.get('status', 'unknown')}")
            
            # Broadcast to all connections for this session
            for connection in connections:
                try:
                    await connection.send_text(json.dumps(message))
                    logger.debug(f"Successfully sent WebSocket message to session {session_id}")
                except Exception as e:
                    # Connection might be closed, we'll remove it on disconnect
                    logger.error(f"Error sending to WebSocket for session {session_id}: {e}")
        
        # Note: We can't directly send to connections on other workers, but we log
        # that the message was sent. In a production system, you'd use Redis pub/sub
        # or similar for cross-worker messaging. For now, we rely on the connection
        # being on the same worker or retry logic.
        if session_id not in self.active_connections:
            # Check if connection exists on another worker
            if self.has_connection(session_id):
                logger.info(f"WebSocket connection exists for session {session_id} on another worker. Message logged but may not be delivered.")
            else:
                logger.warning(f"No active WebSocket connections for session {session_id}. Message not sent: {message.get('agentnumber', 'unknown')} - {message.get('status', 'unknown')}")

    async def complete_registration(self, connection_id: str, session_id: str) -> Optional[WebSocket]:
        """
        Move a pending connection into an active session once the client registers.
        """
        websocket = self.pending_connections.pop(connection_id, None)
        if not websocket:
            # Already registered or unknown connection_id
            return None

        self.connection_sessions[connection_id] = session_id

        if session_id not in self.active_connections:
            self.active_connections[session_id] = []

        self.active_connections[session_id].append(websocket)
        self._persist_connection(connection_id, session_id)
        logger.info("Registered pending connection %s for session %s", connection_id, session_id)
        return websocket

    def _persist_connection(self, connection_id: str, session_id: str) -> None:
        """
        Store connection metadata in the database (best-effort).
        """
        db: Session = SessionLocal()
        try:
            existing = db.query(WSConnectionModel).filter(
                WSConnectionModel.connection_id == connection_id
            ).first()

            if not existing:
                ws_conn = WSConnectionModel(
                    session_id=session_id,
                    connection_id=connection_id,
                    connected_at=datetime.utcnow()
                )
                db.add(ws_conn)
                db.commit()
                logger.info("Registered WebSocket connection %s for session %s in database", connection_id, session_id)
        except Exception as e:
            logger.warning("Failed to register WebSocket connection in database (non-critical): %s", e)
            db.rollback()
        finally:
            db.close()

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
