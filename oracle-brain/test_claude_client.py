"""
Unit tests for claude_client.py

Run:  python3 -m pytest test_claude_client.py -v
"""

import asyncio
import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# ── Load shared fixtures once ─────────────────────────────────────────────────

MOCK_DIR = Path(__file__).parent.parent / "mock-data"
CONTRACT2 = json.loads((MOCK_DIR / "context_payload.json").read_text())
CONTRACT3 = json.loads((MOCK_DIR / "oracle_response.json").read_text())


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_anthropic_response(text: str):
    """Build a minimal fake anthropic Message object."""
    block = MagicMock()
    block.text = text
    msg = MagicMock()
    msg.content = [block]
    return msg


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ── call_claude ───────────────────────────────────────────────────────────────

class TestCallClaude(unittest.TestCase):

    @patch("claude_client.anthropic.Anthropic")
    def test_returns_parsed_json(self, MockAnthropic):
        MockAnthropic.return_value.messages.create.return_value = (
            make_anthropic_response(json.dumps(CONTRACT3))
        )
        from claude_client import call_claude
        result = call_claude(CONTRACT2)
        self.assertEqual(result, CONTRACT3)

    @patch("claude_client.anthropic.Anthropic")
    def test_passes_contract2_as_user_message(self, MockAnthropic):
        mock_create = MockAnthropic.return_value.messages.create
        mock_create.return_value = make_anthropic_response(json.dumps(CONTRACT3))

        from claude_client import call_claude
        call_claude(CONTRACT2)

        _, kwargs = mock_create.call_args
        user_msg = kwargs["messages"][0]
        self.assertEqual(user_msg["role"], "user")
        self.assertEqual(json.loads(user_msg["content"]), CONTRACT2)

    @patch("claude_client.anthropic.Anthropic")
    def test_uses_correct_model(self, MockAnthropic):
        mock_create = MockAnthropic.return_value.messages.create
        mock_create.return_value = make_anthropic_response(json.dumps(CONTRACT3))

        from claude_client import call_claude, MODEL
        call_claude(CONTRACT2)

        _, kwargs = mock_create.call_args
        self.assertEqual(kwargs["model"], MODEL)

    @patch("claude_client.anthropic.Anthropic")
    def test_raises_on_invalid_json_response(self, MockAnthropic):
        MockAnthropic.return_value.messages.create.return_value = (
            make_anthropic_response("not json at all")
        )
        from claude_client import call_claude
        with self.assertRaises(json.JSONDecodeError):
            call_claude(CONTRACT2)


# ── handle (WebSocket handler) ────────────────────────────────────────────────

