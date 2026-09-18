"""Focused deterministic tests for LAI belief metrics."""

import unittest

from src.lai_agent_schema import AgentBelief
from src.lai_agent_trajectory import AgentTrajectory
from src.lai_belief_metrics import (
    compute_phase_occupancy, compute_post_evidence_valid_ratio,
    compute_relative_timing, compute_timing_metrics, compute_transition_matrix,
    find_invalid_episodes,
)


def make_trajectory(statuses, confidence=0.8):
    trajectory = AgentTrajectory()
    for timestamp, status in enumerate(statuses):
        trajectory.append(timestamp, {"fragility": 0.5}, AgentBelief(
            status, confidence, "test", {"supporting_evidence": [], "contradicting_evidence": []}))
    return trajectory.steps()


class BeliefMetricsTests(unittest.TestCase):
    def test_first_uncertainty_and_invalidation(self):
        timing = compute_timing_metrics(make_trajectory(["VALID", "VALID", "UNCERTAIN", "UNCERTAIN", "INVALID"]))
        self.assertEqual((timing["T_U"], timing["T_I"]), (2, 4))
        self.assertIsNone(timing["T_SI_onset"])
        self.assertEqual(compute_relative_timing(timing, 4), {"T_U_relative": -2, "T_I_relative": 0})

    def test_stable_invalidation_20_step_rule(self):
        timing = compute_timing_metrics(make_trajectory(["VALID"] + ["INVALID"] * 20 + ["VALID"]))
        self.assertEqual((timing["T_SI_onset"], timing["T_SI_confirmed"]), (1, 20))

    def test_nineteen_invalid_steps_do_not_trigger(self):
        self.assertIsNone(compute_timing_metrics(make_trajectory(["VALID"] + ["INVALID"] * 19 + ["VALID"]))["T_SI_onset"])

    def test_transition_matrix(self):
        statuses = ["VALID", "UNCERTAIN", "VALID", "INVALID", "VALID", "UNCERTAIN", "INVALID", "UNCERTAIN", "VALID"]
        self.assertEqual(compute_transition_matrix(make_trajectory(statuses)), {
            "VALID->UNCERTAIN": 2, "VALID->INVALID": 1, "UNCERTAIN->VALID": 2,
            "UNCERTAIN->INVALID": 1, "INVALID->VALID": 1, "INVALID->UNCERTAIN": 1})

    def test_invalid_episodes(self):
        statuses = ["VALID"] * 2 + ["INVALID"] * 2 + ["VALID"] + ["INVALID"] * 3
        self.assertEqual(find_invalid_episodes(make_trajectory(statuses)), [
            {"start": 2, "end": 3, "length": 2}, {"start": 5, "end": 7, "length": 3}])

    def test_phase_occupancy(self):
        statuses = ["VALID"] * 951
        statuses[350:400] = ["UNCERTAIN"] * 50
        statuses[400:600] = ["INVALID"] * 200
        statuses[600:675] = ["VALID"] * 75
        statuses[675:710] = ["UNCERTAIN"] * 35
        occupancy = compute_phase_occupancy(make_trajectory(statuses))
        self.assertEqual(occupancy["350-399"]["UNCERTAIN_percentage"], 100.0)
        self.assertEqual(occupancy["400-599"]["INVALID_percentage"], 100.0)
        self.assertEqual(occupancy["600-674"]["VALID_percentage"], 100.0)
        self.assertEqual(occupancy["675-709"]["UNCERTAIN_percentage"], 100.0)
        self.assertEqual(occupancy["710-899"]["VALID_percentage"], 100.0)
        self.assertEqual(occupancy["900-950"]["VALID_percentage"], 100.0)

    def test_post_evidence_valid_ratio(self):
        statuses = ["UNCERTAIN"] * 710 + ["VALID"] * 120 + ["INVALID"] * 121
        self.assertEqual(compute_post_evidence_valid_ratio(make_trajectory(statuses)), 120 / 241)


if __name__ == "__main__":
    unittest.main()
