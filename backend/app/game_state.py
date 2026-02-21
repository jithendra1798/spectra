"""
SPECTRA Component D — Game state manager.

Manages per-session state:
  • Session creation and initialisation
  • Phase transitions  (infiltrate → vault → escape → debrief)
  • Score updates
  • Conversation history
  • Timer lifecycle (async background task per session)
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Optional

from app.config import settings
from app.models import ConversationEntry, GameState, GameUpdate, Phase
from app import redis_client

logger = logging.getLogger("spectra.game")

# Phase ordering for transitions
PHASE_ORDER: list[Phase] = [Phase.infiltrate, Phase.vault, Phase.escape, Phase.debrief]

# Keeps track of running timer tasks so they can be cancelled on session end
_timer_tasks: dict[str, asyncio.Task] = {}


# ---------------------------------------------------------------------------
# Session CRUD
# ---------------------------------------------------------------------------

async def create_session() -> GameState:
    """Create a new session with a unique ID and persist to Redis."""
    session_id = uuid.uuid4().hex[:12]
    state = GameState(
        session_id=session_id,
        time_remaining=settings.effective_game_duration,
    )
    await redis_client.save_game_state(state)
    logger.info("Session created: %s (duration=%ds)", session_id, state.time_remaining)
    return state


async def get_state(session_id: str) -> Optional[GameState]:
    return await redis_client.load_game_state(session_id)


async def save_state(state: GameState) -> None:
    await redis_client.save_game_state(state)


# ---------------------------------------------------------------------------
# Phase transitions
# ---------------------------------------------------------------------------

def next_phase(current: Phase) -> Phase:
    """Return the phase that follows `current`, or debrief if at end."""
    idx = PHASE_ORDER.index(current)
    if idx + 1 < len(PHASE_ORDER):
        return PHASE_ORDER[idx + 1]
    return Phase.debrief


def advance_phase(state: GameState) -> Phase:
    """Advance the game to the next phase, reset conversation history."""
    state.phase = next_phase(state.phase)
    state.conversation_history = []
    logger.info("Session %s advanced to phase: %s", state.session_id, state.phase.value)
    if state.phase == Phase.debrief:
        state.is_active = False
    return state.phase


# ---------------------------------------------------------------------------
# Score & history helpers
# ---------------------------------------------------------------------------

def apply_game_update(state: GameState, update: GameUpdate) -> bool:
    """Apply score_delta and advance_phase from Contract 3.

    Returns True if the phase was advanced.
    """
    state.current_score += update.score_delta
    state.decisions_made += 1

    phase_advanced = False
    if update.advance_phase:
        advance_phase(state)
        phase_advanced = True

    return phase_advanced


def add_to_history(state: GameState, role: str, text: str) -> None:
    state.conversation_history.append(ConversationEntry(role=role, text=text))


# ---------------------------------------------------------------------------
# Timer
# ---------------------------------------------------------------------------

async def start_timer(
    session_id: str,
    on_tick,
    on_end,
) -> None:
    """Start a per-session background timer.

    Args:
        session_id: the session to time.
        on_tick: async callback(session_id, time_remaining) called every second.
        on_end: async callback(session_id) called when timer hits 0.
    """
    if session_id in _timer_tasks:
        logger.warning("Timer already running for session %s", session_id)
        return

    async def _run() -> None:
        logger.info("Timer started for session %s", session_id)
        try:
            while True:
                await asyncio.sleep(1)
                state = await get_state(session_id)
                if state is None or not state.is_active:
                    break
                state.time_remaining = max(0, state.time_remaining - 1)
                await save_state(state)
                await on_tick(session_id, state.time_remaining)
                if state.time_remaining <= 0:
                    state.is_active = False
                    await save_state(state)
                    await on_end(session_id)
                    break
        except asyncio.CancelledError:
            logger.info("Timer cancelled for session %s", session_id)
        except Exception:
            logger.exception("Timer error for session %s", session_id)
        finally:
            _timer_tasks.pop(session_id, None)

    _timer_tasks[session_id] = asyncio.create_task(_run())


async def stop_timer(session_id: str) -> None:
    """Cancel the timer for a session if running."""
    task = _timer_tasks.pop(session_id, None)
    if task and not task.done():
        task.cancel()
        logger.info("Timer stopped for session %s", session_id)
