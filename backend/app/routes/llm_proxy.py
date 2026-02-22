"""
SPECTRA Component D — Custom LLM Proxy (stalling endpoint).

Tavus CVI in Full Pipeline mode sends /chat/completions requests to the
configured custom LLM endpoint.  Instead of returning a real LLM response
(which would make Tavus speak on its own), this endpoint **stalls** — it
holds the SSE connection open while the real orchestration happens through
the existing path:

    conversation.utterance → emotion-pipeline → backend WS → Claude →
    oracle_speech → emotion-pipeline → conversation.interrupt + echo

The interrupt cancels the pending LLM request, and the echo delivers the
actual ORACLE response to Tavus TTS.

Why not echo-only mode?
    Tavus docs: "Echo mode is not recommended if you plan to use the
    perception or speech recognition layers, as it is incompatible with
    them."  SPECTRA needs Raven-1 perception for emotion detection, so we
    must stay in Full Pipeline mode.

Why not return a real response here?
    That would duplicate the orchestration path.  By stalling, we reuse
    the existing battle-tested WebSocket pipeline and avoid double-speak.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

logger = logging.getLogger("spectra.llm_proxy")

router = APIRouter(tags=["llm-proxy"])

# Maximum time (seconds) to hold the SSE connection before giving up.
# In practice, the conversation.interrupt from the echo path will close this
# much sooner (typically 2-5 s after the user finishes speaking).
_STALL_TIMEOUT = 60

# Interval (seconds) between SSE keep-alive pings so Tavus / load balancers
# don't drop the connection for inactivity.
_PING_INTERVAL = 5


async def _stall_sse_generator():
    """Yield SSE keep-alive comments, then a minimal finish chunk."""
    start = time.monotonic()
    chunk_id = f"chatcmpl-spectra-{uuid.uuid4().hex[:12]}"
    created = int(time.time())

    logger.info("[llm-proxy] SSE stream opened  id=%s  stall_timeout=%ds", chunk_id, _STALL_TIMEOUT)

    # Keep the connection alive with SSE comments (invisible to the client
    # parser but prevent TCP / proxy timeouts).
    while (time.monotonic() - start) < _STALL_TIMEOUT:
        yield ": keep-alive\n\n"
        try:
            await asyncio.sleep(_PING_INTERVAL)
        except asyncio.CancelledError:
            # Connection was closed (e.g. Tavus received an interrupt)
            logger.info("[llm-proxy] SSE stream cancelled (interrupt received?)  id=%s  elapsed=%.1fs",
                        chunk_id, time.monotonic() - start)
            return

    # If we reach here the echo path didn't fire in time.  Return a minimal
    # response so Tavus doesn't error out.
    elapsed = time.monotonic() - start
    logger.warning("[llm-proxy] stall timeout reached (%.0fs) — sending fallback  id=%s", elapsed, chunk_id)

    # Final chunk with a brief placeholder (will be immediately overridden
    # by a subsequent echo if it arrives slightly late).
    fallback = (
        f'{{"id":"{chunk_id}","object":"chat.completion.chunk","created":{created},'
        f'"model":"spectra-oracle-proxy","choices":[{{"index":0,"delta":{{"content":"…"}},"finish_reason":null}}]}}'
    )
    yield f"data: {fallback}\n\n"

    done_chunk = (
        f'{{"id":"{chunk_id}","object":"chat.completion.chunk","created":{created},'
        f'"model":"spectra-oracle-proxy","choices":[{{"index":0,"delta":{{}},"finish_reason":"stop"}}]}}'
    )
    yield f"data: {done_chunk}\n\n"
    yield "data: [DONE]\n\n"

    logger.info("[llm-proxy] SSE stream closed (fallback sent)  id=%s", chunk_id)


@router.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """OpenAI-compatible /chat/completions — stalls until echo/interrupt.

    Tavus sends standard OpenAI chat-completion requests here.  We log the
    incoming messages (useful for debugging perception data from Raven) and
    then hold the SSE stream open.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    messages = body.get("messages", [])
    model = body.get("model", "?")

    # Log what Tavus sent us (user speech + Raven perception)
    user_msgs = [m for m in messages if m.get("role") == "user"]
    system_msgs = [m for m in messages if m.get("role") == "system"]
    last_user = user_msgs[-1]["content"][:120] if user_msgs else "(none)"

    logger.info(
        "[llm-proxy] ← Tavus  model=%s  messages=%d  system=%d  user=%d  last_user=%r",
        model, len(messages), len(system_msgs), len(user_msgs), last_user,
    )

    # Log Raven perception data if present (system messages with XML tags)
    for sm in system_msgs:
        content = sm.get("content", "")
        if "<user_emotions>" in content or "<user_appearance>" in content:
            logger.info("[llm-proxy] Raven perception: %s", content[:300])

    return StreamingResponse(
        _stall_sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )
