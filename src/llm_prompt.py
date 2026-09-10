"""Provider-independent prompt contract for the v0.2 LLM track."""

import json


SYSTEM_INSTRUCTIONS = """You are maintaining a belief about whether an observable
market signal remains useful for predicting the direction of the next-period
return. Reason only from the supplied observable evidence.

Use belief_status VALID when the evidence still supports the signal's
usefulness, UNCERTAIN when the evidence is insufficient or conflicted, and
INVALID when the evidence supports abandoning the belief. The structural
ground truth is unknown to you. Return only the structured fields required by
the response schema."""


def serialize_runtime_context(context):
    """Serialize an assembled benchmark context deterministically."""
    return json.dumps(
        context,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
