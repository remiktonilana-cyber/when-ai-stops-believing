"""Minimal Qwen Chat Completions provider for the LLM runtime."""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.llm_prompt import SYSTEM_INSTRUCTIONS, serialize_runtime_context


DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen-plus"
CONCISE_OUTPUT_INSTRUCTIONS = (
    "Keep explanation to at most two short sentences. In each evidence_summary "
    "list, return at most three short summary strings, aggregating patterns or "
    "counts where useful. Do not copy full evidence records or repeat the "
    "evidence history. Consider all supplied evidence when deciding the belief; "
    "these limits apply only to output verbosity. Finish the complete JSON object."
)


class QwenTruncatedOutputError(ValueError):
    """The model exhausted its output budget; no belief can be accepted."""

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
    """POST one Qwen request without exposing credential material."""
    # Set DASHSCOPE_BASE_URL to https://dashscope-intl.aliyuncs.com/compatible-mode/v1
    # for international credentials. The base URL excludes /chat/completions.
    base_url = os.environ.get("DASHSCOPE_BASE_URL") or DEFAULT_BASE_URL
    request = Request(
        f"{base_url.rstrip('/')}/chat/completions",
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
            f"Qwen API request failed with HTTP {error.code}"
        ) from error
    except URLError as error:
        raise RuntimeError(
            "Qwen API request could not reach the service"
        ) from error


def _extract_message_content(response):
    """Extract the assistant JSON string from a chat completion."""
    if not isinstance(response, dict):
        raise ValueError("Qwen response must be a dictionary")
    choices = response.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("Qwen response must contain exactly one choice")
    if choices[0].get("finish_reason") == "length":
        raise QwenTruncatedOutputError(
            "Qwen output was truncated (finish_reason=length)"
        )
    message = choices[0].get("message")
    if not isinstance(message, dict) or not isinstance(message.get("content"), str):
        raise ValueError("Qwen response did not contain message content")
    return message["content"]


class QwenProvider:
    """Map an assembled benchmark context to model-owned belief fields."""

    def __init__(
        self,
        api_key=None,
        model=DEFAULT_MODEL,
        timeout=60,
        transport=None,
        prompt_builder=None,
    ):
        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise RuntimeError("DASHSCOPE_API_KEY is required for Qwen requests")
        self.model = model
        self.timeout = timeout
        self.transport = transport or _http_transport
        self.prompt_builder = prompt_builder
        self.last_response_model = None

    def __call__(self, context):
        system_prompt = (
            self.prompt_builder(context)
            if self.prompt_builder is not None
            else (
                f"{SYSTEM_INSTRUCTIONS}\n\n"
                "Return a JSON object matching this exact shape and do not add fields:\n"
                f"{json.dumps(OUTPUT_EXAMPLE, separators=(',', ':'))}\n\n"
                f"{CONCISE_OUTPUT_INSTRUCTIONS}"
            )
        )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": serialize_runtime_context(context)},
            ],
            "enable_thinking": False,
            "temperature": 0,
            "max_tokens": 1000,
            "response_format": {"type": "json_object"},
            "stream": False,
        }
        for attempt in range(2):
            response = self.transport(payload, self.api_key, self.timeout)
            if isinstance(response, dict) and isinstance(response.get("model"), str):
                self.last_response_model = response["model"]
            try:
                model_output = json.loads(_extract_message_content(response))
            except QwenTruncatedOutputError as error:
                if attempt == 1:
                    raise QwenTruncatedOutputError(
                        "Qwen output remained truncated after one retry "
                        "(max_tokens=2000); no belief accepted"
                    ) from error
                # Regenerate from the identical causal context, never from partial JSON.
                payload = {**payload, "max_tokens": 2000}
                continue
            except json.JSONDecodeError as error:
                raise ValueError("Qwen structured output was not valid JSON") from error
            if not isinstance(model_output, dict):
                raise ValueError("Qwen structured output must be an object")
            return model_output
