"""
SPECTRA Component D — Redis client layer.

Handles:
  • Connection pool lifecycle (startup / shutdown)
  • Game state read / write  (session:{id}:state)
  • Timeline append / read   (session:{id}:timeline)
  • Previous UI commands      (session:{id}:ui_prev)
  • TTL management
  • Graceful fallback to in-memory dicts when Redis is unavailable
"""

from __future__ import annotations

import json
import logging
from typing import Optional

import redis.asyncio as aioredis

from app.config import settings
from app.models import GameState, PreviousUIState, TimelineEntry, UICommands

logger = logging.getLogger("spectra.redis")

# ---------------------------------------------------------------------------
# In-memory fallback stores (used when Redis is down)
# ---------------------------------------------------------------------------
_mem_state: dict[str, str] = {}
_mem_timeline: dict[str, list[tuple[float, str]]] = {}
_mem_ui_prev: dict[str, str] = {}

# ---------------------------------------------------------------------------
# Module-level connection pool
# ---------------------------------------------------------------------------
_pool: Optional[aioredis.Redis] = None
_redis_available: bool = False


async def init_redis() -> None:
    """Create the async Redis connection pool. Called at FastAPI startup."""
    global _pool, _redis_available
    try:
        _pool = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=20,
        )
        await _pool.ping()
        _redis_available = True
        logger.info("Redis connected at %s", settings.redis_url)
    except Exception as exc:
        _redis_available = False
        logger.warning("Redis unavailable (%s) — falling back to in-memory storage", exc)


async def close_redis() -> None:
    """Gracefully close the connection pool. Called at FastAPI shutdown."""
    global _pool, _redis_available
    if _pool:
        await _pool.aclose()
        _pool = None
        _redis_available = False
        logger.info("Redis connection closed")


def _state_key(session_id: str) -> str:
    return f"session:{session_id}:state"


def _timeline_key(session_id: str) -> str:
    return f"session:{session_id}:timeline"


def _ui_prev_key(session_id: str) -> str:
    return f"session:{session_id}:ui_prev"


# ---------------------------------------------------------------------------
# Game State
# ---------------------------------------------------------------------------

async def save_game_state(state: GameState) -> None:
    """Persist the full game state JSON."""
    key = _state_key(state.session_id)
    payload = state.model_dump_json()
    if _redis_available and _pool:
        try:
            await _pool.set(key, payload, ex=settings.session_ttl)
            return
        except Exception as exc:
            logger.error("Redis SET failed for %s: %s", key, exc)
    # fallback
    _mem_state[key] = payload


async def load_game_state(session_id: str) -> Optional[GameState]:
    """Load game state; returns None if session doesn't exist."""
    key = _state_key(session_id)
    raw: Optional[str] = None
    if _redis_available and _pool:
        try:
            raw = await _pool.get(key)
        except Exception as exc:
            logger.error("Redis GET failed for %s: %s", key, exc)
    if raw is None:
        raw = _mem_state.get(key)
    if raw is None:
        return None
    return GameState.model_validate_json(raw)


async def delete_game_state(session_id: str) -> None:
    key = _state_key(session_id)
    if _redis_available and _pool:
        try:
            await _pool.delete(key)
        except Exception:
            pass
    _mem_state.pop(key, None)


# ---------------------------------------------------------------------------
# Timeline (Contract 4 — sorted set, score = timestamp)
# ---------------------------------------------------------------------------

async def append_timeline(session_id: str, entry: TimelineEntry) -> None:
    """Add a Contract 4 entry to the timeline sorted set."""
    key = _timeline_key(session_id)
    payload = entry.model_dump_json()
    if _redis_available and _pool:
        try:
            await _pool.zadd(key, {payload: float(entry.t)})
            await _pool.expire(key, settings.session_ttl)
            return
        except Exception as exc:
            logger.error("Redis ZADD failed for %s: %s", key, exc)
    # fallback
    _mem_timeline.setdefault(key, []).append((float(entry.t), payload))


async def get_timeline(session_id: str) -> list[TimelineEntry]:
    """Retrieve the full timeline sorted by timestamp."""
    key = _timeline_key(session_id)
    raw_entries: list[str] = []

    if _redis_available and _pool:
        try:
            raw_entries = await _pool.zrangebyscore(key, "-inf", "+inf")
        except Exception as exc:
            logger.error("Redis ZRANGEBYSCORE failed for %s: %s", key, exc)

    if not raw_entries:
        mem = _mem_timeline.get(key, [])
        mem.sort(key=lambda x: x[0])
        raw_entries = [item[1] for item in mem]

    return [TimelineEntry.model_validate_json(r) for r in raw_entries]


async def update_latest_timeline_adaptation(
    session_id: str,
    adaptation: str,
) -> None:
    """Set the `adaptation` field on the most recent timeline entry.

    This is called after an ORACLE turn to annotate which emotion reading
    triggered a UI adaptation.
    """
    key = _timeline_key(session_id)

    if _redis_available and _pool:
        try:
            # Get the latest entry (highest score)
            entries = await _pool.zrange(key, -1, -1, withscores=True)
            if not entries:
                return
            raw_json, score = entries[0]
            entry = TimelineEntry.model_validate_json(raw_json)
            # Remove old member, add updated one
            await _pool.zrem(key, raw_json)
            entry.adaptation = adaptation
            await _pool.zadd(key, {entry.model_dump_json(): score})
            return
        except Exception as exc:
            logger.error("Redis timeline adaptation update failed: %s", exc)

    # fallback
    mem = _mem_timeline.get(key, [])
    if mem:
        score, raw_json = mem[-1]
        entry = TimelineEntry.model_validate_json(raw_json)
        entry.adaptation = adaptation
        mem[-1] = (score, entry.model_dump_json())


# ---------------------------------------------------------------------------
# Previous UI Commands (for adaptation detection)
# ---------------------------------------------------------------------------

async def save_prev_ui(session_id: str, prev_state: PreviousUIState) -> None:
    key = _ui_prev_key(session_id)
    payload = prev_state.model_dump_json()
    if _redis_available and _pool:
        try:
            await _pool.set(key, payload, ex=settings.session_ttl)
            return
        except Exception as exc:
            logger.error("Redis SET failed for %s: %s", key, exc)
    _mem_ui_prev[key] = payload


async def load_prev_ui(session_id: str) -> Optional[PreviousUIState]:
    key = _ui_prev_key(session_id)
    raw: Optional[str] = None
    if _redis_available and _pool:
        try:
            raw = await _pool.get(key)
        except Exception as exc:
            logger.error("Redis GET failed for %s: %s", key, exc)
    if raw is None:
        raw = _mem_ui_prev.get(key)
    if raw is None:
        return None
    return PreviousUIState.model_validate_json(raw)


async def delete_session_keys(session_id: str) -> None:
    """Remove all Redis keys for a session (cleanup)."""
    keys = [
        _state_key(session_id),
        _timeline_key(session_id),
        _ui_prev_key(session_id),
    ]
    if _redis_available and _pool:
        try:
            await _pool.delete(*keys)
        except Exception:
            pass
    for k in keys:
        _mem_state.pop(k, None)
        _mem_timeline.pop(k, None)
        _mem_ui_prev.pop(k, None)
