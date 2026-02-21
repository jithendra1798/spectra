"""
SPECTRA Component D — Main orchestration loop.

This module ties everything together:
  1. Emotion data  → buffer / trend / timeline (Contract 4)
  2. Player speech → build Contract 2 → call Component B → parse Contract 3
     → apply game updates → detect adaptation → broadcast WS messages
  3. Mock mode for testing without Component B
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Optional

import httpx

from app.config import settings
from app.emotion_processor import EmotionProcessor
from app import tavus_client as tavus
from app.models import (
    Complexity,
    EmotionSignal,
    EmotionSnapshot,
    GameState,
    GameStateSnapshot,
    GameUpdate,
    OracleContext,
    OracleResponse,
    OracleResponseContent,
    Phase,
    PreviousUIState,
    UICommands,
    VoiceStyle,
    WSGameEnd,
    WSOracleSpeech,
    WSPhaseChange,
    WSUIUpdate,
)
from app import game_state as gsm
from app import redis_client
from app import ws_handler

logger = logging.getLogger("spectra.orchestrator")

# Async HTTP client — reused across requests
_http_client: Optional[httpx.AsyncClient] = None


async def init_http_client() -> None:
    global _http_client
    _http_client = httpx.AsyncClient(timeout=30.0)
    logger.info("HTTP client initialised")


async def close_http_client() -> None:
    global _http_client
    if _http_client:
        await _http_client.aclose()
        _http_client = None
        logger.info("HTTP client closed")


# ---------------------------------------------------------------------------
# Mock Contract 3 responses (alternates stressed / focused)
# ---------------------------------------------------------------------------
_mock_counter: int = 0


def _mock_oracle_response() -> OracleResponse:
    """Return alternating mock responses for testing without Component B."""
    global _mock_counter
    _mock_counter += 1

    if _mock_counter % 2 == 0:
        return OracleResponse(
            oracle_response=OracleResponseContent(
                text="I see you're feeling the pressure. Let's simplify — focus on the two strongest options.",
                voice_style=VoiceStyle.calm_reassuring,
            ),
            ui_commands=UICommands(
                complexity=Complexity.simplified,
                color_mood="calm",
                panels_visible=["main"],
                options=[
                    {"id": "A", "label": "Option A", "highlighted": True},
                    {"id": "B", "label": "Option B", "highlighted": False},
                ],
                guidance_level="high",
            ),
            game_update=GameUpdate(score_delta=5, advance_phase=False),
        )
    else:
        return OracleResponse(
            oracle_response=OracleResponseContent(
                text="Good instinct. You're locked in. Here's the full picture.",
                voice_style=VoiceStyle.direct_fast,
            ),
            ui_commands=UICommands(
                complexity=Complexity.full,
                color_mood="intense",
                panels_visible=["main", "stats", "radar", "comms"],
                options=[
                    {"id": "A", "label": "Node A", "highlighted": False},
                    {"id": "B", "label": "Node B", "highlighted": False},
                    {"id": "C", "label": "Node C", "highlighted": True},
                ],
                guidance_level="none",
            ),
            game_update=GameUpdate(score_delta=10, advance_phase=False),
        )


# ---------------------------------------------------------------------------
# Fallback Contract 3 (when Component B is unreachable)
# ---------------------------------------------------------------------------

def _fallback_oracle_response() -> OracleResponse:
    return OracleResponse(
        oracle_response=OracleResponseContent(
            text="Hold on, recalibrating...",
            voice_style=VoiceStyle.neutral,
        ),
        ui_commands=UICommands(),  # defaults — no changes
        game_update=GameUpdate(),
    )


# ---------------------------------------------------------------------------
# Handle incoming emotion data
# ---------------------------------------------------------------------------

async def handle_emotion_data(session_id: str, signal: EmotionSignal) -> None:
    """Process a Contract 1 emotion reading.

    1. Push to buffer
    2. Build a Contract 4 timeline entry and store in Redis
    3. Derive UI from emotion and broadcast ui_update if it changed
    4. Save updated state
    """
    ts_start = time.monotonic()

    state = await gsm.get_state(session_id)
    if state is None or not state.is_active:
        return

    # 1 — update buffer
    EmotionProcessor.push_to_buffer(state, signal)

    # 2 — Contract 4 timeline entry
    entry = EmotionProcessor.build_timeline_entry(signal, state.phase)
    await redis_client.append_timeline(session_id, entry)

    # 3 — derive UI from emotion and broadcast if it changed
    prev_ui = await redis_client.load_prev_ui(session_id)
    current_ui = prev_ui.ui_commands if prev_ui else UICommands()
    derived_ui = EmotionProcessor.derive_ui_from_emotion(signal, current_ui)

    if derived_ui.complexity != current_ui.complexity or derived_ui.color_mood != current_ui.color_mood:
        logger.info(
            "[emotion→UI] session=%s  stress=%.2f  focus=%.2f  complexity=%s→%s  mood=%s→%s",
            session_id,
            signal.emotions.stress,
            signal.emotions.focus,
            current_ui.complexity.value,
            derived_ui.complexity.value,
            current_ui.color_mood.value,
            derived_ui.color_mood.value,
        )
        await ws_handler.broadcast(session_id, WSUIUpdate(data=derived_ui))
        await redis_client.save_prev_ui(
            session_id,
            PreviousUIState(ui_commands=derived_ui, voice_style=VoiceStyle.neutral),
        )

    # 4 — persist state
    await gsm.save_state(state)

    elapsed = (time.monotonic() - ts_start) * 1000
    logger.debug(
        "Emotion processed for %s in %.1fms  dominant=%s  stress=%.2f",
        session_id,
        elapsed,
        signal.dominant,
        signal.emotions.stress,
    )


# ---------------------------------------------------------------------------
# Handle player speech  (the main orchestration loop)
# ---------------------------------------------------------------------------

async def handle_player_speech(session_id: str, text: str) -> None:
    """Full interaction turn:

    1. Build Contract 2
    2. Call Component B  (or mock)
    3. Parse Contract 3
    4. Apply game updates
    5. Detect adaptation → annotate timeline
    6. Broadcast WS messages
    """
    ts_start = time.monotonic()
    logger.info("Player speech received for %s: %s", session_id, text[:80])

    state = await gsm.get_state(session_id)
    if state is None:
        logger.warning("No state for session %s — ignoring speech", session_id)
        return
    if not state.is_active:
        logger.info("Session %s not active — ignoring speech", session_id)
        return

    # Record player's message in history
    gsm.add_to_history(state, "player", text)

    # ----- Step 1: Build Contract 2 -----
    snapshot = EmotionProcessor.build_snapshot(state)
    context = OracleContext(
        game_state=GameStateSnapshot(
            phase=state.phase,
            time_remaining=state.time_remaining,
            decisions_made=state.decisions_made,
            current_score=state.current_score,
        ),
        emotion_snapshot=snapshot,
        player_input=text,
        conversation_history=state.conversation_history,
    )
    logger.debug("Contract 2 built for %s: phase=%s trend=%s", session_id, state.phase.value, snapshot.trend.value)

    # ----- Step 2: Call Component B (or mock) -----
    oracle_resp: OracleResponse
    if settings.mock_mode:
        oracle_resp = _mock_oracle_response()
        logger.info("MOCK mode — using canned Contract 3")
    else:
        oracle_resp = await _call_component_b(context)

    # ----- Step 3: Apply game updates -----
    gsm.add_to_history(state, "oracle", oracle_resp.oracle_response.text)
    phase_advanced = gsm.apply_game_update(state, oracle_resp.game_update)

    # ----- Step 4: Detect adaptation -----
    prev_ui = await redis_client.load_prev_ui(session_id)
    adaptation = EmotionProcessor.detect_adaptation(
        prev_ui,
        oracle_resp.ui_commands,
        oracle_resp.oracle_response.voice_style,
    )
    if adaptation:
        await redis_client.update_latest_timeline_adaptation(session_id, adaptation)
        logger.info("Adaptation detected for %s: %s", session_id, adaptation)

    # Save new UI + voice_style as prev for next comparison
    await redis_client.save_prev_ui(
        session_id,
        PreviousUIState(
            ui_commands=oracle_resp.ui_commands,
            voice_style=oracle_resp.oracle_response.voice_style,
        ),
    )

    # ----- Step 5: Persist state -----
    await gsm.save_state(state)

    # ----- Step 6: Broadcast WS messages -----
    oracle_text = oracle_resp.oracle_response.text

    # ORACLE speech → Component C chat display
    await ws_handler.broadcast(
        session_id,
        WSOracleSpeech(
            text=oracle_text,
            voice_style=oracle_resp.oracle_response.voice_style.value,
        ),
    )
    # Make Tavus avatar speak the oracle response (fire-and-forget)
    if state.tavus_conversation_id:
        asyncio.create_task(
            tavus.echo_conversation(state.tavus_conversation_id, oracle_text)
        )

    # UI update → Component C (React + CopilotKit)
    await ws_handler.broadcast(
        session_id,
        WSUIUpdate(data=oracle_resp.ui_commands),
    )

    # Phase change notification
    if phase_advanced:
        await ws_handler.broadcast(
            session_id,
            WSPhaseChange(phase=state.phase.value),
        )
        # If game reached debrief, send game_end
        if state.phase == Phase.debrief:
            await ws_handler.broadcast(
                session_id,
                WSGameEnd(final_score=state.current_score, session_id=session_id),
            )

    # Next prompt (if provided) — send after a 1-second delay
    if oracle_resp.game_update.next_prompt:
        async def _send_next_prompt():
            await asyncio.sleep(1)
            await ws_handler.broadcast(
                session_id,
                WSOracleSpeech(
                    text=oracle_resp.game_update.next_prompt,
                    voice_style=oracle_resp.oracle_response.voice_style.value,
                ),
            )

        asyncio.create_task(_send_next_prompt())

    elapsed = (time.monotonic() - ts_start) * 1000
    logger.info(
        "Orchestration complete for %s in %.0fms  score=%d  phase=%s",
        session_id,
        elapsed,
        state.current_score,
        state.phase.value,
    )


# ---------------------------------------------------------------------------
# Component B HTTP call
# ---------------------------------------------------------------------------

async def _call_component_b(context: OracleContext) -> OracleResponse:
    """POST Contract 2 to Component B and parse Contract 3 response."""
    url = f"{settings.component_b_url}/api/oracle/respond"
    try:
        if _http_client is None:
            raise RuntimeError("HTTP client not initialised")

        contract2_json = context.model_dump_json()
        _emo = context.emotion_snapshot.current
        logger.info(
            "[→ oracle-brain] POST %s  phase=%s  stress=%.2f  focus=%.2f  trend=%s  text=%r",
            url,
            context.game_state.phase.value if hasattr(context.game_state.phase, "value") else context.game_state.phase,
            _emo.emotions.stress if _emo else 0.0,
            _emo.emotions.focus if _emo else 0.0,
            context.emotion_snapshot.trend.value if hasattr(context.emotion_snapshot.trend, "value") else context.emotion_snapshot.trend,
            (context.player_input or "")[:60],
        )
        resp = await _http_client.post(
            url,
            content=contract2_json,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        oracle_resp = OracleResponse.model_validate(data)
        logger.info(
            "[← oracle-brain] voice_style=%s  complexity=%s  guidance=%s  score_delta=%s  text=%r",
            oracle_resp.oracle_response.voice_style.value,
            oracle_resp.ui_commands.complexity.value if hasattr(oracle_resp.ui_commands.complexity, "value") else oracle_resp.ui_commands.complexity,
            oracle_resp.ui_commands.guidance_level,
            oracle_resp.game_update.score_delta,
            oracle_resp.oracle_response.text[:80],
        )
        return oracle_resp

    except httpx.ConnectError:
        logger.error("Component B unreachable at %s — returning fallback", url)
        return _fallback_oracle_response()
    except httpx.HTTPStatusError as exc:
        logger.error("Component B returned %s — returning fallback", exc.response.status_code)
        return _fallback_oracle_response()
    except Exception:
        logger.exception("Unexpected error calling Component B")
        return _fallback_oracle_response()


# ---------------------------------------------------------------------------
# Timer callbacks (wired up when the timer is started)
# ---------------------------------------------------------------------------

async def on_timer_tick(session_id: str, time_remaining: int) -> None:
    """Broadcast a timer_tick message every second."""
    from app.models import WSTimerTick

    await ws_handler.broadcast(
        session_id,
        WSTimerTick(time_remaining=time_remaining),
    )


async def on_timer_end(session_id: str) -> None:
    """Timer hit 0 — advance to debrief phase and end the game."""
    state = await gsm.get_state(session_id)
    if state is None:
        return
    # Advance to debrief phase
    state.phase = Phase.debrief
    state.is_active = False
    await gsm.save_state(state)
    logger.info("Timer expired for session %s  final_score=%d", session_id, state.current_score)
    # Notify clients of phase change first, then game end
    await ws_handler.broadcast(
        session_id,
        WSPhaseChange(phase=Phase.debrief.value),
    )
    await ws_handler.broadcast(
        session_id,
        WSGameEnd(final_score=state.current_score, session_id=session_id),
    )


# ---------------------------------------------------------------------------
# Opening greeting (sent once when game starts)
# ---------------------------------------------------------------------------

_OPENING_TEXT = (
    "ORACLE online. We have a narrow window to extract the classified data. "
    "I've identified three entry points — Node A has low encryption but active monitoring, "
    "Node B is heavily encrypted but unmonitored, Node C is an unmapped maintenance port. "
    "Which pattern looks weakest to you?"
)

async def send_opening_greeting(session_id: str) -> None:
    """Broadcast ORACLE's mission briefing right after game start.

    Always uses a hardcoded opening line so the briefing is immediate and
    consistent.  Waits 2 s so the WS client and Tavus have time to connect.
    """
    await asyncio.sleep(2.0)

    state = await gsm.get_state(session_id)
    if state is None:
        return

    # Record in conversation history so Claude has context
    gsm.add_to_history(state, "oracle", _OPENING_TEXT)
    await gsm.save_state(state)

    # Send text to frontend chat display
    await ws_handler.broadcast(
        session_id,
        WSOracleSpeech(text=_OPENING_TEXT, voice_style=VoiceStyle.neutral.value),
    )
    # Make Tavus avatar speak the greeting
    if state.tavus_conversation_id:
        await tavus.echo_conversation(state.tavus_conversation_id, _OPENING_TEXT)

    logger.info("Opening greeting sent for session %s", session_id)
