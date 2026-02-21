"""
SPECTRA Component D — WebSocket connection manager + message routing.

Supports multiple simultaneous connections per session (Component A + C both
connect to the same session).  Messages are broadcast to ALL connections in a
session so both components receive updates.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger("spectra.ws")

# session_id → set of active WebSocket connections
_connections: dict[str, set[WebSocket]] = {}


# ---------------------------------------------------------------------------
# Connection lifecycle
# ---------------------------------------------------------------------------

async def connect(session_id: str, ws: WebSocket) -> None:
    """Accept and register a WebSocket for the given session."""
    await ws.accept()
    _connections.setdefault(session_id, set()).add(ws)
    count = len(_connections[session_id])
    logger.info(
        "WS connected: session=%s  (total connections for session: %d)",
        session_id,
        count,
    )


def disconnect(session_id: str, ws: WebSocket) -> None:
    """Un-register a WebSocket.  Safe to call if already removed."""
    conns = _connections.get(session_id)
    if conns:
        conns.discard(ws)
        if not conns:
            del _connections[session_id]
    logger.info("WS disconnected: session=%s", session_id)


def session_has_connections(session_id: str) -> bool:
    return bool(_connections.get(session_id))


# ---------------------------------------------------------------------------
# Broadcasting
# ---------------------------------------------------------------------------

async def broadcast(session_id: str, message: dict | BaseModel) -> None:
    """Send a JSON message to every connection in a session."""
    conns = _connections.get(session_id)
    if not conns:
        return

    if isinstance(message, BaseModel):
        payload = message.model_dump_json()
    else:
        payload = json.dumps(message)

    dead: list[WebSocket] = []
    for ws in conns:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws)

    # Clean up dead sockets
    for ws in dead:
        conns.discard(ws)
        logger.warning("Removed dead WS from session %s", session_id)


async def send_to(ws: WebSocket, message: dict | BaseModel) -> None:
    """Send a message to a single WebSocket (not broadcast)."""
    if isinstance(message, BaseModel):
        payload = message.model_dump_json()
    else:
        payload = json.dumps(message)
    await ws.send_text(payload)


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

async def close_all(session_id: str) -> None:
    """Force-close all WebSocket connections for a session."""
    conns = _connections.pop(session_id, set())
    for ws in conns:
        try:
            await ws.close()
        except Exception:
            pass
    logger.info("Closed all WS connections for session %s", session_id)
