"""
Unit tests for scenarios.py

Run:  python3 -m pytest test_scenarios.py -v
"""

import unittest

from scenarios import (
    PHASES,
    PHASE_ORDER,
    get_opening,
    get_options,
    get_transition,
    next_phase,
)


# ── Constants / structure ─────────────────────────────────────────────────────

class TestScenariosStructure(unittest.TestCase):
    """PHASES and PHASE_ORDER are consistent and complete."""

    def test_phase_order_matches_phases(self):
        self.assertEqual(set(PHASE_ORDER), set(PHASES.keys()))

    def test_each_phase_has_opening_options_transition(self):
        for name, data in PHASES.items():
            self.assertIn("opening", data, f"phase {name!r} missing 'opening'")
            self.assertIn("options", data, f"phase {name!r} missing 'options'")
            self.assertIn("transition", data, f"phase {name!r} missing 'transition'")

    def test_options_have_id_and_label(self):
        for name, data in PHASES.items():
            for opt in data["options"]:
                self.assertIn("id", opt, f"phase {name!r} option missing 'id'")
                self.assertIn("label", opt, f"phase {name!r} option missing 'label'")


# ── get_opening ────────────────────────────────────────────────────────────────

class TestGetOpening(unittest.TestCase):

    def test_infiltrate_opening_contains_expected_text(self):
        text = get_opening("infiltrate")
        self.assertIn("three possible entry points", text)
        self.assertIn("Node A", text)
        self.assertIn("Node B", text)
        self.assertIn("Node C", text)

    def test_vault_opening_contains_expected_text(self):
        text = get_opening("vault")
        self.assertIn("rotating cipher", text)
        self.assertIn("7-3-11", text)

    def test_escape_opening_uses_default_time_remaining(self):
        text = get_opening("escape")
        self.assertIn("300s", text)

    def test_escape_opening_formats_time_remaining(self):
        text = get_opening("escape", time_remaining=90)
        self.assertIn("90s", text)

    def test_get_opening_invalid_phase_raises(self):
        with self.assertRaises(KeyError):
            get_opening("unknown_phase")


# ── get_options ───────────────────────────────────────────────────────────────

class TestGetOptions(unittest.TestCase):

    def test_infiltrate_returns_three_options(self):
        opts = get_options("infiltrate")
        self.assertEqual(len(opts), 3)
        ids = [o["id"] for o in opts]
        self.assertEqual(ids, ["A", "B", "C"])

    def test_vault_returns_two_options(self):
        opts = get_options("vault")
        self.assertEqual(len(opts), 2)
        self.assertEqual([o["id"] for o in opts], ["fast", "safe"])

    def test_escape_returns_three_options(self):
        opts = get_options("escape")
        self.assertEqual(len(opts), 3)
        self.assertEqual([o["id"] for o in opts], ["corridor", "tunnel", "rooftop"])

    def test_get_options_invalid_phase_raises(self):
        with self.assertRaises(KeyError):
            get_options("unknown_phase")


# ── get_transition ────────────────────────────────────────────────────────────

class TestGetTransition(unittest.TestCase):

    def test_infiltrate_transition(self):
        self.assertIn("Firewall bypassed", get_transition("infiltrate"))

    def test_vault_transition(self):
        self.assertIn("Vault cracked", get_transition("vault"))

    def test_escape_transition(self):
        self.assertIn("We made it", get_transition("escape"))

    def test_get_transition_invalid_phase_raises(self):
        with self.assertRaises(KeyError):
            get_transition("unknown_phase")


# ── next_phase ────────────────────────────────────────────────────────────────

class TestNextPhase(unittest.TestCase):

    def test_infiltrate_next_is_vault(self):
        self.assertEqual(next_phase("infiltrate"), "vault")

    def test_vault_next_is_escape(self):
        self.assertEqual(next_phase("vault"), "escape")

    def test_escape_next_is_none(self):
        self.assertIsNone(next_phase("escape"))

    def test_next_phase_invalid_phase_raises(self):
        with self.assertRaises(ValueError):
            next_phase("unknown_phase")


if __name__ == "__main__":
    unittest.main()
