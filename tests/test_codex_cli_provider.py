"""Deterministic tests for the Codex CLI provider boundary."""

import json
import unittest

from src.codex_cli_provider import BELIEF_OUTPUT_SCHEMA, CodexCLIProvider


MODEL_OUTPUT = {
    "belief_status": "VALID",
    "confidence": 0.75,
    "explanation": "Resolved observable evidence remains supportive.",
    "evidence_summary": {
        "supporting_evidence": [],
        "contradicting_evidence": [],
    },
}


class RecordingRunner:
    def __init__(self, output=None):
        self.output = output if output is not None else json.dumps(MODEL_OUTPUT)
        self.calls = []

    def __call__(self, command, prompt, timeout):
        schema_index = command.index("--output-schema") + 1
        with open(command[schema_index], encoding="utf-8") as schema_file:
            schema = json.load(schema_file)
        self.calls.append((command, prompt, timeout, schema))
        return self.output


class CodexCLIProviderTests(unittest.TestCase):
    def setUp(self):
        self.context = {
            "current_observation": {"timestamp": "2000-01-03"},
            "previous_belief_state": None,
            "recent_resolved_evidence": [],
            "historical_evidence_summary": {
                "resolved_count": 0,
                "supporting_count": 0,
                "contradicting_count": 0,
                "success_rate": None,
            },
        }

    def test_invocation_is_ephemeral_schema_bound_and_context_only(self):
        runner = RecordingRunner()
        provider = CodexCLIProvider(runner=runner)

        self.assertEqual(provider(self.context), MODEL_OUTPUT)
        command, prompt, timeout, schema = runner.calls[0]
        self.assertIn("--ephemeral", command)
        self.assertIn("--ignore-user-config", command)
        self.assertIn("--ignore-rules", command)
        self.assertEqual(command[-1], "-")
        self.assertEqual(schema, BELIEF_OUTPUT_SCHEMA)
        self.assertEqual(timeout, 300)
        self.assertIn(json.dumps(self.context, sort_keys=True, separators=(",", ":")), prompt)
        for forbidden in ('"regime"', '"beta"', '"driver"', '"future_return"'):
            self.assertNotIn(forbidden, prompt.lower())

    def test_invalid_json_is_rejected(self):
        provider = CodexCLIProvider(runner=RecordingRunner("not-json"))
        with self.assertRaisesRegex(ValueError, "not valid JSON"):
            provider(self.context)


if __name__ == "__main__":
    unittest.main()
