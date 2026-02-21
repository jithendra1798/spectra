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


async def create_conversation(session_id: str) -> tuple[Optional[str], Optional[str]]:
    """Create a new Tavus conversation and return (url, conversation_id).

    Returns (None, None) if the API key is not configured or the call fails.
    """
    if not settings.tavus_api_key:
        logger.warning("TAVUS_API_KEY not set — skipping conversation creation")
        return None, None

    payload = {
        "replica_id": settings.tavus_replica_id,
        "conversation_name": f"SPECTRA_{session_id}",
        "conversational_context": (
            f"[SPECTRA_SESSION:{session_id}] "
            "You are ORACLE, an adaptive AI partner inside SPECTRA — a real-time cyber mission. "
            "You are calm, competent, and trust the player's judgment. "
            "You adapt your tone: slower and reassuring when the player looks stressed, "
            "direct and fast when they're focused. Never condescending. "
            "Keep responses concise — 1-2 sentences max. "
            "When the player joins, greet them immediately with the mission briefing."
        ),
        "properties": {
            "enable_transcription": True,
            "participant_left_timeout": 60,
            "participant_absent_timeout": 30,
        },
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
            conv_id = data.get("conversation_id")
            logger.info(
                "Tavus conversation created: id=%s  url=%s  session=%s",
                conv_id,
                url,
                session_id,
            )
            return url, conv_id
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Tavus API error %s: %s — session=%s",
            exc.response.status_code,
            exc.response.text[:200],
            session_id,
        )
    except Exception:
        logger.exception("Failed to create Tavus conversation for session %s", session_id)

    return None, None


async def update_persona_llm(persona_id: str, oracle_base_url: str) -> bool:
    """Patch a Tavus persona to use our oracle-brain as the custom LLM.

    Call this once before a demo when oracle-brain is reachable at a public URL
    (e.g. via ngrok).  The URL should be the root of oracle-brain — Tavus will
    append /chat/completions internally.

    Args:
        persona_id: Tavus persona ID (from settings.tavus_persona_id)
        oracle_base_url: Public base URL of oracle-brain, e.g.
                         "https://abc123.ngrok-free.app"
    """
    if not settings.tavus_api_key:
        logger.warning("TAVUS_API_KEY not set — skipping persona LLM update")
        return False

    payload = {
        "layers": {
            "llm": {
                "model": "spectra-oracle",
                "base_url": oracle_base_url.rstrip("/") + "/v1",
                "api_key": "spectra-oracle-key",
            }
        }
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.patch(
                f"{TAVUS_API}/personas/{persona_id}",
                json=payload,
                headers={"x-api-key": settings.tavus_api_key},
            )
            if resp.status_code in (200, 204):
                logger.info(
                    "Tavus persona %s updated with custom LLM → %s",
                    persona_id,
                    oracle_base_url,
                )
                return True
            logger.error(
                "Tavus persona update failed %s: %s",
                resp.status_code,
                resp.text[:200],
            )
    except Exception:
        logger.exception("Failed to update Tavus persona %s", persona_id)

    return False


async def echo_conversation(conversation_id: str, text: str) -> bool:
    """Make the Tavus avatar speak `text` in the active conversation.

    Uses the /echo endpoint which injects speech directly into the live call.
    Returns True on success, False otherwise.
    """
    if not settings.tavus_api_key or not conversation_id:
        return False
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{TAVUS_API}/conversations/{conversation_id}/echo",
                json={"message": text},
                headers={"x-api-key": settings.tavus_api_key},
            )
            resp.raise_for_status()
            logger.info("Tavus echo sent to conv=%s  text=%r", conversation_id, text[:60])
            return True
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "Tavus echo failed %s for conv=%s: %s",
            exc.response.status_code,
            conversation_id,
            exc.response.text[:120],
        )
    except Exception:
        logger.exception("Tavus echo error for conv=%s", conversation_id)
    return False
