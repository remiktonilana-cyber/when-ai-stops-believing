"""Tests for descriptive matched-trajectory comparisons."""

import unittest

from src.lai_agent_schema import AgentBelief
from src.lai_agent_trajectory import AgentTrajectory, TrajectoryStep
from src.lai_paired_evaluator import (
    compare_paired_trajectories,
    control_abandonment,
    first_status_divergence,
    pre_divergence_agreement,
)


def trajectory(statuses, confidences=None, hidden=None):
    confidences = confidences or [0.8] * len(statuses)
    result = AgentTrajectory()
    for timestamp, (status, confidence) in enumerate(zip(statuses, confidences)):
        observation = {"fragility": 0.5, "crowding": 0.5, "liquidity_stress": 0.5}
        if hidden:
            observation.update(hidden)
        result.append(timestamp, observation, AgentBelief(
            status, confidence, "test", {"supporting_evidence": [], "contradicting_evidence": []}))
    return result.steps()


class PairedEvaluatorTests(unittest.TestCase):
    def test_identical_trajectories_full_agreement(self):
        statuses = ["VALID"] * 600
        summary = compare_paired_trajectories(trajectory(statuses), trajectory(statuses))
        agreement = summary["pre_divergence_agreement"]
        self.assertEqual(agreement["n_compared"], 250)
        self.assertEqual(agreement["status_agreement_rate"], 1.0)
        self.assertEqual(agreement["confidence_mean_absolute_difference"], 0.0)
        self.assertIsNone(summary["first_status_divergence"])
        self.assertEqual(summary["control_abandonment"], {
            "entered_invalid": False, "first_invalid_timestamp": None})

    def test_controlled_divergence_detected(self):
        transition_statuses = ["VALID"] * 400 + ["UNCERTAIN"] + ["VALID"] * 199
        control_statuses = ["VALID"] * 600
        summary = compare_paired_trajectories(
            trajectory(transition_statuses), trajectory(control_statuses))
        self.assertEqual(summary["first_status_divergence"], {
            "timestamp": 400, "transition_status": "UNCERTAIN", "control_status": "VALID"})
        agreement = summary["pre_divergence_agreement"]
        self.assertEqual(agreement["status_agreement_count"], 249)
        self.assertEqual(agreement["status_agreement_rate"], 249 / 250)

    def test_control_invalidation_detection(self):
        control_statuses = ["VALID"] * 10 + ["INVALID"] * 5
        self.assertEqual(control_abandonment(trajectory(control_statuses)), {
            "entered_invalid": True, "first_invalid_timestamp": 10})

    def test_confidence_comparison(self):
        transition = trajectory(["VALID"] * 600, [0.8] * 500 + [0.7] * 100)
        control = trajectory(["VALID"] * 600, [0.8] * 500 + [0.6] * 100)
        agreement = pre_divergence_agreement(transition, control)
        self.assertEqual(agreement["confidence_exact_agreement_count"], 150)
        self.assertAlmostEqual(agreement["confidence_mean_absolute_difference"], 0.04)
        self.assertAlmostEqual(agreement["confidence_max_absolute_difference"], 0.1)

    def test_hidden_observation_fields_do_not_affect_results(self):
        statuses = ["VALID"] * 400 + ["UNCERTAIN"] * 200
        plain = compare_paired_trajectories(trajectory(statuses), trajectory(statuses))
        def raw(hidden):
            return [TrajectoryStep(i, {**hidden, "fragility": 0.5}, AgentBelief(
                status, 0.8, "test",
                {"supporting_evidence": [], "contradicting_evidence": []}))
                    for i, status in enumerate(statuses)]
        hidden = compare_paired_trajectories(
            raw({"alpha": 999, "latent_stress": -999}),
            raw({"alpha": 1, "latent_stress": 0}),
        )
        self.assertEqual(plain, hidden)


if __name__ == "__main__":
    unittest.main()
