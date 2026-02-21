"""
SPECTRA Component D — Pydantic models for all data contracts and WebSocket messages.

Contract 1: Emotion Signal          (A → D)
Contract 2: ORACLE Prompt Context   (D → B)
Contract 3: ORACLE Response + UI    (B → D → A, C)
Contract 4: Timeline Entry          (D → Redis)
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Phase(str, Enum):
    infiltrate = "infiltrate"
    vault = "vault"
    escape = "escape"
    debrief = "debrief"


class EmotionTrend(str, Enum):
    rising_stress = "rising_stress"
    falling_stress = "falling_stress"
    rising_focus = "rising_focus"
    falling_focus = "falling_focus"
    stable = "stable"


class VoiceStyle(str, Enum):
    calm_reassuring = "calm_reassuring"
    direct_fast = "direct_fast"
    urgent = "urgent"
    neutral = "neutral"


class Complexity(str, Enum):
    simplified = "simplified"
    standard = "standard"
    full = "full"


class ColorMood(str, Enum):
    calm = "calm"
    neutral = "neutral"
    intense = "intense"


class GuidanceLevel(str, Enum):
    none = "none"
    low = "low"
    medium = "medium"
    high = "high"


class AdaptationType(str, Enum):
    ui_simplified = "ui_simplified"
    options_expanded = "options_expanded"
    full_dashboard = "full_dashboard"
    voice_calmed = "voice_calmed"


# ---------------------------------------------------------------------------
# Contract 1 — Emotion Signal  (A → D)
# ---------------------------------------------------------------------------

class EmotionScores(BaseModel):
    stress: float = Field(ge=0, le=1)
    focus: float = Field(ge=0, le=1)
    confusion: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    neutral: float = Field(ge=0, le=1)


class EmotionSignal(BaseModel):
    """Contract 1 — raw emotion frame from Component A."""
    timestamp: int
    emotions: EmotionScores
    dominant: str
    face_detected: bool


# ---------------------------------------------------------------------------
# Contract 2 — ORACLE Prompt Context  (D → B)
# ---------------------------------------------------------------------------

class GameStateSnapshot(BaseModel):
    phase: Phase
    time_remaining: int
    decisions_made: int
    current_score: int


class EmotionSnapshot(BaseModel):
    current: Optional[EmotionSignal] = None
    trend: EmotionTrend = EmotionTrend.stable
    avg_stress_30s: float = 0.0


class ConversationEntry(BaseModel):
    role: Literal["oracle", "player"]
    text: str


class OracleContext(BaseModel):
    """Contract 2 — sent to Component B for Claude reasoning."""
    game_state: GameStateSnapshot
    emotion_snapshot: EmotionSnapshot
    player_input: Optional[str] = None
    conversation_history: list[ConversationEntry] = []


# ---------------------------------------------------------------------------
# Contract 3 — ORACLE Response + UI Commands  (B → D)
# ---------------------------------------------------------------------------

class OracleResponseContent(BaseModel):
    text: str
    voice_style: VoiceStyle = VoiceStyle.neutral


class OptionItem(BaseModel):
    id: str
    label: str
    highlighted: bool = False


class UICommands(BaseModel):
    complexity: Complexity = Complexity.standard
    color_mood: ColorMood = ColorMood.neutral
    panels_visible: list[str] = Field(default_factory=lambda: ["main", "stats"])
    options: list[OptionItem] = []
    guidance_level: GuidanceLevel = GuidanceLevel.low


class GameUpdate(BaseModel):
    score_delta: int = 0
    advance_phase: bool = False
    next_prompt: Optional[str] = None


class OracleResponse(BaseModel):
    """Contract 3 — returned by Component B."""
    oracle_response: OracleResponseContent
    ui_commands: UICommands
    game_update: GameUpdate = Field(default_factory=GameUpdate)


# ---------------------------------------------------------------------------
# Contract 4 — Timeline Entry  (D → Redis)
# ---------------------------------------------------------------------------

class TimelineEntry(BaseModel):
    """Contract 4 — one emotion data-point stored in Redis sorted set."""
    t: int
    phase: Phase
    stress: float = Field(ge=0, le=1)
    focus: float = Field(ge=0, le=1)
    adaptation: Optional[str] = None


# ---------------------------------------------------------------------------
# Game State (stored in Redis as JSON)
# ---------------------------------------------------------------------------

class GameState(BaseModel):
    session_id: str
    phase: Phase = Phase.infiltrate
    time_remaining: int = 300
    decisions_made: int = 0
    current_score: int = 0
    conversation_history: list[ConversationEntry] = []
    is_active: bool = True
    last_emotion: Optional[EmotionSignal] = None
    emotion_buffer: list[EmotionSignal] = []


# ---------------------------------------------------------------------------
# WebSocket Messages — Incoming (browser → backend)
# ---------------------------------------------------------------------------

class WSEmotionData(BaseModel):
    type: Literal["emotion_data"] = "emotion_data"
    data: EmotionSignal


class WSPlayerSpeech(BaseModel):
    type: Literal["player_speech"] = "player_speech"
    text: str


# ---------------------------------------------------------------------------
# WebSocket Messages — Outgoing (backend → browser)
# ---------------------------------------------------------------------------

class WSUIUpdate(BaseModel):
    type: Literal["ui_update"] = "ui_update"
    data: UICommands


class WSOracleSpeech(BaseModel):
    type: Literal["oracle_speech"] = "oracle_speech"
    text: str
    voice_style: str


class WSTimerTick(BaseModel):
    type: Literal["timer_tick"] = "timer_tick"
    time_remaining: int


class WSPhaseChange(BaseModel):
    type: Literal["phase_change"] = "phase_change"
    phase: str


class WSGameEnd(BaseModel):
    type: Literal["game_end"] = "game_end"
    final_score: int
    session_id: str


# ---------------------------------------------------------------------------
# REST Responses
# ---------------------------------------------------------------------------

class PreviousUIState(BaseModel):
    """Stores previous UI commands + voice_style for adaptation detection."""
    ui_commands: UICommands
    voice_style: VoiceStyle = VoiceStyle.neutral


class SessionCreated(BaseModel):
    session_id: str


class SessionStarted(BaseModel):
    status: str = "started"
    time_remaining: int


class SessionState(BaseModel):
    session_id: str
    phase: Phase
    time_remaining: int
    current_score: int
    decisions_made: int
    is_active: bool
