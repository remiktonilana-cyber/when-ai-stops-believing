"""Offline tests for the Qwen provider wrapper."""

import json
import os
import unittest
from unittest.mock import patch

import pandas as pd

from src.observation_builder import build_observation_sequence
from src.qwen_provider import DEFAULT_MODEL, QwenProvider
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


class QwenProviderTests(unittest.TestCase):
    def test_http_endpoint_selection(self):
        mainland = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        international = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        cases = (
            ({}, mainland),
            ({"DASHSCOPE_BASE_URL": ""}, mainland),
            ({"DASHSCOPE_BASE_URL": mainland}, mainland),
            ({"DASHSCOPE_BASE_URL": international}, international),
            ({"DASHSCOPE_BASE_URL": international + "/"}, international),
        )
        for environment, expected_base in cases:
            with self.subTest(environment=environment):
                with patch.dict(os.environ, environment, clear=True):
                    with patch("src.qwen_provider.urlopen") as mock_urlopen:
                        response = mock_urlopen.return_value.__enter__.return_value
                        response.read.return_value = json.dumps({
                            "model": DEFAULT_MODEL,
                            "choices": [{"message": {
                                "content": json.dumps(MODEL_OUTPUT),
                            }}],
                        }).encode("utf-8")
                        provider = QwenProvider(api_key="test-key-not-real")

                        self.assertEqual(provider({}), MODEL_OUTPUT)

                        mock_urlopen.assert_called_once()
                        request = mock_urlopen.call_args.args[0]
                        self.assertEqual(
                            request.full_url, expected_base + "/chat/completions"
                        )
                        self.assertEqual(request.get_method(), "POST")
                        self.assertEqual(
                            request.get_header("Authorization"),
                            "Bearer test-key-not-real",
                        )

    def test_missing_credential_is_rejected(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "DASHSCOPE_API_KEY"):
                QwenProvider()

    def test_provider_builds_json_chat_request(self):
        transport = RecordingTransport()
        provider = QwenProvider(api_key="test-key-not-real", transport=transport)
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
        self.assertFalse(payload["enable_thinking"])
        self.assertFalse(payload["stream"])
        self.assertEqual(json.loads(payload["messages"][1]["content"]), context)
        self.assertIn("JSON", payload["messages"][0]["content"])
        self.assertEqual(provider.last_response_model, DEFAULT_MODEL)

    def test_invalid_json_is_rejected(self):
        provider = QwenProvider(
            api_key="test-key-not-real",
            transport=RecordingTransport("not-json"),
        )
        with self.assertRaisesRegex(ValueError, "not valid JSON"):
            provider({})

    def test_four_step_runtime_is_causal(self):
        market = pd.read_csv("data/synthetic_market.csv")
        observations = build_observation_sequence(market)[20:24]
        transport = RecordingTransport()
        provider = QwenProvider(
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
