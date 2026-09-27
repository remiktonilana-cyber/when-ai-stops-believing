"""Facade identity and policy checks; installation is verified separately."""

from dataclasses import replace
import unittest

from src import decision_gate, lai_agent_schema, reliability_adapter
import when_ai_stops_believing as public
from when_ai_stops_believing import reliability


class PublicAPITests(unittest.TestCase):
    def test_gate_exports_are_original_objects(self):
        for name in ("DecisionRequest", "GateDecision", "evaluate"):
            self.assertIs(getattr(public, name), getattr(decision_gate, name))

    def test_adapter_exports_are_original_objects(self):
        for name in ("AgentBelief", "BeliefStatus"):
            self.assertIs(getattr(reliability, name), getattr(lai_agent_schema, name))
        for name in ("ReliabilityObservation", "to_decision_request"):
            self.assertIs(getattr(reliability, name), getattr(reliability_adapter, name))

    def test_public_policy_outcomes(self):
        request = public.DecisionRequest(
            action_id="draft-1", proposed_action="Update a reversible draft",
            belief_status="VALID", confidence=0.8, evidence_conflict=False,
            belief_persistence=3, context_shift=False, data_quality="GOOD",
            data_freshness="FRESH", system_health="HEALTHY",
            consequence_level="LOW", reversibility="HIGH",
        )
        cases = (
            (request, "GREEN", "POLICY_REQUIREMENTS_MET"),
            (replace(request, context_shift=True), "YELLOW", "CONTEXT_SHIFT"),
            (replace(request, system_health="UNHEALTHY"), "RED", "SYSTEM_UNHEALTHY"),
            (replace(request, evidence_conflict=None), "RED", "MISSING_REQUIRED_INFORMATION"),
        )
        for candidate, permission, reason in cases:
            with self.subTest(permission=permission, reason=reason):
                result = public.evaluate(candidate)
                self.assertIsInstance(result, public.GateDecision)
                self.assertEqual(result.permission, permission)
                self.assertIn(reason, result.reason_codes)
                self.assertEqual(result.policy_version, "1")


if __name__ == "__main__":
    unittest.main()
