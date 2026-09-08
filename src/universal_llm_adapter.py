"""Provider-independent runtime adapter for the v0.2 LLM benchmark track."""

from copy import deepcopy
from numbers import Real

import pandas as pd

from src.baseline_belief_agent import extract_prediction
from src.belief_interface import create_belief_state, validate_belief_status
from src.observation_builder import (
    OBSERVATION_COLUMNS,
    validate_observation_boundary,
)


RECENT_EVIDENCE_LIMIT = 50
MODEL_OUTPUT_FIELDS = {
    "belief_status",
    "confidence",
    "explanation",
    "evidence_summary",
}
EVIDENCE_SUMMARY_FIELDS = {
    "supporting_evidence",
    "contradicting_evidence",
}


def _prepare_current_observation(observation):
    """Copy and validate the static, causally available observation at time t."""
    validate_observation_boundary(observation)
    current_observation = deepcopy(observation)
    current_observation.pop("previous_belief_state", None)

    if set(current_observation) != {"timestamp", "market_history", "current_features"}:
        raise ValueError("Unexpected current observation fields")
    if current_observation["market_history"] != []:
        raise ValueError("Raw market history must not enter the LLM context")
    if set(current_observation["current_features"]) != set(OBSERVATION_COLUMNS):
        raise ValueError("Unexpected current feature fields")

    return current_observation


def _historical_evidence_summary(resolved_evidence):
    """Build deterministic aggregate statistics without exposing raw history."""
    resolved_count = len(resolved_evidence)
    supporting_count = sum(item["supported"] for item in resolved_evidence)
    contradicting_count = resolved_count - supporting_count
    success_rate = (
        supporting_count / resolved_count if resolved_count else None
    )
    return {
        "resolved_count": resolved_count,
        "supporting_count": supporting_count,
        "contradicting_count": contradicting_count,
        "success_rate": success_rate,
    }


def assemble_runtime_context(
    observation,
    previous_belief_state,
    resolved_evidence,
):
    """Assemble the frozen four-part information set for timestep t."""
    return {
        "current_observation": _prepare_current_observation(observation),
        "previous_belief_state": deepcopy(previous_belief_state),
        "recent_resolved_evidence": deepcopy(
            resolved_evidence[-RECENT_EVIDENCE_LIMIT:]
        ),
        "historical_evidence_summary": _historical_evidence_summary(
            resolved_evidence
        ),
    }


def validate_model_output(model_output):
    """Validate the provider-owned portion of a belief response."""
    if not isinstance(model_output, dict):
        raise ValueError("Model output must be a dictionary")
    if set(model_output) != MODEL_OUTPUT_FIELDS:
        raise ValueError("Model output fields do not match the required contract")

    validate_belief_status(model_output["belief_status"])

    confidence = model_output["confidence"]
    if isinstance(confidence, bool) or not isinstance(confidence, Real):
        raise ValueError("confidence must be numeric")
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be between 0 and 1")
    if not isinstance(model_output["explanation"], str):
        raise ValueError("explanation must be a string")

    evidence_summary = model_output["evidence_summary"]
    if not isinstance(evidence_summary, dict):
        raise ValueError("evidence_summary must be a dictionary")
    if set(evidence_summary) != EVIDENCE_SUMMARY_FIELDS:
        raise ValueError("Malformed evidence_summary fields")
    if not isinstance(evidence_summary["supporting_evidence"], list):
        raise ValueError("supporting_evidence must be a list")
    if not isinstance(evidence_summary["contradicting_evidence"], list):
        raise ValueError("contradicting_evidence must be a list")

    return True


def _resolve_previous_prediction(previous_prediction, observation):
    """Resolve prediction t-1 using Return_t revealed in observation t."""
    if previous_prediction is None:
        return None

    historical_return = observation["current_features"]["historical_return"]
    if historical_return is None or pd.isna(historical_return):
        return None

    outcome = "positive" if historical_return > 0 else "negative"
    return {
        "prediction_timestamp": previous_prediction["timestamp"],
        "resolution_timestamp": observation["timestamp"],
        "prediction": previous_prediction["prediction"],
        "outcome": outcome,
        "supported": previous_prediction["prediction"] == outcome,
    }


def run_llm_agent(observations, model_callable):
    """Run a provider callback over a causal observation sequence."""
    if not callable(model_callable):
        raise TypeError("model_callable must be callable")

    belief_history = []
    resolved_evidence = []
    previous_belief_state = None
    previous_prediction = None

    for observation in observations:
        current_observation = _prepare_current_observation(observation)
        resolved = _resolve_previous_prediction(
            previous_prediction,
            current_observation,
        )
        if resolved is not None:
            resolved_evidence.append(resolved)

        context = assemble_runtime_context(
            current_observation,
            previous_belief_state,
            resolved_evidence,
        )
        model_output = model_callable(deepcopy(context))
        validate_model_output(model_output)

        belief_state = create_belief_state(
            timestamp=current_observation["timestamp"],
            belief_status=model_output["belief_status"],
            confidence=model_output["confidence"],
            explanation=model_output["explanation"],
            evidence_summary=deepcopy(model_output["evidence_summary"]),
        )
        belief_history.append(belief_state)
        previous_belief_state = belief_state

        prediction = extract_prediction(current_observation)
        previous_prediction = (
            None
            if prediction is None
            else {
                "timestamp": current_observation["timestamp"],
                "prediction": prediction,
            }
        )

    return belief_history
