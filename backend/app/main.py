"""
SPECTRA Component D — FastAPI application entry point.

• Configures CORS
• Registers REST routers and WebSocket endpoint
• Manages startup / shutdown lifecycle (Redis, HTTP client)
"""

from __future__ import annotations

import json
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import EmotionSignal
from app import orchestrator
from app import redis_client
from app import ws_handler
from app.routes.session import router as session_router
from app.routes.timeline import router as timeline_router

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.DEBUG if settings.mock_mode else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("spectra.main")


# ---------------------------------------------------------------------------
# Lifespan (startup + shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- startup ----
    logger.info("=" * 60)
    logger.info("SPECTRA Component D — starting up")
    logger.info("  MOCK_MODE  = %s", settings.mock_mode)
    logger.info("  DEMO_MODE  = %s", settings.demo_mode)
    logger.info("  REDIS_URL  = %s", settings.redis_url)
    logger.info("  COMP_B_URL = %s", settings.component_b_url)
    logger.info("  CORS       = %s", settings.cors_origin_list)
    logger.info("  TIMER      = %ds", settings.effective_game_duration)
    logger.info("=" * 60)
    await redis_client.init_redis()
    await orchestrator.init_http_client()
    yield
    # ---- shutdown ----
    logger.info("Shutting down …")
    await orchestrator.close_http_client()
    await redis_client.close_redis()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="SPECTRA — Component D Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST routes
app.include_router(session_router)
app.include_router(timeline_router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "mock_mode": settings.mock_mode, "demo_mode": settings.demo_mode}


# ---------------------------------------------------------------------------
# WebSocket endpoint: /ws/session/{session_id}
# ---------------------------------------------------------------------------

@app.websocket("/ws/session/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Single WS endpoint for both Component A and Component C.

    Incoming message types:
      • emotion_data   → emotion processing pipeline
      • player_speech  → orchestration loop
    """
    await ws_handler.connect(session_id, websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON on WS from session %s", session_id)
                continue

            msg_type = msg.get("type")

            if msg_type == "emotion_data":
                try:
                    signal = EmotionSignal.model_validate(msg.get("data", {}))
                    await orchestrator.handle_emotion_data(session_id, signal)
                except Exception:
                    logger.exception("Error processing emotion_data for %s", session_id)

            elif msg_type == "player_speech":
                text = msg.get("text", "")
                if text:
                    try:
                        await orchestrator.handle_player_speech(session_id, text)
                    except Exception:
                        logger.exception("Error processing player_speech for %s", session_id)
                else:
                    logger.warning("Empty player_speech from session %s", session_id)

            else:
                logger.warning("Unknown WS message type '%s' from session %s", msg_type, session_id)

    except WebSocketDisconnect:
        logger.info("WS client disconnected from session %s", session_id)
    except Exception:
        logger.exception("WebSocket error for session %s", session_id)
    finally:
        ws_handler.disconnect(session_id, websocket)
