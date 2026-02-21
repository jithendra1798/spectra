"""
oracle-brain — WebSocket server
Receives Contract 2 JSON, returns Contract 3 JSON via Claude.
Falls back to mock data if the API call fails.

Usage:
    python claude_client.py              # starts on ws://localhost:8765
    python claude_client.py --mock       # always return mock data (no API calls)

Test with:
    python -c "
    import asyncio, websockets, json, pathlib
    async def t():
        async with websockets.connect('ws://localhost:8765') as ws:
            payload = json.loads(pathlib.Path('../mock-data/context_payload.json').read_text())
            await ws.send(json.dumps(payload))
            print(await ws.recv())
    asyncio.run(t())
    "
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import anthropic
import websockets
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# ── Config ────────────────────────────────────────────────────────────────────

HOST = "localhost"
PORT = 8765
MODEL = "claude-sonnet-4-6"

MOCK_MODE = "--mock" in sys.argv

ROOT = Path(__file__).parent
MOCK_DIR = ROOT.parent / "mock-data"

SYSTEM_PROMPT = (ROOT / "system_prompt.txt").read_text()
MOCK_RESPONSE = json.loads((MOCK_DIR / "oracle_response.json").read_text())

# ── Claude call ───────────────────────────────────────────────────────────────

def call_claude(contract2: dict) -> dict:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": json.dumps(contract2)}],
    )
    return json.loads(result.content[0].text)


# ── WebSocket handler ─────────────────────────────────────────────────────────

async def handle(websocket):
    async for raw in websocket:
        try:
            contract2 = json.loads(raw)
            print(f"[in]  phase={contract2.get('game_state', {}).get('phase', '?')}  "
                  f"player={contract2.get('player_input', '')!r}")

            if MOCK_MODE:
                response = MOCK_RESPONSE
            else:
                try:
                    response = call_claude(contract2)
                except Exception as e:
                    print(f"[warn] Claude call failed ({e}), returning mock response")
                    response = MOCK_RESPONSE

            await websocket.send(json.dumps(response, ensure_ascii=False))
            print(f"[out] voice_style={response['oracle_response']['voice_style']}  "
                  f"complexity={response['ui_commands']['complexity']}  "
                  f"guidance={response['ui_commands']['guidance_level']}")

        except Exception as e:
            error = {"error": str(e)}
            await websocket.send(json.dumps(error, ensure_ascii=False))
            print(f"[err] {e}")


# ── Entry point ───────────────────────────────────────────────────────────────

async def main():
    mode = "MOCK" if MOCK_MODE else "LIVE (Claude API)"
    print(f"ORACLE brain listening on ws://{HOST}:{PORT}  [{mode}]")
    async with websockets.serve(handle, HOST, PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
