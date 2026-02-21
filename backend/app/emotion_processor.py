"""
SPECTRA Component D — Emotion processing.

Responsibilities:
  • Maintain a rolling buffer of the last 30 emotion readings (~30 s)
  • Compute trend  (rising_stress / falling_stress / rising_focus / falling_focus / stable)
  • Compute avg_stress_30s
  • Detect adaptation type by diffing old vs. new UI commands
  • Build Contract 4 timeline entries
"""

from __future__ import annotations

import logging
from typing import Optional

from app.models import (
    AdaptationType,
    Complexity,
    EmotionSignal,
    EmotionSnapshot,
    EmotionTrend,
    GameState,
    Phase,
    PreviousUIState,
    TimelineEntry,
    UICommands,
    VoiceStyle,
)

logger = logging.getLogger("spectra.emotion")

# Maximum readings kept in the buffer (≈ 30 seconds at 1 reading/s)
BUFFER_SIZE = 30

# Number of recent readings used for trend calculation
TREND_WINDOW = 5

# Threshold delta for declaring a "rising" or "falling" trend
TREND_THRESHOLD = 0.1


class EmotionProcessor:
    """Stateless helper — operates on the emotion_buffer inside GameState."""

    # ------------------------------------------------------------------
    # Buffer management
    # ------------------------------------------------------------------

    @staticmethod
    def push_to_buffer(state: GameState, signal: EmotionSignal) -> None:
        """Append a reading to the buffer, trimming to BUFFER_SIZE."""
        state.emotion_buffer.append(signal)
        if len(state.emotion_buffer) > BUFFER_SIZE:
            state.emotion_buffer = state.emotion_buffer[-BUFFER_SIZE:]
        state.last_emotion = signal

    # ------------------------------------------------------------------
    # Trend computation
    # ------------------------------------------------------------------

    @staticmethod
    def compute_trend(buffer: list[EmotionSignal]) -> EmotionTrend:
        """Compare readings [0-2] vs [2-4] of the last TREND_WINDOW readings.

        Uses overlapping windows per spec: first 3 readings vs last 3 readings
        in a 5-element window (index 2 is shared).
        • If avg stress rose by > TREND_THRESHOLD  → rising_stress
        • If avg stress fell by > TREND_THRESHOLD  → falling_stress
        • Same logic for focus  → rising_focus / falling_focus
        • Otherwise → stable
        """
        if len(buffer) < TREND_WINDOW:
            return EmotionTrend.stable

        window = buffer[-TREND_WINDOW:]
        # Spec: compare readings [0-2] vs [2-4]
        first_half = window[:3]   # indices 0, 1, 2
        second_half = window[2:]  # indices 2, 3, 4

        first_stress = sum(r.emotions.stress for r in first_half) / len(first_half)
        second_stress = sum(r.emotions.stress for r in second_half) / len(second_half)
        stress_delta = second_stress - first_stress

        first_focus = sum(r.emotions.focus for r in first_half) / len(first_half)
        second_focus = sum(r.emotions.focus for r in second_half) / len(second_half)
        focus_delta = second_focus - first_focus

        # Stress takes priority over focus
        if stress_delta > TREND_THRESHOLD:
            return EmotionTrend.rising_stress
        if stress_delta < -TREND_THRESHOLD:
            return EmotionTrend.falling_stress
        if focus_delta > TREND_THRESHOLD:
            return EmotionTrend.rising_focus
        if focus_delta < -TREND_THRESHOLD:
            return EmotionTrend.falling_focus

        return EmotionTrend.stable

    # ------------------------------------------------------------------
    # Average stress over buffer
    # ------------------------------------------------------------------

    @staticmethod
    def compute_avg_stress(buffer: list[EmotionSignal]) -> float:
        """Mean stress over the full buffer (up to 30 s)."""
        if not buffer:
            return 0.0
        return sum(r.emotions.stress for r in buffer) / len(buffer)

    # ------------------------------------------------------------------
    # Build EmotionSnapshot (for Contract 2)
    # ------------------------------------------------------------------

    @classmethod
    def build_snapshot(cls, state: GameState) -> EmotionSnapshot:
        return EmotionSnapshot(
            current=state.last_emotion,
            trend=cls.compute_trend(state.emotion_buffer),
            avg_stress_30s=round(cls.compute_avg_stress(state.emotion_buffer), 4),
        )

    # ------------------------------------------------------------------
    # Build Contract 4 timeline entry
    # ------------------------------------------------------------------

    @staticmethod
    def build_timeline_entry(
        signal: EmotionSignal,
        phase: Phase,
        adaptation: Optional[str] = None,
    ) -> TimelineEntry:
        return TimelineEntry(
            t=signal.timestamp,
            phase=phase,
            stress=signal.emotions.stress,
            focus=signal.emotions.focus,
            adaptation=adaptation,
        )

    # ------------------------------------------------------------------
    # Adaptation detection (diff previous vs. new UI commands)
    # ------------------------------------------------------------------

    @staticmethod
    def detect_adaptation(
        prev: Optional[PreviousUIState],
        new: UICommands,
        new_voice_style: VoiceStyle,
    ) -> Optional[str]:
        """Compare previous and new UI/voice state and return the adaptation
        label (or None if nothing changed).

        Priority order:
          1. complexity changed  → ui_simplified / options_expanded / full_dashboard
          2. voice_style changed to calm_reassuring → voice_calmed
        """
        if prev is not None:
            if new.complexity != prev.ui_commands.complexity:
                if new.complexity == Complexity.simplified:
                    return AdaptationType.ui_simplified.value
                elif new.complexity == Complexity.full:
                    return AdaptationType.full_dashboard.value
                else:
                    return AdaptationType.options_expanded.value

            # Only trigger voice_calmed when it *changes* to calm_reassuring
            if (
                new_voice_style == VoiceStyle.calm_reassuring
                and prev.voice_style != VoiceStyle.calm_reassuring
            ):
                return AdaptationType.voice_calmed.value
        else:
            # First turn — no previous state to compare against
            if new_voice_style == VoiceStyle.calm_reassuring:
                return AdaptationType.voice_calmed.value

        return None
