"""Offline tests for the DeepSeek provider wrapper."""

import json
import os
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import pandas as pd

from src.deepseek_provider import DEFAULT_MODEL, DeepSeekProvider
from src.lai_agent_contract import build_neutral_prompt
from src.lai_qwen_paired_experiment import run_paired_experiment
from src.lai_transition_environment import generate_transition
from src.lai_transition_reference import D_PLUS
from src.observation_builder import build_observation_sequence
from src.universal_llm_adapter import run_llm_agent, validate_model_output


MODEL_OUTPUT = {
    "belief_status": "VALID",
    "confidence": 0.75,
    "explanation": "Observable evidence remains supportive.",
    "evidence_summary": {
        "supporting_evidence": ["A resolved prediction was supported."],
        "contradicting_evidence": [],
    },
}


class RecordingTransport:
    def __init__(self, content=None):
        self.content = content if content is not None else json.dumps(MODEL_OUTPUT)
        self.payloads = []

    def __call__(self, payload, api_key, timeout):
        self.payloads.append(payload)
        return {
            "model": DEFAULT_MODEL,
            "choices": [{"message": {"role": "assistant", "content": self.content}}],
        }


class SequenceTransport:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.payloads = []

    def __call__(self, payload, api_key, timeout):
        self.payloads.append(payload)
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response


class DeepSeekProviderTests(unittest.TestCase):
    def test_missing_credential_is_rejected(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "DEEPSEEK_API_KEY"):
                DeepSeekProvider()

    def test_provider_builds_json_chat_request(self):
        transport = RecordingTransport()
        provider = DeepSeekProvider(api_key="test-key-not-real", transport=transport)
        context = {
            "current_observation": {"timestamp": "2000-01-03"},
            "previous_belief_state": None,
            "recent_resolved_evidence": [],
            "historical_evidence_summary": {
                "resolved_count": 0,
                "supporting_count": 0,
                "contradicting_count": 0,
                "success_rate": None,
            },
        }

        self.assertEqual(provider(context), MODEL_OUTPUT)
        payload = transport.payloads[0]
        self.assertEqual(payload["model"], DEFAULT_MODEL)
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        self.assertEqual(payload["thinking"], {"type": "disabled"})
        self.assertFalse(payload["stream"])
        self.assertEqual(json.loads(payload["messages"][1]["content"]), context)
        self.assertEqual(provider.last_response_model, DEFAULT_MODEL)

    def test_lai_prompt_builder_uses_frozen_prompt_and_legacy_path_is_separate(self):
        transport = RecordingTransport()
        context = {"resolved_history": [], "historical_summary": {"resolved_count": 0}}
        provider = DeepSeekProvider(
            api_key="test-key-not-real",
            transport=transport,
            prompt_builder=build_neutral_prompt,
        )

        provider(context)
        payload = transport.payloads[0]
        system_prompt = payload["messages"][0]["content"]
        self.assertEqual(system_prompt, build_neutral_prompt(context))
        self.assertIn(
            "previously established shock-response relationship remains a reliable description",
            system_prompt,
        )
        self.assertNotIn("market signal remains useful", system_prompt)
        self.assertEqual(payload["response_format"], {"type": "json_object"})

    def test_lai_output_still_requires_provider_independent_strict_validation(self):
        malformed = dict(MODEL_OUTPUT)
        malformed["evidence_summary"] = {
            "supporting_evidence": [],
            "unexpected": [],
        }
        provider = DeepSeekProvider(
            api_key="test-key-not-real",
            transport=RecordingTransport(json.dumps(malformed)),
            prompt_builder=build_neutral_prompt,
        )
        with self.assertRaisesRegex(ValueError, "evidence_summary fields"):
            validate_model_output(provider({}))

    def test_pre_response_failure_clears_previous_response_metadata(self):
        success = {
            "model": DEFAULT_MODEL,
            "choices": [{"message": {"content": json.dumps(MODEL_OUTPUT)}}],
        }
        transport = SequenceTransport([success, RuntimeError("transport failure")])
        provider = DeepSeekProvider(api_key="test-key-not-real", transport=transport)
        provider({})
        self.assertEqual(provider.last_response_model, DEFAULT_MODEL)
        with self.assertRaisesRegex(RuntimeError, "transport failure"):
            provider({})
        self.assertIsNone(provider.last_response_model)

    def test_lai_provider_hook_runs_causal_paired_runner_with_fake_transport(self):
        transport = RecordingTransport()
        provider = DeepSeekProvider(
            api_key="test-key-not-real",
            transport=transport,
            prompt_builder=build_neutral_prompt,
        )
        transition = generate_transition(1000, D_PLUS)
        control = generate_transition(1000, D_PLUS, control=True)
        with TemporaryDirectory() as directory:
            result = run_paired_experiment(
                provider,
                transition_world=transition,
                control_world=control,
                artifact_dir=directory,
                start=350,
                end=351,
                provider_name="deepseek",
                model=DEFAULT_MODEL,
            )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(len(transport.payloads), 5)  # init + two steps per world
        user_inputs = [json.loads(item["messages"][1]["content"]) for item in transport.payloads]
        self.assertEqual(user_inputs[0]["historical_summary"]["resolved_count"], 349)
        self.assertNotIn("next_response", user_inputs[1]["current_observation"])
        self.assertEqual(
            tuple(user_inputs[2]["resolved_history"][-1]),
            (float(transition.iloc[350]["shock"]), float(transition.iloc[350]["next_response"])),
        )
        self.assertEqual(user_inputs[1]["previous_belief"], user_inputs[3]["previous_belief"])
        self.assertNotIn("explanation", user_inputs[1]["previous_belief"])
        self.assertEqual(
            transport.payloads[1]["messages"][0]["content"],
            transport.payloads[3]["messages"][0]["content"],
        )

    def test_invalid_json_is_rejected(self):
        provider = DeepSeekProvider(
            api_key="test-key-not-real",
            transport=RecordingTransport("not-json"),
        )
        with self.assertRaisesRegex(ValueError, "not valid JSON"):
            provider({})

    def test_four_step_runtime_is_causal(self):
        market = pd.read_csv("data/synthetic_market.csv")
        observations = build_observation_sequence(market)[20:24]
        transport = RecordingTransport()
        provider = DeepSeekProvider(
            api_key="test-key-not-real",
            transport=transport,
        )

        beliefs = run_llm_agent(observations, provider)

        contexts = [
            json.loads(payload["messages"][1]["content"])
            for payload in transport.payloads
        ]
        self.assertEqual(len(beliefs), 4)
        self.assertIsNone(contexts[0]["previous_belief_state"])
        self.assertEqual(contexts[1]["previous_belief_state"], beliefs[0])
        self.assertEqual(contexts[0]["recent_resolved_evidence"], [])
        self.assertEqual(len(contexts[1]["recent_resolved_evidence"]), 1)
        self.assertTrue(
            all(
                belief["timestamp"] == observation["timestamp"]
                for belief, observation in zip(beliefs, observations)
            )
        )
        prompt_text = json.dumps(transport.payloads).lower()
        for forbidden in (
            '"regime"',
            '"beta"',
            '"driver"',
            '"future_return"',
            '"future_price"',
        ):
            self.assertNotIn(forbidden, prompt_text)


if __name__ == "__main__":
    unittest.main()
