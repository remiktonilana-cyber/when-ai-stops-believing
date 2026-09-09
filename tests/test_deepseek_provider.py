"""Offline tests for the DeepSeek provider wrapper."""

import json
import os
import unittest
from unittest.mock import patch

import pandas as pd

from src.deepseek_provider import DEFAULT_MODEL, DeepSeekProvider
from src.observation_builder import build_observation_sequence
from src.universal_llm_adapter import run_llm_agent


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
