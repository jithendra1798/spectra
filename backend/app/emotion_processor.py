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
    # Real-time emotion → UI derivation (mirrors frontend emotionEngine.ts)
    # ------------------------------------------------------------------

    @staticmethod
    def derive_ui_from_emotion(signal: EmotionSignal, current: UICommands) -> UICommands:
        """Derive UI commands directly from a single emotion signal.

        Mirrors the rules in spectra_frontend/src/adaptive/emotionEngine.ts.
        Used for real-time UI updates from emotion data without waiting for oracle.
        """
        stress = signal.emotions.stress
        focus = signal.emotions.focus
        confusion = signal.emotions.confusion
        confidence = signal.emotions.confidence

        # Rule 1: high stress OR high confusion → simplified + calm + high guidance
        if stress > 0.6 or confusion > 0.5:
            options = [o.model_copy(update={"highlighted": True}) for o in current.options[:2]] or current.options
            return UICommands(
                complexity=Complexity.simplified,
                color_mood=ColorMood.calm,
                panels_visible=["main"],
                guidance_level=GuidanceLevel.high,
                options=options,
            )

        # Rule 2: high focus AND low stress → full + intense
        if focus > 0.6 and stress < 0.3 and confidence > 0.5:
            return UICommands(
                complexity=Complexity.full,
                color_mood=ColorMood.intense,
                panels_visible=["main", "stats", "radar", "comms"],
                guidance_level=GuidanceLevel.low,
                options=[o.model_copy(update={"highlighted": False}) for o in current.options],
            )

        # Default: standard + neutral
        return UICommands(
            complexity=Complexity.standard,
            color_mood=ColorMood.neutral,
            panels_visible=["main", "stats"],
            guidance_level=GuidanceLevel.medium,
            options=[o.model_copy(update={"highlighted": False}) for o in current.options],
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
