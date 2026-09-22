"""Minimal DeepSeek Chat Completions provider for the LLM runtime."""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.llm_prompt import SYSTEM_INSTRUCTIONS, serialize_runtime_context


DEEPSEEK_CHAT_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-v4-flash"

OUTPUT_EXAMPLE = {
    "belief_status": "VALID",
    "confidence": 0.8,
    "explanation": "Observable evidence supports the signal's usefulness.",
    "evidence_summary": {
        "supporting_evidence": [],
        "contradicting_evidence": [],
    },
}


def _http_transport(payload, api_key, timeout):
    """POST one DeepSeek request without exposing credential material."""
    request = Request(
        DEEPSEEK_CHAT_URL,
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
        raise RuntimeError(
            f"DeepSeek API request failed with HTTP {error.code}"
        ) from error
    except URLError as error:
        raise RuntimeError(
            "DeepSeek API request could not reach the service"
        ) from error


def _extract_message_content(response):
    """Extract the assistant JSON string from a chat completion."""
    if not isinstance(response, dict):
        raise ValueError("DeepSeek response must be a dictionary")
    choices = response.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("DeepSeek response must contain exactly one choice")
    message = choices[0].get("message")
    if not isinstance(message, dict) or not isinstance(message.get("content"), str):
        raise ValueError("DeepSeek response did not contain message content")
    return message["content"]


class DeepSeekProvider:
    """Map an assembled benchmark context to model-owned belief fields."""

    def __init__(
        self,
        api_key=None,
        model=DEFAULT_MODEL,
        timeout=60,
        transport=None,
        prompt_builder=None,
    ):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is required for DeepSeek requests")
        self.model = model
        self.timeout = timeout
        self.transport = transport or _http_transport
        self.prompt_builder = prompt_builder
        self.last_response_model = None

    def __call__(self, context):
        # Request metadata is scoped to this invocation.  In particular, a
        # transport failure must not leave the previous response model attached
        # to the failed request's provenance.
        self.last_response_model = None
        system_prompt = (
            self.prompt_builder(context)
            if self.prompt_builder is not None
            else (
                f"{SYSTEM_INSTRUCTIONS}\n\n"
                "Return a JSON object matching this exact shape and do not add fields:\n"
                f"{json.dumps(OUTPUT_EXAMPLE, separators=(',', ':'))}"
            )
        )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": serialize_runtime_context(context)},
            ],
            "thinking": {"type": "disabled"},
            "temperature": 0,
            "max_tokens": 1000,
            "response_format": {"type": "json_object"},
            "stream": False,
        }
        response = self.transport(payload, self.api_key, self.timeout)
        if isinstance(response, dict) and isinstance(response.get("model"), str):
            self.last_response_model = response["model"]
        try:
            model_output = json.loads(_extract_message_content(response))
        except json.JSONDecodeError as error:
            raise ValueError("DeepSeek structured output was not valid JSON") from error
        if not isinstance(model_output, dict):
            raise ValueError("DeepSeek structured output must be an object")
        return model_output
