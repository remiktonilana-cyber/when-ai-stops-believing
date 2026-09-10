"""Minimal OpenAI Responses API wrapper for the universal LLM runtime."""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.llm_prompt import SYSTEM_INSTRUCTIONS, serialize_runtime_context


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-4.1-mini"

BELIEF_OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "belief_status",
        "confidence",
        "explanation",
        "evidence_summary",
    ],
    "properties": {
        "belief_status": {
            "type": "string",
            "enum": ["VALID", "UNCERTAIN", "INVALID"],
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "explanation": {"type": "string"},
        "evidence_summary": {
            "type": "object",
            "additionalProperties": False,
            "required": ["supporting_evidence", "contradicting_evidence"],
            "properties": {
                "supporting_evidence": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "contradicting_evidence": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        },
    },
}


def _http_transport(payload, api_key, timeout):
    """POST one response request without exposing credential material."""
    request = Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise RuntimeError(f"OpenAI API request failed with HTTP {error.code}") from error
    except URLError as error:
        raise RuntimeError("OpenAI API request could not reach the service") from error


def _extract_output_text(response):
    """Extract structured text from a completed Responses API response."""
    if not isinstance(response, dict):
        raise ValueError("OpenAI response must be a dictionary")
    if isinstance(response.get("output_text"), str):
        return response["output_text"]

    for item in response.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text" and isinstance(
                content.get("text"), str
            ):
                return content["text"]
    raise ValueError("OpenAI response did not contain structured output text")


class OpenAIResponsesProvider:
    """Callable provider that maps an assembled context to model-owned fields."""

    def __init__(
        self,
        api_key=None,
        model=DEFAULT_MODEL,
        timeout=60,
        transport=None,
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required for OpenAI requests")
        self.model = model
        self.timeout = timeout
        self.transport = transport or _http_transport

    def __call__(self, context):
        payload = {
            "model": self.model,
            "instructions": SYSTEM_INSTRUCTIONS,
            "input": serialize_runtime_context(context),
            "temperature": 0,
            "store": False,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "belief_state",
                    "strict": True,
                    "schema": BELIEF_OUTPUT_SCHEMA,
                }
            },
        }
        response = self.transport(payload, self.api_key, self.timeout)
        try:
            return json.loads(_extract_output_text(response))
        except json.JSONDecodeError as error:
            raise ValueError("OpenAI structured output was not valid JSON") from error
