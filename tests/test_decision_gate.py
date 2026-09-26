"""Safety invariants for the offline, provider-neutral permission policy."""

from dataclasses import FrozenInstanceError, fields, replace
import unittest

from src.decision_gate import DecisionRequest, POLICY_VERSION, evaluate
from src.lai_agent_schema import BeliefStatus


def favorable(**changes):
    request = DecisionRequest(
        action_id="action-1", proposed_action="Update a reversible draft",
        belief_status=BeliefStatus.VALID, confidence=0.8,
        evidence_conflict=False, belief_persistence=3, context_shift=False,
        data_quality="GOOD", data_freshness="FRESH", system_health="HEALTHY",
        consequence_level="LOW", reversibility="HIGH",
    )
    return replace(request, **changes)


class DecisionGateTests(unittest.TestCase):
    def test_favorable_low_impact_is_green_and_scoped(self):
        request = favorable()
        decision = evaluate(request)
        self.assertEqual(decision.permission, "GREEN")
        self.assertEqual(decision.reason_codes, ("POLICY_REQUIREMENTS_MET",))
        self.assertFalse(decision.requires_human_review)
        self.assertEqual(decision.action_id, request.action_id)
        self.assertEqual(decision.proposed_action, request.proposed_action)
        self.assertEqual(decision.policy_version, POLICY_VERSION)
        self.assertEqual(decision, evaluate(request))

    def test_each_review_condition_prevents_automatic_execution(self):
        cases = (
            ("evidence_conflict", True, "EVIDENCE_CONFLICT"),
            ("context_shift", True, "CONTEXT_SHIFT"),
            ("belief_status", "UNCERTAIN", "BELIEF_UNCERTAIN"),
            ("data_quality", "DEGRADED", "DEGRADED_REQUIRED_DATA"),
            ("consequence_level", "HIGH", "HIGH_CONSEQUENCE"),
            ("reversibility", "LOW", "LOW_REVERSIBILITY"),
        )
        for field, value, reason in cases:
            with self.subTest(field=field):
                decision = evaluate(favorable(**{field: value}))
                self.assertEqual(decision.permission, "YELLOW")
                self.assertTrue(decision.requires_human_review)
                self.assertIn(reason, decision.reason_codes)
                self.assertIn("HUMAN_REVIEW_REQUIRED", decision.reason_codes)

    def test_hard_blocks_override_favorable_and_review_signals(self):
        for field, value, reason in (
            ("system_health", "UNHEALTHY", "SYSTEM_UNHEALTHY"),
            ("data_freshness", "STALE", "STALE_REQUIRED_DATA"),
            ("data_quality", "UNUSABLE", "UNUSABLE_REQUIRED_DATA"),
            ("belief_status", "INVALID", "BELIEF_INVALID"),
        ):
            for conflict in (False, True):
                with self.subTest(field=field, conflict=conflict):
                    decision = evaluate(favorable(**{field: value}, evidence_conflict=conflict))
                    self.assertEqual(decision.permission, "RED")
                    self.assertIn(reason, decision.assessment.blocking_reasons)
                    self.assertFalse(decision.requires_human_review)
                    self.assertNotIn("HUMAN_REVIEW_REQUIRED", decision.reason_codes)

    def test_every_unavailable_signal_blocks(self):
        for field in fields(DecisionRequest):
            if field.name in ("action_id", "proposed_action"):
                continue
            with self.subTest(field=field.name):
                decision = evaluate(favorable(**{field.name: None}))
                self.assertEqual(decision.permission, "RED")
                self.assertIn(field.name, decision.assessment.missing_fields)
                self.assertIn("MISSING_REQUIRED_INFORMATION", decision.reason_codes)
        self.assertEqual(evaluate(DecisionRequest("a", "draft")).permission, "RED")

    def test_same_belief_different_decision_context(self):
        low = favorable()
        high = replace(low, consequence_level="HIGH", reversibility="LOW")
        self.assertEqual(evaluate(low).permission, "GREEN")
        decision = evaluate(high)
        self.assertEqual(decision.permission, "YELLOW")
        self.assertTrue(decision.requires_human_review)
        self.assertIn("HIGH_CONSEQUENCE", decision.reason_codes)
        self.assertIn("LOW_REVERSIBILITY", decision.reason_codes)

    def test_confidence_and_persistence_do_not_authorize(self):
        for confidence in (0.0, 0.5, 1.0):
            for persistence in (0, 1000):
                for status, permission in (("VALID", "GREEN"), ("UNCERTAIN", "YELLOW"), ("INVALID", "RED")):
                    with self.subTest(confidence=confidence, persistence=persistence, status=status):
                        self.assertEqual(evaluate(favorable(
                            confidence=confidence, belief_persistence=persistence,
                            belief_status=status)).permission, permission)

    def test_unknown_policy_blocks(self):
        for changes in ({"policy_id": "other"}, {"policy_version": "2"}):
            decision = evaluate(favorable(**changes))
            self.assertEqual(decision.permission, "RED")
            self.assertIn("UNSUPPORTED_POLICY", decision.reason_codes)
            self.assertEqual(decision.policy_version, POLICY_VERSION)

    def test_malformed_inputs_rejected(self):
        cases = {
            "action_id": (None, "", " "), "proposed_action": (None, 1, ""),
            "belief_status": ("UNKNOWN", 1),
            "confidence": (True, "0.8", -0.1, 1.1, float("nan"), float("inf")),
            "evidence_conflict": (0, "false"), "context_shift": (1, "false"),
            "belief_persistence": (True, -1, 1.5),
            "data_quality": ("unknown",), "data_freshness": (True,),
            "system_health": ("unknown",), "consequence_level": ("MEDIUM",),
            "reversibility": (False,), "policy_id": ("",), "policy_version": (1,),
        }
        for field, values in cases.items():
            for value in values:
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    evaluate(favorable(**{field: value}))
        with self.assertRaises(TypeError):
            evaluate({})

    def test_no_ordinary_confirmation_bypass(self):
        request = favorable(system_health="UNHEALTHY")
        with self.assertRaises(TypeError):
            evaluate(request, human_confirmed=True)
        decision = evaluate(request)
        with self.assertRaises(FrozenInstanceError):
            decision.permission = "GREEN"
        self.assertEqual(evaluate(request).permission, "RED")


if __name__ == "__main__":
    unittest.main()
