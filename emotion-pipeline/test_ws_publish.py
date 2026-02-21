"""Test harness for WS publish (Checkpoint 3).

Usage:
  python emotion-pipeline/test_ws_publish.py --session <session_id>
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path

import httpx

from ws_client import BackendWSClient


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", default="http://localhost:8000")
    p.add_argument("--session", required=False, help="Session ID. If omitted, create one via REST.")
    return p.parse_args()


async def main() -> int:
    args = parse_args()

    session_id = args.session
    if not session_id:
        resp = httpx.post(f"{args.base_url}/api/session/create")
        resp.raise_for_status()
        session_id = resp.json()["session_id"]
        print(f"Created session: {session_id}")

    ws_base = args.base_url.replace("http://", "ws://").replace("https://", "wss://")
    client = BackendWSClient(ws_base, session_id)
    await client.connect()

    sample = json.loads(Path("mock-data/emotion_signal.json").read_text())
    sample["timestamp"] = int(time.time() * 1000)

    await client.send_emotion_data(sample)
    await client.send_player_speech("I think node A looks weakest")

    # Read a few responses then exit
    try:
        for _ in range(3):
            msg = await client.ws.recv()  # type: ignore[union-attr]
            print("WS recv:", msg)
    except Exception:
        pass

    await client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
