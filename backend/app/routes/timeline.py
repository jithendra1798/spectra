"""
SPECTRA Component D — REST route for emotion timeline retrieval.

GET /api/timeline/{session_id} → full timeline array for debrief screen
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from app.models import TimelineEntry
from app import redis_client

logger = logging.getLogger("spectra.routes.timeline")

router = APIRouter(prefix="/api/timeline", tags=["timeline"])


@router.get("/{session_id}", response_model=list[TimelineEntry])
async def get_timeline(session_id: str):
    """Return the full Contract 4 emotion timeline sorted by timestamp.

    Used by Component C's debrief screen to render the emotion curve.
    """
    entries = await redis_client.get_timeline(session_id)
    logger.info("Timeline fetched for %s — %d entries", session_id, len(entries))
    return entries
