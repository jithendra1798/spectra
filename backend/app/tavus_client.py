"""
SPECTRA — Tavus CVI client.

Creates a fresh conversation for each game session so the Daily.co
meeting URL is never stale.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger("spectra.tavus")

TAVUS_API = "https://tavusapi.com/v2"


async def create_conversation(session_id: str) -> Optional[str]:
    """Create a new Tavus conversation and return its URL.

    Returns None if the API key is not configured or the call fails.
    """
    if not settings.tavus_api_key:
        logger.warning("TAVUS_API_KEY not set — skipping conversation creation")
        return None

    payload = {
        "persona_id": settings.tavus_persona_id,
        "replica_id": settings.tavus_replica_id,
        "conversation_name": f"SPECTRA_{session_id}",
        "conversational_context": (
            "You are ORACLE, tactical AI for mission SPECTRA. "
            "When the agent joins, greet them as 'Agent' and brief them in 3-4 sentences: "
            "Phase 1 — Infiltrate: breach the target network node. "
            "Phase 2 — Vault: decrypt the cipher fragments before the window closes. "
            "Phase 3 — Escape: choose an exit route under time pressure. "
            "Tell them you will monitor their stress and focus throughout, adapting the interface to their cognitive state. "
            "End with: 'When you are ready, hit the button below and your mission begins. Good luck, Agent.'"
        ),
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{TAVUS_API}/conversations",
                json=payload,
                headers={"x-api-key": settings.tavus_api_key},
            )
            resp.raise_for_status()
            data = resp.json()
            url = data.get("conversation_url")
            logger.info(
                "Tavus conversation created: id=%s  url=%s  session=%s",
                data.get("conversation_id"),
                url,
                session_id,
            )
            return url
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Tavus API error %s: %s — session=%s",
            exc.response.status_code,
            exc.response.text[:200],
            session_id,
        )
    except Exception:
        logger.exception("Failed to create Tavus conversation for session %s", session_id)

    return None
