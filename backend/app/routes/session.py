"""
SPECTRA Component D — REST routes for session management.

POST /api/session/create     → create a new game session
GET  /api/session/{id}/state → return current game state
POST /api/session/{id}/start → start the 5-minute timer
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import SessionCreated, SessionStarted, SessionState
from app import game_state as gsm
from app import orchestrator

logger = logging.getLogger("spectra.routes.session")

router = APIRouter(prefix="/api/session", tags=["session"])


@router.post("/create", response_model=SessionCreated)
async def create_session():
    """Create a new game session and return its ID."""
    state = await gsm.create_session()
    logger.info("REST — session created: %s", state.session_id)
    return SessionCreated(session_id=state.session_id)


@router.get("/{session_id}/state", response_model=SessionState)
async def get_session_state(session_id: str):
    """Return the current game state for a session."""
    state = await gsm.get_state(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionState(
        session_id=state.session_id,
        phase=state.phase,
        time_remaining=state.time_remaining,
        current_score=state.current_score,
        decisions_made=state.decisions_made,
        is_active=state.is_active,
    )


@router.post("/{session_id}/start", response_model=SessionStarted)
async def start_session(session_id: str):
    """Start the game timer for a session."""
    state = await gsm.get_state(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if not state.is_active:
        raise HTTPException(status_code=400, detail="Session is not active")

    await gsm.start_timer(
        session_id,
        on_tick=orchestrator.on_timer_tick,
        on_end=orchestrator.on_timer_end,
    )
    logger.info("REST — timer started for session %s", session_id)
    return SessionStarted(time_remaining=state.time_remaining)
