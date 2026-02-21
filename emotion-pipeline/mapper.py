"""Emotion extraction mapper for Tavus utterance payloads.

Input: Tavus conversation.utterance payload (dict)
Output:
  - Contract 1 EmotionSignal dict
  - player_speech text (properties.speech)

Assumptions:
  - user_audio_analysis and user_visual_analysis contain ratings in the format:
    "stress=X, focus=Y, confusion=Z, confidence=W, neutral=N"
"""

from __future__ import annotations

import re
import time
from typing import Any, Dict, Optional, Tuple

RATING_KEYS = ("stress", "focus", "confusion", "confidence", "neutral")
RATING_RE = re.compile(r"(stress|focus|confusion|confidence|neutral)\s*=\s*([0-9]+(?:\.[0-9]+)?)", re.I)


def _parse_ratings(text: Optional[str]) -> Dict[str, float]:
    if not text:
        return {}
    ratings: Dict[str, float] = {}
    for match in RATING_RE.finditer(text):
        key = match.group(1).lower()
        val = float(match.group(2))
        ratings[key] = val
    return ratings


def _normalize(val_1_to_10: float) -> float:
    # Clamp to [1,10] then normalize to [0,1]
    if val_1_to_10 < 1:
        val_1_to_10 = 1
    if val_1_to_10 > 10:
        val_1_to_10 = 10
    return round(val_1_to_10 / 10.0, 4)


def _average(audio: Dict[str, float], visual: Dict[str, float]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for key in RATING_KEYS:
        a = audio.get(key)
        v = visual.get(key)
        if a is None and v is None:
            out[key] = 0.0
        elif a is None:
            out[key] = _normalize(v)
        elif v is None:
            out[key] = _normalize(a)
        else:
            out[key] = _normalize((a + v) / 2.0)
    return out


def map_utterance_to_contract1(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
    properties = payload.get("properties", {}) if isinstance(payload, dict) else {}

    user_audio = properties.get("user_audio_analysis")
    user_visual = properties.get("user_visual_analysis")

    audio_ratings = _parse_ratings(user_audio)
    visual_ratings = _parse_ratings(user_visual)
    emotions = _average(audio_ratings, visual_ratings)

    # Determine dominant
    dominant = max(emotions, key=lambda k: emotions[k]) if emotions else "neutral"

    face_detected = bool(user_visual)

    contract1 = {
        "timestamp": int(time.time() * 1000),
        "emotions": emotions,
        "dominant": dominant,
        "face_detected": face_detected,
    }

    player_speech = properties.get("speech")

    return contract1, player_speech
