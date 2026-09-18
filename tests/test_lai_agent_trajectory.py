"""Tests for causal LAI Agent trajectory storage."""

import unittest

from src.lai_agent_schema import AgentBelief, BeliefStatus
from src.lai_agent_trajectory import AgentTrajectory, TrajectoryStep


def belief():
    return AgentBelief(
        BeliefStatus.VALID,
        0.8,
        "The current relationship remains useful.",
        {"supporting_evidence": [], "contradicting_evidence": []},
    )


class AgentTrajectoryTests(unittest.TestCase):
    def test_append_length_and_order(self):
        trajectory = AgentTrajectory()
        trajectory.append(1, {"fragility": 0.2, "current_shock": 0.1}, belief())
        trajectory.append(2, {"fragility": 0.3, "current_shock": -0.2}, belief())

        self.assertEqual(len(trajectory), 2)
        self.assertEqual(trajectory.length, 2)
        steps = trajectory.steps()
        self.assertEqual([step.timestamp for step in steps], [1, 2])
        self.assertTrue(all(isinstance(step, TrajectoryStep) for step in steps))
        self.assertEqual(steps[0].observation["fragility"], 0.2)
        self.assertIsInstance(steps[0].belief, AgentBelief)

    def test_steps_are_detached_from_storage(self):
        trajectory = AgentTrajectory()
        observation = {"fragility": 0.2}
        trajectory.append(1, observation, belief())
        returned = trajectory.steps()
        returned[0].observation["fragility"] = 99
        self.assertEqual(trajectory.steps()[0].observation["fragility"], 0.2)

    def test_missing_timestamp_and_belief_rejected(self):
        trajectory = AgentTrajectory()
        with self.assertRaisesRegex(ValueError, "timestamp"):
            trajectory.append(None, {}, belief())
        with self.assertRaisesRegex(ValueError, "belief"):
            trajectory.append(1, {}, None)

    def test_backwards_or_unorderable_timestamp_rejected(self):
        trajectory = AgentTrajectory()
        trajectory.append(2, {}, belief())
        with self.assertRaisesRegex(ValueError, "chronological"):
            trajectory.append(1, {}, belief())
        with self.assertRaisesRegex(ValueError, "orderable"):
            trajectory.append("later", {}, belief())

    def test_forbidden_information_rejected_recursively(self):
        forbidden = (
            "alpha", "latent_state", "latent_stress", "T_warning", "T_structural",
            "T_delta", "T_evidence", "future_response", "future_observations",
        )
        for field in forbidden:
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, field):
                    AgentTrajectory().append(1, {"nested": {field: 1}}, belief())

        with self.assertRaisesRegex(ValueError, "future_response"):
            AgentTrajectory().append(
                1,
                {},
                AgentBelief(
                    BeliefStatus.VALID,
                    0.5,
                    "x",
                    {"supporting_evidence": [{"future_response": 1}], "contradicting_evidence": []},
                ),
            )


if __name__ == "__main__":
    unittest.main()
