"""Focused tests for the provider-independent LAI belief schema."""

import unittest

from src.lai_agent_schema import AgentBelief, BeliefStatus, MAX_EVIDENCE_ITEMS


def evidence(supporting=None, contradicting=None):
    return {
        "supporting_evidence": [] if supporting is None else supporting,
        "contradicting_evidence": [] if contradicting is None else contradicting,
    }


class AgentBeliefTests(unittest.TestCase):
    def test_valid_belief_creation(self):
        belief = AgentBelief(
            status=BeliefStatus.VALID,
            confidence=0.8,
            explanation="The current relationship remains useful.",
            evidence_summary=evidence(["recent support"]),
        )
        self.assertEqual(belief.status, BeliefStatus.VALID)
        self.assertEqual(belief.confidence, 0.8)
        self.assertEqual(belief.evidence_summary["supporting_evidence"], ["recent support"])

        string_status = AgentBelief("UNCERTAIN", 0.5, "warning", evidence())
        self.assertIs(string_status.status, BeliefStatus.UNCERTAIN)

    def test_invalid_status_rejected(self):
        with self.assertRaisesRegex(ValueError, "status"):
            AgentBelief("UNKNOWN", 0.5, "explanation", evidence())

    def test_confidence_outside_range_rejected(self):
        for confidence in (-0.01, 1.01, float("nan"), float("inf"), True):
            with self.subTest(confidence=confidence), self.assertRaises(ValueError):
                AgentBelief(BeliefStatus.VALID, confidence, "explanation", evidence())

    def test_evidence_summary_size_validation(self):
        valid = AgentBelief(
            BeliefStatus.VALID,
            0.5,
            "explanation",
            evidence(["support"] * MAX_EVIDENCE_ITEMS),
        )
        self.assertEqual(len(valid.evidence_summary["supporting_evidence"]), MAX_EVIDENCE_ITEMS)

        with self.assertRaisesRegex(ValueError, "50"):
            AgentBelief(
                BeliefStatus.VALID,
                0.5,
                "explanation",
                evidence(["support"] * (MAX_EVIDENCE_ITEMS + 1)),
            )

        with self.assertRaises(ValueError):
            AgentBelief(BeliefStatus.VALID, 0.5, "explanation", {"supporting_evidence": []})


if __name__ == "__main__":
    unittest.main()
