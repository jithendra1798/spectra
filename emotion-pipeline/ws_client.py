"""WebSocket client for SPECTRA backend (Checkpoint 3).

Sends:
  - emotion_data (Contract 1)
  - player_speech
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable, Optional

import websockets


class BackendWSClient:
    def __init__(self, base_url: str, session_id: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.session_id = session_id
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self._connected = False

    @property
    def ws_url(self) -> str:
        return f"{self.base_url}/ws/session/{self.session_id}"

    async def connect(self) -> None:
        self.ws = await websockets.connect(self.ws_url)
        self._connected = True

    async def close(self) -> None:
        if self.ws is not None:
            await self.ws.close()
            self.ws = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected and self.ws is not None

    async def send(self, payload: dict[str, Any]) -> None:
        if self.ws is None or not self._connected:
            raise RuntimeError("WebSocket not connected")
        await self.ws.send(json.dumps(payload))

    async def send_emotion_data(self, contract1: dict[str, Any]) -> None:
        await self.send({"type": "emotion_data", "data": contract1})

    async def send_player_speech(self, text: str) -> None:
        await self.send({"type": "player_speech", "text": text})

    async def recv_loop(self) -> None:
        if self.ws is None:
            raise RuntimeError("WebSocket not connected")
        async for msg in self.ws:
            print(msg)

    async def recv_loop_with_handler(self, handler: Callable[[str], None]) -> None:
        if self.ws is None:
            raise RuntimeError("WebSocket not connected")
        async for msg in self.ws:
            handler(msg)


async def _smoke_test() -> None:
    """Manual smoke test. Requires session_id env or args."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="ws://localhost:8000")
    parser.add_argument("--session-id", required=True)
    args = parser.parse_args()

    client = BackendWSClient(args.base_url, args.session_id)
    await client.connect()
    await client.send_player_speech("Hello from emotion-pipeline")
    await client.close()


if __name__ == "__main__":
    asyncio.run(_smoke_test())
