"""
oracle-brain — REST API server (FastAPI)

Exposes POST /api/oracle/respond for Component D to call.
Exposes POST /v1/chat/completions for Tavus Custom LLM integration.
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
import uuid
from pathlib import Path

import anthropic
import httpx

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


ORACLE_TAVUS_PROMPT = (
    "You are ORACLE, the AI handler for SPECTRA cyber-ops agents. "
    "You can see and hear the agent through their camera. "
    "Respond with 1-2 short, punchy tactical sentences. No markdown. No lists. "
    "Be calm, precise, and trust their judgment. "
    "Mirror their energy: slower and reassuring when they look stressed, "
    "direct and fast when they're focused."
)

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


@app.post("/v1/chat/completions")
async def tavus_llm(request: Request):
    """OpenAI-compatible endpoint — used by Tavus as a Custom LLM.

    Tavus sends the full conversation history in OpenAI message format.
    We extract the session_id embedded in the system message, optionally
    fetch current game state from the backend, then call Claude and return
    the oracle speech text in OpenAI format.
    """
    body = await request.json()
    messages = body.get("messages", [])

    # Extract system message (contains our conversational_context)
    sys_content = next((m["content"] for m in messages if m["role"] == "system"), "")
    # Session ID is embedded as [SPECTRA_SESSION:xxx]
    m = re.search(r"\[SPECTRA_SESSION:(\w+)\]", sys_content)
    session_id = m.group(1) if m else None

    # Get the last user message (player's transcribed speech)
    user_text = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"),
        "continue",
    )

    # Optionally fetch live game state for richer context
    game_context = ""
    if session_id:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{BACKEND_URL}/api/session/{session_id}/state")
                if resp.status_code == 200:
                    state = resp.json()
                    game_context = (
                        f" Current game state: phase={state['phase']}, "
                        f"time_remaining={state['time_remaining']}s, "
                        f"score={state['current_score']}."
                    )
        except Exception:
            pass  # Graceful degradation — oracle still responds without game state

    prompt = ORACLE_TAVUS_PROMPT + game_context

    if MOCK_MODE:
        oracle_text = "Copy that. I'm watching your back. Proceed with caution."
    else:
        try:
            claude = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
            result = await claude.messages.create(
                model=MODEL,
                max_tokens=100,
                system=prompt,
                messages=[{"role": "user", "content": user_text}],
            )
            oracle_text = result.content[0].text.strip()
        except Exception as e:
            logger.warning("[Tavus LLM] Claude call failed: %s", e)
            oracle_text = "Understood. Stay focused."

    logger.info("[Tavus LLM] session=%s  user=%r  oracle=%r", session_id, user_text[:50], oracle_text[:60])

    return JSONResponse({
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "model": "spectra-oracle",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": oracle_text},
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    })


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
