"""
Scenario templates for ORACLE's 3-phase mission.
Used by the backend to inject phase context into Contract 2.
"""

from typing import Optional

PHASES = {
    "infiltrate": {
        "opening": (
            "I've identified three possible entry points. "
            "Node A has low encryption but active monitoring. "
            "Node B is heavily encrypted but unmonitored. "
            "Node C is a maintenance port — unknown security. "
            "Which pattern looks weakest to you?"
        ),
        "options": [
            {"id": "A", "label": "Node A — low encryption, monitored"},
            {"id": "B", "label": "Node B — heavy encryption, unmonitored"},
            {"id": "C", "label": "Node C — maintenance port, unknown"},
        ],
        "transition": "We're through. Firewall bypassed. Moving to the vault.",
    },
    "vault": {
        "opening": (
            "The vault uses a rotating cipher. I can brute-force sections, "
            "but I need you to spot the pattern. Look at these fragments: "
            "7-3-11-7-3-11 / 4-8-4-8-4-8 / 2-5-9-2-5-9. "
            "Which one breaks the rotation?"
        ),
        "options": [
            {"id": "fast", "label": "Fast track — 40s, 30% alarm risk"},
            {"id": "safe", "label": "Safe track — 2min, no risk"},
        ],
        "transition": "Vault cracked. Data extracted. Now we need to get out — security is aware.",
    },
    "escape": {
        "opening": (
            "Security is converging. Three routes: "
            "main corridor — fast, 45s, exposed. "
            "Service tunnel — slow, 90s, hidden. "
            "Rooftop — 60s, risky, unexpected. "
            "We have {time_remaining}s. Your call."
        ),
        "options": [
            {"id": "corridor", "label": "Main corridor — fast, exposed"},
            {"id": "tunnel",   "label": "Service tunnel — slow, hidden"},
            {"id": "rooftop",  "label": "Rooftop — risky, unexpected"},
        ],
        "transition": "We made it. Let's debrief.",
    },
}

PHASE_ORDER = ["infiltrate", "vault", "escape"]


def get_opening(phase: str, time_remaining: int = 300) -> str:
    return PHASES[phase]["opening"].format(time_remaining=time_remaining)


def get_options(phase: str) -> list:
    return PHASES[phase]["options"]


def get_transition(phase: str) -> str:
    return PHASES[phase]["transition"]


def next_phase(phase: str) -> Optional[str]:
    idx = PHASE_ORDER.index(phase)
    return PHASE_ORDER[idx + 1] if idx + 1 < len(PHASE_ORDER) else None
