"""Offline orchestration tests; no real provider calls."""

import copy
import unittest

from src.lai_qwen_smoke import run_qwen_smoke
from src.lai_transition_environment import generate_transition


VALID = {
    "belief_status": "VALID", "confidence": 0.8,
    "explanation": "The relationship remains useful.",
    "evidence_summary": {"supporting_evidence": [], "contradicting_evidence": []},
}


class FakeProvider:
    model = "fake"

    def __init__(self, outputs=None):
        self.outputs = list(outputs or [VALID, VALID, VALID])
        self.inputs = []

    def __call__(self, agent_input):
        self.inputs.append(copy.deepcopy(agent_input))
        return copy.deepcopy(self.outputs.pop(0))


class QwenSmokeTests(unittest.TestCase):
    def test_three_call_order_and_causal_boundaries(self):
        provider = FakeProvider()
        result = run_qwen_smoke(seed=1000, provider=provider)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(len(provider.inputs), 3)
        self.assertEqual([len(item["resolved_history"]) for item in provider.inputs], [50, 50, 50])
        self.assertNotIn("current_observation", provider.inputs[0])
        self.assertEqual(set(provider.inputs[1]["current_observation"]), {
            "fragility", "crowding", "liquidity_stress", "context_signal", "current_shock"})
        self.assertNotIn("explanation", provider.inputs[1]["previous_belief"])
        self.assertNotIn("explanation", provider.inputs[2]["previous_belief"])
        world = generate_transition(1000, 0.03)
        self.assertEqual(provider.inputs[2]["resolved_history"][-1],
                         (float(world.iloc[350].shock), float(world.iloc[350].next_response)))
        self.assertTrue(result["day351_gained_day350_pair"])
        self.assertTrue(result["day351_current_response_absent"])

    def test_initial_non_valid_stops_without_retry_or_runtime_calls(self):
        output = dict(VALID, belief_status="UNCERTAIN")
        provider = FakeProvider([output, VALID, VALID])
        result = run_qwen_smoke(seed=1000, provider=provider)
        self.assertEqual(result["status"], "INITIAL BELIEF NOT ESTABLISHED")
        self.assertEqual(len(provider.inputs), 1)
        self.assertEqual(result["real_provider_calls"], 1)

    def test_output_schema_is_required(self):
        provider = FakeProvider([dict(VALID, confidence=2.0)])
        result = run_qwen_smoke(seed=1000, provider=provider)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["failure_type"], "ValueError")


if __name__ == "__main__":
    unittest.main()
