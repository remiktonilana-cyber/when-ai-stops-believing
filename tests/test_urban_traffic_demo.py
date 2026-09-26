"""Offline application integration and execution enforcement checks."""

from copy import deepcopy
from dataclasses import asdict, replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from applications.urban_traffic.adapter import build_request
from applications.urban_traffic.fixtures import scenarios
from applications.urban_traffic.run_demo import run_demo
from applications.urban_traffic.simulator import run_scenario
from applications.urban_traffic.visualization import LABEL, render_report
from src.decision_gate import evaluate


class UrbanTrafficTests(unittest.TestCase):
    def test_green_executes_once(self):
        scenario = scenarios()[0]
        result = run_scenario(scenario)
        self.assertEqual(result["decision"]["permission"], "GREEN")
        self.assertEqual(result["execution_result"], "EXECUTED")
        self.assertEqual(scenario.state.ns_green, 35)
        self.assertEqual(scenario.state.ew_green, 30)
        after = deepcopy(scenario.state)
        self.assertEqual(run_scenario(scenario)["execution_result"], "ALREADY_EXECUTED")
        self.assertEqual(scenario.state, after)
        self.assertEqual(len(scenario.state.executed_actions), 1)

    def test_yellow_and_red_do_not_mutate(self):
        for scenario, permission, execution in zip(scenarios()[1:], ("YELLOW", "RED"), ("HELD", "BLOCKED")):
            with self.subTest(permission=permission):
                before = deepcopy(scenario.state)
                result = run_scenario(scenario)
                self.assertEqual(result["decision"]["permission"], permission)
                self.assertEqual(result["execution_result"], execution)
                self.assertEqual(scenario.state, before)
                self.assertEqual(result["before"], result["after"])

    def test_same_belief_context_changes_permissions_and_reasons(self):
        fixtures = scenarios()
        self.assertEqual(len(fixtures), 3)
        self.assertTrue(all(s.belief == fixtures[0].belief for s in fixtures))
        expected = (("GREEN", ("POLICY_REQUIREMENTS_MET",)),
                    ("YELLOW", ("CONTEXT_SHIFT", "HUMAN_REVIEW_REQUIRED")),
                    ("RED", ("SYSTEM_UNHEALTHY",)))
        for scenario, (permission, reasons) in zip(fixtures, expected):
            result = run_scenario(scenario)
            self.assertEqual(result["decision"]["permission"], permission)
            self.assertEqual(result["decision"]["reason_codes"], reasons)

    def test_no_state_leakage(self):
        fixtures = scenarios()
        untouched = deepcopy(fixtures[1:])
        run_scenario(fixtures[0])
        self.assertEqual(fixtures[1:], untouched)
        self.assertEqual(scenarios()[0].state.ns_green, 30)
        self.assertEqual(scenarios()[0].state.executed_actions, [])

    def test_mapping_missing_stale_and_invalid_data(self):
        for field, value, request_field, expected in (
            ("ns_queue", None, "data_quality", None),
            ("ew_queue", -1, "data_quality", "UNUSABLE"),
            ("observation_step", None, "data_freshness", None),
            ("observation_step", 2, "data_freshness", "STALE"),
            ("observation_step", 4, "data_quality", "UNUSABLE"),
            ("context_shift", None, "context_shift", None),
        ):
            with self.subTest(field=field, value=value):
                scenario = scenarios()[0]
                setattr(scenario.state, field, value)
                observation, request = build_request(scenario)
                self.assertEqual(getattr(request, request_field), expected)
                self.assertEqual(observation.confidence, scenario.belief.confidence)
                self.assertEqual(evaluate(request).permission, "RED")

    def test_invalid_input_and_out_of_scope_action_do_not_mutate(self):
        for change in ("invalid_request", "phase", "target", "cycle"):
            scenario = scenarios()[0]
            if change == "invalid_request":
                scenario.state.context_shift = "false"
            else:
                changes = {"phase": {"phase": "EW"}, "target": {"to_seconds": 100},
                           "cycle": {"cycle": 8}}[change]
                scenario.proposal = replace(scenario.proposal, **changes)
            before = deepcopy(scenario.state)
            with self.subTest(change=change), self.assertRaises(ValueError):
                run_scenario(scenario)
            self.assertEqual(scenario.state, before)

    def test_gate_scope_mismatch_does_not_mutate(self):
        for changes in ({"action_id": "other"}, {"proposed_action": "other"}):
            scenario = scenarios()[0]
            before = deepcopy(scenario.state)
            _, request = build_request(scenario)
            wrong = replace(evaluate(request), **changes)
            with patch("applications.urban_traffic.simulator.decision_gate.evaluate", return_value=wrong):
                with self.assertRaises(ValueError):
                    run_scenario(scenario)
            self.assertEqual(scenario.state, before)

    def test_existing_gate_result_is_used_unchanged(self):
        for scenario in scenarios():
            _, request = build_request(scenario)
            expected = asdict(evaluate(request))
            self.assertEqual(run_scenario(scenario)["decision"], expected)

    def test_outputs_and_visualization_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            results = run_demo(directory)
            stored = json.loads((Path(directory) / "demo_results.json").read_text())
            self.assertEqual([r["execution_result"] for r in stored], ["EXECUTED", "HELD", "BLOCKED"])
            html = (Path(directory) / "index.html").read_text()
            self.assertIn(LABEL, html)
            for field in ("Traffic situation", "Traffic state", "Scripted AI proposal", "Belief status",
                          "Confidence", "Permission", "Reason codes", "Execution result", "Timing before"):
                self.assertIn(field, html)
            for result in results:
                self.assertIn(result["scenario"], html)
                self.assertIn(result["decision"]["permission"], html)
                for reason in result["decision"]["reason_codes"]:
                    self.assertIn(reason, html)
            self.assertNotIn("<script", html)
            self.assertNotIn("https://", html)
            results[0]["situation"] = "<script>alert(1)</script>"
            self.assertIn("&lt;script&gt;", render_report(results))


if __name__ == "__main__":
    unittest.main()
