"""
oracle-brain — REST API server (FastAPI)

Exposes POST /api/oracle/respond for Component D to call.
Accepts Contract 2 JSON, returns Contract 3 JSON via Claude.

Usage:
    python run.py                    # live mode (calls Claude API)
    MOCK_MODE=true python run.py     # mock mode (returns canned response)
"""

import json
import logging
import os
import re
import sys
from pathlib import Path

import anthropic

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# ── Config ────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent
MOCK_DIR = ROOT.parent / "mock-data"

SYSTEM_PROMPT = (ROOT / "system_prompt.txt").read_text()
MOCK_RESPONSE = json.loads((MOCK_DIR / "oracle_response.json").read_text())

MOCK_MODE = os.environ.get("MOCK_MODE", "false").lower() in ("true", "1", "yes")

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("ORACLE_PORT", "8001"))
MODEL = os.environ.get("ORACLE_MODEL", "claude-sonnet-4-6")

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("oracle-brain")

# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_json(text: str) -> dict:
    """Parse JSON from Claude's response, stripping markdown code fences if present."""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if m:
        text = m.group(1).strip()
    return json.loads(text)


# ── Claude call ───────────────────────────────────────────────────────────────

async def call_claude(contract2: dict) -> dict:
    """Send Contract 2 to Claude and parse Contract 3 response (async, non-blocking)."""
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = await client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": json.dumps(contract2)}],
    )
    return _extract_json(result.content[0].text)


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(title="SPECTRA — Oracle Brain (Component B)", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "ok", "mock_mode": MOCK_MODE, "model": MODEL}


@app.post("/api/oracle/respond")
async def oracle_respond(request: Request):
    """Receive Contract 2, return Contract 3."""
    contract2 = await request.json()

    phase = contract2.get("game_state", {}).get("phase", "?")
    player_input = contract2.get("player_input", "")
    logger.info("[in]  phase=%s  player=%r", phase, player_input)

    if MOCK_MODE:
        response = MOCK_RESPONSE
        logger.info("[out] MOCK mode — returning canned response")
    else:
        try:
            response = await call_claude(contract2)
        except Exception as e:
            logger.warning("[warn] Claude call failed (%s), returning mock response", e)
            response = MOCK_RESPONSE

    logger.info(
        "[out] voice_style=%s  complexity=%s  guidance=%s  score_delta=%s",
        response.get("oracle_response", {}).get("voice_style", "?"),
        response.get("ui_commands", {}).get("complexity", "?"),
        response.get("ui_commands", {}).get("guidance_level", "?"),
        response.get("game_update", {}).get("score_delta", "?"),
    )

    return JSONResponse(content=response)
