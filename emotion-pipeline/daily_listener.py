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
        self.call_client: CallClient | None = None
        self.last_conversation_id: str | None = None

    def set_call_client(self, client: CallClient) -> None:
        self.call_client = client

    def _update_conversation_id(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        conversation_id = payload.get("conversation_id")
        if not conversation_id:
            properties = payload.get("properties", {}) if isinstance(payload, dict) else {}
            conversation_id = properties.get("conversation_id")
        if conversation_id:
            self.last_conversation_id = str(conversation_id)

    def send_echo(self, text: str, emotion_tag: str | None = None) -> None:
        if not self.call_client:
            logging.error("[send_echo] FAILED — CallClient not set")
            return
        if not self.last_conversation_id:
            logging.error("[send_echo] FAILED — conversation_id unknown")
            return

        logging.info("[send_echo] sending interrupt  conversation_id=%s", self.last_conversation_id)
        try:
            self.call_client.send_app_message(
                {
                    "message_type": "conversation",
                    "event_type": "conversation.interrupt",
                    "conversation_id": self.last_conversation_id,
                }
            )
            logging.info("[send_echo] interrupt sent OK")
        except Exception:
            logging.exception("[send_echo] FAILED to send conversation.interrupt")

        if emotion_tag:
            body = f'<emotion value="{emotion_tag}"/> {text}'
        else:
            body = text

        logging.info("[send_echo] sending echo  conversation_id=%s  text=%r", self.last_conversation_id, body[:80])
        try:
            self.call_client.send_app_message(
                {
                    "message_type": "conversation",
                    "event_type": "conversation.echo",
                    "conversation_id": self.last_conversation_id,
                    "properties": {
                        "modality": "text",
                        "text": body,
                        "done": True,
                    },
                }
            )
            logging.info("[send_echo] echo sent OK — avatar should speak now")
        except Exception:
            logging.exception("[send_echo] FAILED to send conversation.echo")

    def on_app_message(self, message: Any, sender: str = "") -> None:
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

            self._update_conversation_id(payload)

            properties = payload.get("properties", {}) if isinstance(payload, dict) else {}

            # Detect whether this is a USER utterance vs a REPLICA utterance.
            #
            # Reliable signals (in priority order):
            #   1. role == "user"  → definitely user
            #   2. role == "replica" or role == "assistant"  → definitely replica
            #   3. user_audio_analysis / user_visual_analysis present → user
            #      (Raven-1 only produces these for user utterances)
            #   4. None of the above → ASSUME user (safe default — it's
            #      better to double-process a replica line than to silently
            #      drop a player command)
            role = properties.get("role")  # may or may not exist
            has_raven = bool(
                properties.get("user_audio_analysis")
                or properties.get("user_visual_analysis")
            )
            is_replica = role in ("replica", "assistant")
            is_user = not is_replica  # default: treat as user unless proven otherwise

            logging.info(
                "utterance detection: role=%s  has_raven=%s  is_replica=%s  is_user=%s",
                role, has_raven, is_replica, is_user,
            )

            # Checkpoint 2: map to Contract 1 + extract player speech
            contract1, player_speech = map_utterance_to_contract1(payload)
            logging.info("contract1: %s", _safe_json(contract1))
            if player_speech:
                logging.info("player_speech: %s", player_speech)

            # Send to backend WS (Checkpoint 3)
            if self.ws_client is not None and is_user:
                try:
                    loop = Daily.get_event_loop()
                except Exception:
                    loop = None
                if loop is not None:
                    loop.create_task(self.ws_client.send_emotion_data(contract1))
                    if player_speech:
                        loop.create_task(self.ws_client.send_player_speech(player_speech))
            elif self.ws_client is not None and not is_user:
                logging.info("Skipping backend send — replica utterance (role=%s)", role)
            elif self.ws_client is None:
                logging.warning(
                    "ws_client is None — cannot send to backend. "
                    "hint: start with --backend-ws and --session-id"
                )


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
    handler.set_call_client(client)

    logging.info("Joining Daily room: %s", args.url)
    if ws_client is not None:
        logging.info("Connecting backend WS: %s", ws_client.ws_url)
        loop = Daily.get_event_loop()

        def _on_backend_message(raw: str) -> None:
            # Checkpoint 4: echo backend speech to Tavus replica
            try:
                msg = json.loads(raw)
            except Exception:
                logging.error("[ECHO PHASE 1/3] bad JSON from backend: %r", raw[:200])
                return

            msg_type = msg.get("type", "unknown")
            logging.info("[ECHO PHASE 1/3] backend_ws received  type=%s  payload=%s", msg_type, raw[:200])

            if isinstance(msg, dict) and msg_type == "oracle_speech":
                text = msg.get("text") or ""
                logging.info("[ECHO PHASE 2/3] oracle_speech matched  text=%r  conversation_id=%s",
                             text[:80], handler.last_conversation_id)
                if not text:
                    logging.warning("[ECHO PHASE 2/3] SKIPPED — empty text in oracle_speech")
                    return
                if not handler.last_conversation_id:
                    logging.error(
                        "[ECHO PHASE 2/3] FAILED — conversation_id is None  "
                        "hint: no conversation.utterance received yet, avatar may not have spoken first"
                    )
                    return
                logging.info("[ECHO PHASE 3/3] calling send_echo → conversation.echo to Tavus")
                handler.send_echo(text)
                logging.info("[ECHO PHASE 3/3] send_echo returned (avatar should speak now)")
            else:
                logging.debug("[ECHO PHASE 1/3] ignoring non-oracle_speech message  type=%s", msg_type)

        async def _ws_task() -> None:
            await ws_client.connect()
            await ws_client.recv_loop_with_handler(_on_backend_message)

        loop.create_task(_ws_task())
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
