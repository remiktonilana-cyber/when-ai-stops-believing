"""Integration contract checks with no providers or scientific evaluators."""

from copy import deepcopy
from dataclasses import replace
import unittest

from src.decision_gate import DecisionRequest, evaluate
from src.lai_agent_schema import AgentBelief
from src.reliability_adapter import ReliabilityObservation, to_decision_request


def belief():
    return AgentBelief("VALID", 0.8, "Existing belief", {
        "supporting_evidence": [{"observation": "support"}],
        "contradicting_evidence": ["contradiction"],
    })


def request(observation, **changes):
    context = dict(
        action_id="a1", proposed_action="Proposed action",
        context_shift=False, data_quality="GOOD", data_freshness="FRESH",
        system_health="HEALTHY", consequence_level="LOW", reversibility="HIGH",
    )
    context.update(changes)
    return to_decision_request(observation, **context)


class ReliabilityAdapterTests(unittest.TestCase):
    def observation(self, **changes):
        return ReliabilityObservation.from_agent_belief(
            belief(), evidence_conflict=False, belief_persistence=3, **changes)

    def test_valid_observation_creates_request(self):
        observation = self.observation()
        result = request(observation)
        self.assertIsInstance(result, DecisionRequest)
        for field in ("belief_status", "confidence", "evidence_conflict", "belief_persistence"):
            self.assertEqual(getattr(result, field), getattr(observation, field))
        self.assertEqual(evaluate(result).permission, "GREEN")

    def test_explicit_conflict_preserved_without_inference(self):
        for conflict, permission in ((True, "YELLOW"), (False, "GREEN"), (None, "RED")):
            with self.subTest(conflict=conflict):
                observation = ReliabilityObservation.from_agent_belief(
                    belief(), evidence_conflict=conflict, belief_persistence=3)
                result = request(observation)
                self.assertIs(result.evidence_conflict, conflict)
                self.assertEqual(evaluate(result).permission, permission)
                self.assertEqual(observation.contradicting_evidence, ("contradiction",))

    def test_missing_information_is_explicit_and_safe(self):
        observation = ReliabilityObservation.from_agent_belief(belief())
        for field in ("evidence_conflict", "belief_persistence", "timestamp", "provenance"):
            self.assertIsNone(getattr(observation, field))
        decision = evaluate(request(observation))
        self.assertEqual(decision.permission, "RED")
        self.assertIn("evidence_conflict", decision.assessment.missing_fields)
        self.assertIn("belief_persistence", decision.assessment.missing_fields)
        empty = ReliabilityObservation()
        self.assertIsNone(empty.supporting_evidence)
        self.assertIsNone(empty.contradicting_evidence)
        self.assertEqual(evaluate(request(empty)).permission, "RED")
        # Metadata is optional and its absence alone does not block.
        self.assertEqual(evaluate(request(self.observation())).permission, "GREEN")

    def test_no_application_defaults_favor_execution(self):
        result = to_decision_request(self.observation(), action_id="a", proposed_action="x")
        for field in ("context_shift", "data_quality", "data_freshness", "system_health",
                      "consequence_level", "reversibility"):
            self.assertIsNone(getattr(result, field))
        self.assertEqual(evaluate(result).permission, "RED")

    def test_original_belief_and_nested_data_are_not_changed_or_aliased(self):
        original = belief()
        before = deepcopy(original)
        provenance = {"source": ["record-1"]}
        observation = ReliabilityObservation.from_agent_belief(
            original, provenance=provenance, timestamp=12)
        request(observation)
        self.assertEqual(original, before)
        observation.supporting_evidence[0]["observation"] = "changed"
        observation.provenance["source"].append("other")
        self.assertEqual(original, before)
        self.assertEqual(provenance, {"source": ["record-1"]})
        original.evidence_summary["contradicting_evidence"].append("later")
        self.assertEqual(observation.contradicting_evidence, ("contradiction",))
        self.assertEqual(observation.timestamp, 12)

    def test_same_observation_different_context(self):
        observation = self.observation()
        self.assertEqual(evaluate(request(observation)).permission, "GREEN")
        high = request(observation, consequence_level="HIGH", reversibility="LOW")
        self.assertEqual(evaluate(high).permission, "YELLOW")
        self.assertTrue(evaluate(high).requires_human_review)

    def test_translation_does_not_assess_or_normalize_signals(self):
        observation = replace(self.observation(), belief_status="INVALID", confidence=1.0)
        result = request(observation, policy_version="future")
        self.assertEqual(result.belief_status, "INVALID")
        self.assertEqual(result.confidence, 1.0)
        self.assertEqual(result.consequence_level, "LOW")
        self.assertEqual(result.policy_version, "future")
        self.assertFalse(hasattr(result, "permission"))
        malformed = request(replace(observation, evidence_conflict="false"))
        self.assertEqual(malformed.evidence_conflict, "false")
        with self.assertRaises(ValueError):
            evaluate(malformed)

    def test_empty_evidence_remains_distinct_from_unavailable(self):
        observation = ReliabilityObservation(supporting_evidence=[], contradicting_evidence=[])
        self.assertEqual(observation.supporting_evidence, ())
        self.assertEqual(observation.contradicting_evidence, ())
        self.assertIsNone(observation.evidence_conflict)

    def test_wrong_container_types_rejected(self):
        with self.assertRaises(TypeError):
            ReliabilityObservation.from_agent_belief({})
        with self.assertRaises(TypeError):
            request({})
        with self.assertRaises(ValueError):
            ReliabilityObservation(supporting_evidence="text")


if __name__ == "__main__":
    unittest.main()
