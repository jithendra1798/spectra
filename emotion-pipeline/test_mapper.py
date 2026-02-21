"""Simple test harness for mapper.

Usage:
  python emotion-pipeline/test_mapper.py emotion-pipeline/fixtures/utterance.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from mapper import map_utterance_to_contract1


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python emotion-pipeline/test_mapper.py <utterance.json>")
        return 2

    path = Path(sys.argv[1])
    payload = json.loads(path.read_text())
    contract1, player_speech = map_utterance_to_contract1(payload)

    print("Contract 1:")
    print(json.dumps(contract1, indent=2, ensure_ascii=True))
    print("\nplayer_speech:")
    print(player_speech)

    # basic checks
    assert "timestamp" in contract1
    assert "emotions" in contract1
    assert "dominant" in contract1
    assert "face_detected" in contract1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
