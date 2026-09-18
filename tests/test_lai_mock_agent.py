"""Pipeline-only tests for the deterministic LAI mock Agent."""

import unittest

from src.lai_agent_schema import AgentBelief, BeliefStatus
from src.lai_mock_agent import MockAgent


def observation(value=0.3):
    return {
        "fragility": value,
        "crowding": value,
        "liquidity_stress": value,
        "context_signal": 0.0,
        "current_shock": 0.1,
    }


class MockAgentTests(unittest.TestCase):
    def test_normal_input_returns_valid(self):
        belief = MockAgent().respond(observation())
        self.assertEqual(belief.status, BeliefStatus.VALID)

    def test_warning_input_returns_uncertain(self):
        belief = MockAgent().respond(observation(0.8))
        self.assertEqual(belief.status, BeliefStatus.UNCERTAIN)

    def test_contradiction_input_returns_invalid(self):
        history = [(1.0, 2.0), (-1.0, -2.0), (0.5, 1.5)]
        belief = MockAgent().respond(observation(0.3), history)
        self.assertEqual(belief.status, BeliefStatus.INVALID)

    def test_output_conforms_to_agent_belief_schema(self):
        belief = MockAgent()(observation())
        self.assertIsInstance(belief, AgentBelief)
        self.assertIn(belief.status, tuple(BeliefStatus))
        self.assertGreaterEqual(belief.confidence, 0.0)
        self.assertLessEqual(belief.confidence, 1.0)

    def test_contradiction_takes_precedence_over_warning(self):
        history = [{"shock": 0.0, "response": 1.0}] * 3
        belief = MockAgent().respond(observation(0.95), history)
        self.assertEqual(belief.status, BeliefStatus.INVALID)

    def test_missing_observation_field_rejected(self):
        incomplete = observation()
        del incomplete["context_signal"]
        with self.assertRaisesRegex(ValueError, "context_signal"):
            MockAgent().respond(incomplete)


if __name__ == "__main__":
    unittest.main()
