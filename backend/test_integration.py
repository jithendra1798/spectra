#!/usr/bin/env python3
"""
Quick integration test for SPECTRA Component D.
Run the server first (python run.py), then run this script.
"""

import asyncio
import json
import httpx
import websockets

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"


async def main():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # --- Health ---
        print("=" * 50)
        r = await client.get("/health")
        print(f"GET /health → {r.status_code}: {r.json()}")

        # --- Create session ---
        print("=" * 50)
        r = await client.post("/api/session/create")
        print(f"POST /api/session/create → {r.status_code}: {r.json()}")
        session_id = r.json()["session_id"]
        print(f"  session_id = {session_id}")

        # --- Get state ---
        print("=" * 50)
        r = await client.get(f"/api/session/{session_id}/state")
        print(f"GET /api/session/{session_id}/state → {r.status_code}: {json.dumps(r.json(), indent=2)}")

        # --- Start timer ---
        print("=" * 50)
        r = await client.post(f"/api/session/{session_id}/start")
        print(f"POST /api/session/{session_id}/start → {r.status_code}: {r.json()}")

        # --- WebSocket test ---
        print("=" * 50)
        print("Connecting WebSocket...")
        async with websockets.connect(f"{WS_URL}/ws/session/{session_id}") as ws:
            # Wait for a timer tick
            msg = await asyncio.wait_for(ws.recv(), timeout=3)
            print(f"  Received: {msg}")

            # Send emotion data
            emotion_msg = {
                "type": "emotion_data",
                "data": {
                    "timestamp": 1740153600000,
                    "emotions": {
                        "stress": 0.72,
                        "focus": 0.15,
                        "confusion": 0.58,
                        "confidence": 0.10,
                        "neutral": 0.05,
                    },
                    "dominant": "stress",
                    "face_detected": True,
                },
            }
            await ws.send(json.dumps(emotion_msg))
            print(f"  Sent: emotion_data (stress=0.72)")

            # Send player speech
            speech_msg = {
                "type": "player_speech",
                "text": "I think node A looks weakest",
            }
            await ws.send(json.dumps(speech_msg))
            print(f"  Sent: player_speech")

            # Receive ORACLE's responses
            responses = []
            try:
                for _ in range(5):
                    msg = await asyncio.wait_for(ws.recv(), timeout=3)
                    parsed = json.loads(msg)
                    responses.append(parsed)
                    print(f"  Received ({parsed['type']}): {json.dumps(parsed, indent=2)[:200]}")
            except asyncio.TimeoutError:
                pass

        # --- Get timeline ---
        print("=" * 50)
        r = await client.get(f"/api/timeline/{session_id}")
        print(f"GET /api/timeline/{session_id} → {r.status_code}: {len(r.json())} entries")
        if r.json():
            print(f"  First entry: {json.dumps(r.json()[0], indent=2)}")

        # --- Final state ---
        print("=" * 50)
        r = await client.get(f"/api/session/{session_id}/state")
        print(f"Final state: {json.dumps(r.json(), indent=2)}")

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
