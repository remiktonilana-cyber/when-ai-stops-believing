"""End-to-end engineering checks for the deterministic mock pipeline."""

import unittest
from unittest.mock import patch

from src.lai_mock_pipeline import (
    FORBIDDEN_AGENT_FIELDS,
    build_agent_observation,
    run_mock_pipeline,
)
from src.lai_transition_environment import generate_transition


class MockPipelineTests(unittest.TestCase):
    def test_end_to_end_pipeline_runs(self):
        result = run_mock_pipeline(seed=1000)
        self.assertEqual(len(result["transition_trajectory"]), 1200)
        self.assertEqual(len(result["control_trajectory"]), 1200)
        self.assertIn("T_U", result["transition_metrics"])
        self.assertIn("phase_occupancy", result["control_metrics"])
        self.assertIn("pre_divergence_agreement", result["paired_summary"])

    def test_transition_and_control_trajectories_created(self):
        result = run_mock_pipeline(seed=1001)
        self.assertEqual(result["transition_trajectory"].length, 1200)
        self.assertEqual(result["control_trajectory"].length, 1200)
        self.assertEqual(result["transition_trajectory"].steps()[0].timestamp, 0)
        self.assertEqual(result["control_trajectory"].steps()[-1].timestamp, 1199)

    def test_paired_evaluator_summary_is_descriptive(self):
        result = run_mock_pipeline(seed=1002)
        paired = result["paired_summary"]
        self.assertIn("first_status_divergence", paired)
        self.assertIn("control_abandonment", paired)
        self.assertNotIn("score", paired)
        self.assertNotIn("pass", paired)
        self.assertNotIn("rank", paired)

    def test_adapter_exposes_only_contract_fields(self):
        world = generate_transition(1000, 0.03)
        observation = build_agent_observation(world, 10)
        self.assertEqual(set(observation), {
            "fragility", "crowding", "liquidity_stress", "context_signal", "current_shock",
        })
        self.assertFalse(FORBIDDEN_AGENT_FIELDS.intersection(observation))

    def test_hidden_fields_not_passed_to_mock_agent(self):
        seen = []

        class RecordingAgent:
            def respond(self, observation, resolved_history, historical_summary):
                seen.append((observation.copy(), list(resolved_history), dict(historical_summary)))
                from src.lai_mock_agent import MockAgent
                return MockAgent().respond(observation, resolved_history, historical_summary)

        with patch("src.lai_mock_pipeline.MockAgent", RecordingAgent):
            run_mock_pipeline(seed=1003)
        self.assertEqual(len(seen), 2400)
        for observation, history, summary in seen:
            self.assertFalse(FORBIDDEN_AGENT_FIELDS.intersection(observation))
            self.assertTrue(all(len(pair) == 2 for pair in history))
            self.assertNotIn("alpha", summary)
            self.assertNotIn("latent_stress", summary)
            self.assertNotIn("future_response", summary)


if __name__ == "__main__":
    unittest.main()