class TestHandle(unittest.TestCase):

    def _make_ws(self, messages):
        """Fake websocket that yields messages then stops."""
        async def aiter(self_):
            for m in messages:
                yield m

        async def noop(*_):
            pass

        ws = MagicMock()
        ws.__aiter__ = aiter
        ws.send = MagicMock(side_effect=noop)
        return ws

    def _sent(self, ws):
        """Return list of decoded JSON payloads sent on ws."""
        return [json.loads(c.args[0]) for c in ws.send.call_args_list]

    # -- mock mode ------------------------------------------------------------

    @patch("claude_client.MOCK_MODE", True)
    def test_mock_mode_returns_mock_response(self):
        from claude_client import handle
        ws = self._make_ws([json.dumps(CONTRACT2)])
        run(handle(ws))
        self.assertEqual(self._sent(ws), [CONTRACT3])

    @patch("claude_client.MOCK_MODE", True)
    def test_mock_mode_handles_multiple_messages(self):
        from claude_client import handle
        ws = self._make_ws([json.dumps(CONTRACT2)] * 3)
        run(handle(ws))
        self.assertEqual(len(self._sent(ws)), 3)

    # -- live mode ------------------------------------------------------------

    @patch("claude_client.MOCK_MODE", False)
    @patch("claude_client.call_claude", return_value=CONTRACT3)
    def test_live_mode_calls_claude_and_returns_response(self, mock_call):
        from claude_client import handle
        ws = self._make_ws([json.dumps(CONTRACT2)])
        run(handle(ws))
        mock_call.assert_called_once_with(CONTRACT2)
        self.assertEqual(self._sent(ws), [CONTRACT3])

    @patch("claude_client.MOCK_MODE", False)
    @patch("claude_client.call_claude", side_effect=Exception("API down"))
    def test_live_mode_falls_back_to_mock_on_error(self, _):
        from claude_client import handle
        ws = self._make_ws([json.dumps(CONTRACT2)])
        run(handle(ws))
        self.assertEqual(self._sent(ws), [CONTRACT3])

    # -- bad input ------------------------------------------------------------

    @patch("claude_client.MOCK_MODE", True)
    def test_invalid_json_input_returns_error_key(self):
        from claude_client import handle
        ws = self._make_ws(["this is not json"])
        run(handle(ws))
        sent = self._sent(ws)
        self.assertEqual(len(sent), 1)
        self.assertIn("error", sent[0])

    @patch("claude_client.MOCK_MODE", True)
    def test_empty_object_is_accepted(self):
        from claude_client import handle
        ws = self._make_ws(["{}"])
        run(handle(ws))
        self.assertEqual(self._sent(ws), [CONTRACT3])


# ── Contract 3 shape ──────────────────────────────────────────────────────────

class TestContract3Shape(unittest.TestCase):
    """Validate that the mock response (and therefore Claude's output) matches
    the expected Contract 3 schema."""

    def setUp(self):
        self.r = CONTRACT3

    def test_has_oracle_response(self):
        self.assertIn("oracle_response", self.r)

    def test_oracle_response_has_text(self):
        self.assertIsInstance(self.r["oracle_response"]["text"], str)
        self.assertTrue(len(self.r["oracle_response"]["text"]) > 0)

    def test_voice_style_is_valid(self):
        valid = {"calm_reassuring", "direct_fast", "urgent", "neutral"}
        self.assertIn(self.r["oracle_response"]["voice_style"], valid)

    def test_has_ui_commands(self):
        self.assertIn("ui_commands", self.r)

    def test_complexity_is_valid(self):
        valid = {"simplified", "standard", "full"}
        self.assertIn(self.r["ui_commands"]["complexity"], valid)

    def test_color_mood_is_valid(self):
        valid = {"calm", "neutral", "intense"}
        self.assertIn(self.r["ui_commands"]["color_mood"], valid)

    def test_panels_visible_is_list(self):
        self.assertIsInstance(self.r["ui_commands"]["panels_visible"], list)

    def test_panels_visible_contains_main(self):
        self.assertIn("main", self.r["ui_commands"]["panels_visible"])

    def test_options_is_list(self):
        self.assertIsInstance(self.r["ui_commands"]["options"], list)

    def test_each_option_has_required_keys(self):
        for opt in self.r["ui_commands"]["options"]:
            self.assertIn("id", opt)
            self.assertIn("label", opt)
            self.assertIn("highlighted", opt)
            self.assertIsInstance(opt["highlighted"], bool)

    def test_guidance_level_is_valid(self):
        valid = {"none", "low", "medium", "high"}
        self.assertIn(self.r["ui_commands"]["guidance_level"], valid)

    def test_has_game_update(self):
        self.assertIn("game_update", self.r)

    def test_score_delta_is_int(self):
        self.assertIsInstance(self.r["game_update"]["score_delta"], int)

    def test_advance_phase_is_bool(self):
        self.assertIsInstance(self.r["game_update"]["advance_phase"], bool)

    def test_next_prompt_is_str_or_none(self):
        val = self.r["game_update"]["next_prompt"]
        self.assertTrue(val is None or isinstance(val, str))


if __name__ == "__main__":
    unittest.main()
