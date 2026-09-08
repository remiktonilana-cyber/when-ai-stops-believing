"""Deterministic tests for the provider-independent LLM adapter core."""

from copy import deepcopy
import unittest

import pandas as pd

from src.observation_builder import build_observation_sequence
from src.universal_llm_adapter import (
    assemble_runtime_context,
    run_llm_agent,
    validate_model_output,
)


def valid_model_output():
    return {
        "belief_status": "VALID",
        "confidence": 0.8,
        "explanation": "Deterministic fake-model response.",
        "evidence_summary": {
            "supporting_evidence": [],
            "contradicting_evidence": [],
        },
    }


class RecordingFakeModel:
    def __init__(self):
        self.context_checks = []

    def __call__(self, context):
        current = context["current_observation"]
        keys = str(context).lower()
        self.context_checks.append(
            {
                "timestamp": current["timestamp"],
                "previous": deepcopy(context["previous_belief_state"]),
                "recent_count": len(context["recent_resolved_evidence"]),
                "summary_count": context["historical_evidence_summary"][
                    "resolved_count"
                ],
                "hidden": any(
                    token in keys
                    for token in ("'regime'", "'beta'", "'driver'")
                ),
                "future": any(
                    token in keys
                    for token in ("'future_return'", "'future_price'")
                ),
                "resolutions": [
                    item["resolution_timestamp"]
                    for item in context["recent_resolved_evidence"]
                ],
            }
        )
        return valid_model_output()


class UniversalLLMAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        market = pd.read_csv("data/synthetic_market.csv")
        cls.observations = build_observation_sequence(market)

    def test_temporal_context_and_full_run(self):
        model = RecordingFakeModel()
        static_observations = deepcopy(self.observations)
        beliefs = run_llm_agent(self.observations, model)

        self.assertEqual(len(beliefs), 2000)
        self.assertEqual(self.observations, static_observations)
        self.assertIsNone(model.context_checks[0]["previous"])
        self.assertEqual(
            model.context_checks[1]["previous"],
            beliefs[0],
        )
        self.assertTrue(all(check["recent_count"] <= 50 for check in model.context_checks))
        self.assertGreater(model.context_checks[-1]["summary_count"], 50)
        self.assertFalse(any(check["hidden"] for check in model.context_checks))
        self.assertFalse(any(check["future"] for check in model.context_checks))
        self.assertTrue(
            all(
                resolution <= check["timestamp"]
                for check in model.context_checks
                for resolution in check["resolutions"]
            )
        )
        self.assertTrue(
            all(
                belief["timestamp"] == observation["timestamp"]
                for belief, observation in zip(beliefs, self.observations)
            )
        )
        self.assertTrue(all(len(belief) == 5 for belief in beliefs))

    def test_unresolved_outcome_is_not_available(self):
        contexts = []

        def fake_model(context):
            contexts.append(context)
            return valid_model_output()

        run_llm_agent(self.observations[20:22], fake_model)
        self.assertEqual(contexts[0]["recent_resolved_evidence"], [])
        self.assertEqual(len(contexts[1]["recent_resolved_evidence"]), 1)
        resolved = contexts[1]["recent_resolved_evidence"][0]
        self.assertEqual(resolved["prediction_timestamp"], self.observations[20]["timestamp"])
        self.assertEqual(resolved["resolution_timestamp"], self.observations[21]["timestamp"])
        self.assertNotIn("return", contexts[0]["current_observation"])

    def test_hidden_state_is_rejected(self):
        observation = deepcopy(self.observations[0])
        observation["regime"] = "VALID"
        with self.assertRaises(ValueError):
            assemble_runtime_context(observation, None, [])

    def test_adapter_owns_timestamp(self):
        output = valid_model_output()
        output["timestamp"] = "model-controlled"
        with self.assertRaises(ValueError):
            validate_model_output(output)

    def test_invalid_model_outputs_are_rejected(self):
        invalid_outputs = []

        missing = valid_model_output()
        missing.pop("confidence")
        invalid_outputs.append(missing)

        invalid_status = valid_model_output()
        invalid_status["belief_status"] = "MAYBE"
        invalid_outputs.append(invalid_status)

        invalid_confidence = valid_model_output()
        invalid_confidence["confidence"] = 1.1
        invalid_outputs.append(invalid_confidence)

        malformed_summary = valid_model_output()
        malformed_summary["evidence_summary"] = {"supporting_evidence": []}
        invalid_outputs.append(malformed_summary)

        malformed_lists = valid_model_output()
        malformed_lists["evidence_summary"]["supporting_evidence"] = "support"
        invalid_outputs.append(malformed_lists)

        for output in invalid_outputs:
            with self.subTest(output=output):
                with self.assertRaises(ValueError):
                    validate_model_output(output)


if __name__ == "__main__":
    unittest.main()
