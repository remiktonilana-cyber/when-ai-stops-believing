"""Offline tests for the minimal OpenAI provider wrapper."""

import json
import os
import unittest
from unittest.mock import patch

import pandas as pd

from src.observation_builder import build_observation_sequence
from src.openai_provider import OpenAIResponsesProvider
from src.universal_llm_adapter import run_llm_agent


MODEL_OUTPUT = {
    "belief_status": "VALID",
    "confidence": 0.75,
    "explanation": "Observable evidence remains supportive.",
    "evidence_summary": {
        "supporting_evidence": ["Recent resolved prediction was supported."],
        "contradicting_evidence": [],
    },
}


class RecordingTransport:
    def __init__(self):
        self.payloads = []

    def __call__(self, payload, api_key, timeout):
        self.payloads.append(payload)
        return {"output_text": json.dumps(MODEL_OUTPUT)}


class OpenAIProviderTests(unittest.TestCase):
    def test_missing_credential_is_rejected(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY"):
                OpenAIResponsesProvider()

    def test_provider_builds_structured_responses_request(self):
        transport = RecordingTransport()
        provider = OpenAIResponsesProvider(
            api_key="test-key-not-real",
            transport=transport,
        )
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
        self.assertFalse(payload["store"])
        self.assertEqual(payload["temperature"], 0)
        self.assertEqual(payload["text"]["format"]["type"], "json_schema")
        self.assertTrue(payload["text"]["format"]["strict"])
        self.assertNotIn("timestamp", payload["text"]["format"]["schema"]["properties"])
        self.assertEqual(json.loads(payload["input"]), context)

    def test_four_step_provider_runtime_smoke(self):
        market = pd.read_csv("data/synthetic_market.csv")
        observations = build_observation_sequence(market)[20:24]
        transport = RecordingTransport()
        provider = OpenAIResponsesProvider(
            api_key="test-key-not-real",
            transport=transport,
        )

        beliefs = run_llm_agent(observations, provider)

        self.assertEqual(len(beliefs), 4)
        self.assertEqual(len(transport.payloads), 4)
        contexts = [json.loads(payload["input"]) for payload in transport.payloads]
        self.assertIsNone(contexts[0]["previous_belief_state"])
        self.assertEqual(contexts[1]["previous_belief_state"], beliefs[0])
        self.assertEqual(contexts[0]["recent_resolved_evidence"], [])
        self.assertEqual(len(contexts[1]["recent_resolved_evidence"]), 1)
        self.assertEqual(
            contexts[1]["recent_resolved_evidence"][0]["resolution_timestamp"],
            observations[1]["timestamp"],
        )
        self.assertTrue(
            all(
                belief["timestamp"] == observation["timestamp"]
                for belief, observation in zip(beliefs, observations)
            )
        )
        prompt_text = json.dumps(transport.payloads).lower()
        for forbidden_key in ("\"regime\"", "\"beta\"", "\"driver\""):
            self.assertNotIn(forbidden_key, prompt_text)
        self.assertNotIn('"future_return"', prompt_text)
        self.assertNotIn('"future_price"', prompt_text)


if __name__ == "__main__":
    unittest.main()
