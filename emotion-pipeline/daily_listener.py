"""
Checkpoint 1: Tavus interaction client + event capture.

This module joins a Daily room (CVI conversation URL) as a participant and
listens for app-message events. It filters for conversation.utterance and
prints raw payloads.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sys
from typing import Any

from mapper import map_utterance_to_contract1
from ws_client import BackendWSClient

try:
    from daily import CallClient, Daily, EventHandler
except Exception as exc:  # pragma: no cover - import error
    raise SystemExit(
        "daily-python is required. Install with: pip install -r emotion-pipeline/requirements.txt"
    ) from exc


class TavusEventHandler(EventHandler):
    def __init__(self, log_all: bool, ws_client: BackendWSClient | None) -> None:
        super().__init__()
        self.log_all = log_all
        self.ws_client = ws_client

    def on_app_message(self, message: Any) -> None:
        payload = message
        # daily-python may wrap payload in an object with .data or .message
        if hasattr(message, "data"):
            payload = message.data
        elif hasattr(message, "message"):
            payload = message.message

        if self.log_all:
            logging.info("app-message: %s", _safe_json(payload))

        if isinstance(payload, dict) and payload.get("event_type") == "conversation.utterance":
            logging.info("conversation.utterance: %s", _safe_json(payload))

            # Checkpoint 2: map to Contract 1 + extract player speech
            contract1, player_speech = map_utterance_to_contract1(payload)
            logging.info("contract1: %s", _safe_json(contract1))
            if player_speech:
                logging.info("player_speech: %s", player_speech)

            # Send to backend WS (Checkpoint 3)
            if self.ws_client is not None:
                try:
                    loop = Daily.get_event_loop()
                except Exception:
                    loop = None
                if loop is not None:
                    loop.create_task(self.ws_client.send_emotion_data(contract1))
                    if player_speech:
                        loop.create_task(self.ws_client.send_player_speech(player_speech))


def _safe_json(payload: Any) -> str:
    try:
        return json.dumps(payload, ensure_ascii=True)
    except Exception:
        return str(payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Listen for Tavus conversation.utterance events.")
    parser.add_argument(
        "--url",
        default=os.getenv("TAVUS_CONVERSATION_URL"),
        help="Daily room / Tavus conversation URL (env: TAVUS_CONVERSATION_URL)",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("DAILY_TOKEN"),
        help="Daily meeting token if required (env: DAILY_TOKEN)",
    )
    parser.add_argument(
        "--name",
        default=os.getenv("DAILY_USER_NAME", "spectra-emotion-pipeline"),
        help="Display name for the Daily participant (env: DAILY_USER_NAME)",
    )
    parser.add_argument(
        "--log-all",
        action="store_true",
        help="Log all app-message events, not just conversation.utterance",
    )
    parser.add_argument(
        "--backend-ws",
        default=os.getenv("BACKEND_WS_URL"),
        help="Backend WS base URL (e.g. ws://localhost:8000). If set, will send emotion_data/player_speech.",
    )
    parser.add_argument(
        "--session-id",
        default=os.getenv("SESSION_ID"),
        help="Session ID for backend WS (env: SESSION_ID)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.url:
        logging.error("Missing --url or TAVUS_CONVERSATION_URL")
        return 2

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )

    Daily.init()

    ws_client = None
    if args.backend_ws and args.session_id:
        ws_client = BackendWSClient(args.backend_ws, args.session_id)

    handler = TavusEventHandler(log_all=args.log_all, ws_client=ws_client)
    client = CallClient(event_handler=handler)

    logging.info("Joining Daily room: %s", args.url)
    if ws_client is not None:
        logging.info("Connecting backend WS: %s", ws_client.ws_url)
        Daily.get_event_loop().create_task(ws_client.connect())
    client.join(args.url, token=args.token, user_name=args.name)

    # Block until SIGINT/SIGTERM
    stop = False

    def _signal_handler(_sig, _frame):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    while not stop:
        Daily.run_main_loop(0.1)

    logging.info("Leaving call...")
    client.leave()
    if ws_client is not None:
        Daily.get_event_loop().run_until_complete(ws_client.close())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
