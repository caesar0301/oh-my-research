"""Tests for the mechanical gate-mode / confirmation validator."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "skills/oh-my-research/scripts"),
)

import gate_cli  # noqa: E402


class GateCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tmp.name) / "topic"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_cli(self, *argv: str) -> tuple[int, dict]:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = gate_cli.main(list(argv))
        return code, json.loads(buffer.getvalue())

    def ws(self, *args: str) -> tuple[str, ...]:
        return ("--workspace", str(self.workspace), *args)

    def init(self) -> None:
        code, _ = self.run_cli("init", *self.ws())
        self.assertEqual(code, 0)

    def user_record(self, gate: str) -> None:
        code, payload = self.run_cli(
            "record",
            *self.ws(
                "--gate",
                gate,
                "--decision-source",
                "user",
                "--user-decision",
                "proceed",
                "--checks",
                '[{"id":"coverage","status":"pass","details":"ok"}]',
            ),
        )
        self.assertEqual(code, 0, payload)

    def agent_record(self, gate: str) -> None:
        code, payload = self.run_cli(
            "record",
            *self.ws(
                "--gate",
                gate,
                "--checks",
                '[{"id":"coverage","status":"pass","details":"ok"}]',
            ),
        )
        self.assertEqual(code, 0, payload)

    def test_init_defaults_to_semi_automated(self) -> None:
        code, payload = self.run_cli("init", *self.ws())
        self.assertEqual(code, 0)
        self.assertEqual(payload["mode"]["mode"], "semi-automated")
        self.assertEqual(payload["mode"]["source"], "default")

    def test_set_requires_explicit_user_request(self) -> None:
        code, payload = self.run_cli("set", *self.ws("--mode", "quick-pass"))
        self.assertEqual(code, 2)
        self.assertFalse(payload["ok"])

    def test_set_accepts_explicit_phrase(self) -> None:
        code, payload = self.run_cli(
            "set",
            *self.ws(
                "--mode",
                "quick-pass",
                "--user-request",
                "no confirmations, just finish the report",
            ),
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["mode"]["mode"], "quick-pass")
        self.assertEqual(payload["mode"]["source"], "user")

    def test_semi_automated_record_requires_user_decision(self) -> None:
        self.init()
        code, payload = self.run_cli(
            "record",
            *self.ws("--gate", "M", "--checks", "[]"),
        )
        self.assertEqual(code, 2)
        self.assertFalse(payload["ok"])

        code, payload = self.run_cli(
            "record",
            *self.ws(
                "--gate",
                "M",
                "--decision-source",
                "user",
                "--user-decision",
                "proceed",
                "--checks",
                "[]",
            ),
        )
        self.assertEqual(code, 0)
        gate = json.loads(
            (self.workspace / ".omr/quality-gates/gate-m.json").read_text()
        )
        self.assertEqual(gate["decision_source"], "user")
        self.assertIs(gate["pause"], True)
        self.assertEqual(gate["user_decision"], "proceed")

    def test_chain_prerequisites_are_enforced(self) -> None:
        self.init()
        code, payload = self.run_cli(
            "record",
            *self.ws(
                "--gate", "A", "--decision-source", "user", "--user-decision", "proceed"
            ),
        )
        self.assertEqual(code, 2)
        self.assertIn("prerequisite", payload["error"])

    def test_validate_blocks_self_approved_gate(self) -> None:
        self.init()
        path = self.workspace / ".omr/quality-gates/gate-m.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "gate": "M",
                    "status": "pass",
                    "scenario_note": "agent decided to continue",
                    "decision_source": "agent",
                    "pause": False,
                    "user_decision": None,
                    "confirmed_at": None,
                    "checks": [],
                }
            ),
            encoding="utf-8",
        )
        code, payload = self.run_cli("validate", *self.ws("--stage", "analyze"))
        self.assertEqual(code, 1)
        self.assertFalse(payload["ok"])
        self.assertTrue(any("decision_source" in issue for issue in payload["issues"]))

    def test_validate_passes_user_confirmed_chain(self) -> None:
        self.init()
        for gate in ("M", "T", "A", "QA1", "P"):
            self.user_record(gate)
        code, payload = self.run_cli("validate", *self.ws("--stage", "synth"))
        self.assertEqual(code, 0, payload)
        self.assertTrue(payload["ok"])

    def test_quick_pass_still_requires_recorded_gates(self) -> None:
        code, _ = self.run_cli(
            "set",
            *self.ws("--mode", "quick-pass", "--user-request", "quick-pass please"),
        )
        self.assertEqual(code, 0)
        for gate in ("M", "T", "A", "QA1", "P"):
            self.agent_record(gate)
        code, payload = self.run_cli("validate", *self.ws("--stage", "synth"))
        self.assertEqual(code, 0, payload)
        self.assertTrue(payload["ok"])

    def test_rapid_pattern_skips_gates(self) -> None:
        code, payload = self.run_cli(
            "set", *self.ws("--mode", "fully-automated", "--pattern", "rapid")
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["mode"]["source"], "pattern")
        code, payload = self.run_cli("validate", *self.ws("--stage", "all"))
        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])

    def test_validate_rejects_missing_gate_mode(self) -> None:
        code, payload = self.run_cli("validate", *self.ws("--stage", "analyze"))
        self.assertEqual(code, 1)
        self.assertTrue(any("gate-mode.json" in issue for issue in payload["issues"]))


if __name__ == "__main__":
    unittest.main()
