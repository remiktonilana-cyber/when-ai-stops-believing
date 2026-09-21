"""Focused causal-contract regression tests; no provider calls."""

from copy import deepcopy
import unittest

from src.lai_agent_contract import (
    FORBIDDEN_FIELDS,
    MAX_RESOLVED_HISTORY,
    build_initialization_input,
    build_neutral_prompt,
    build_runtime_input,
)
from src.lai_agent_schema import AgentBelief
from src.lai_transition_environment import generate_transition


def previous_belief():
    return AgentBelief("UNCERTAIN", 0.4, "must not be forwarded", {
        "supporting_evidence": ["support"], "contradicting_evidence": ["challenge"]})


class AgentContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world = generate_transition(1000, 0.03)

    def test_runtime_input_has_causal_fields_only(self):
        result = build_runtime_input(self.world, 400, previous_belief())
        self.assertEqual(set(result), {"current_observation", "previous_belief", "resolved_history", "historical_summary"})
        self.assertEqual(set(result["current_observation"]), {
            "fragility", "crowding", "liquidity_stress", "context_signal", "current_shock"})
        self.assertFalse(FORBIDDEN_FIELDS.intersection(result["current_observation"]))
        self.assertNotIn("explanation", result["previous_belief"])

    def test_history_maximum_and_only_prior_rows(self):
        result = build_runtime_input(self.world, 349)
        self.assertEqual(len(result["resolved_history"]), MAX_RESOLVED_HISTORY)
        self.assertEqual(result["historical_summary"]["resolved_count"], 349)
        expected = [(float(self.world.iloc[i].shock), float(self.world.iloc[i].next_response))
                    for i in range(299, 349)]
        self.assertEqual(result["resolved_history"], expected)

    def test_current_response_and_future_values_are_absent(self):
        first = build_runtime_input(self.world, 400, previous_belief())
        mutated = self.world.copy(deep=True)
        mutated.loc[400, "next_response"] = 999999
        mutated.loc[401:, ["fragility", "crowding", "liquidity_stress", "nuisance", "shock", "next_response"]] = -777
        mutated.loc[:, ["latent_stress", "alpha"]] = 123456
        second = build_runtime_input(mutated, 400, previous_belief())
        self.assertEqual(first, second)
        self.assertNotIn("next_response", first["current_observation"])
        self.assertNotIn("response", first["current_observation"])

    def test_historical_summary_uses_only_resolved_prefix(self):
        first = build_runtime_input(self.world, 400)
        mutated = self.world.copy(deep=True)
        mutated.loc[400:, "next_response"] = 999999
        self.assertEqual(first["historical_summary"], build_runtime_input(mutated, 400)["historical_summary"])
        self.assertEqual(first["historical_summary"]["resolved_count"], 400)

    def test_initialization_day_349_is_future_and_hidden_free(self):
        result = build_initialization_input(self.world)
        self.assertEqual(result["historical_summary"]["resolved_count"], 349)
        self.assertEqual(len(result["resolved_history"]), 50)
        self.assertEqual(set(result), {"resolved_history", "historical_summary"})
        self.assertFalse(FORBIDDEN_FIELDS.intersection(result))
        for pair in result["resolved_history"]:
            self.assertEqual(len(pair), 2)

    def test_detached_initial_belief_can_be_copied_to_both_worlds(self):
        initial = previous_belief()
        transition_copy = deepcopy(initial)
        control_copy = deepcopy(initial)
        self.assertEqual(transition_copy, control_copy)
        self.assertIsNot(transition_copy, control_copy)

    def test_prompt_contains_epistemic_contract(self):
        prompt = build_neutral_prompt(build_runtime_input(self.world, 400, previous_belief()))
        self.assertIn("previously established shock-response relationship remains a reliable description", prompt)
        for status in ("VALID", "UNCERTAIN", "INVALID"):
            self.assertIn(status, prompt)
        self.assertIn("relevance and strength", prompt)
        self.assertIn("supporting_evidence", prompt)
        self.assertIn("contradicting_evidence", prompt)

    def test_prompt_excludes_forbidden_benchmark_language(self):
        prompt = build_neutral_prompt(build_runtime_input(self.world, 400))
        prohibited = (
            "LAI", "Latent Amplification State", "amplification regime", "hidden state",
            "structural transition", "regime change", "warning phase", "transition/control world",
            "alpha", "T_evidence", "failure taxonomy", "adaptation delay",
            "false persistence", "belief boundary awareness", "benchmark score",
        )
        lowered = prompt.lower()
        for phrase in prohibited:
            self.assertNotIn(phrase.lower(), lowered, phrase)


if __name__ == "__main__":
    unittest.main()
