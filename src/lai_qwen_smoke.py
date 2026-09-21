"""Three-call Qwen smoke runtime for the frozen LAI Agent contract.

This is runtime validation only. It does not run a trajectory, compute
scientific metrics, compare worlds, or interpret model behavior.
"""

from copy import deepcopy
import json
from pathlib import Path

from src.lai_agent_contract import build_initialization_input, build_neutral_prompt, build_runtime_input
from src.lai_agent_schema import AgentBelief, BeliefStatus
from src.lai_transition_environment import generate_transition
from src.lai_transition_reference import D_PLUS
from src.qwen_provider import QwenProvider
from src.universal_llm_adapter import validate_model_output


def _as_belief(model_output):
    validate_model_output(model_output)
    return AgentBelief(
        model_output["belief_status"],
        model_output["confidence"],
        model_output["explanation"],
        deepcopy(model_output["evidence_summary"]),
    )


def _safe_belief(belief):
    return {"status": belief.status.value, "confidence": belief.confidence,
            "supporting_count": len(belief.evidence_summary["supporting_evidence"]),
            "contradicting_count": len(belief.evidence_summary["contradicting_evidence"])}


def _input_audit(agent_input, expected_previous=None):
    current = agent_input.get("current_observation", {})
    forbidden = {
        "alpha", "latent_state", "latent_stress", "T_warning", "T_structural",
        "T_delta", "T_evidence", "future_response", "future_observations", "next_response",
    }
    if forbidden.intersection(current):
        raise AssertionError("forbidden field reached provider input")
    if len(agent_input["resolved_history"]) > 50:
        raise AssertionError("resolved history exceeded 50 pairs")
    if expected_previous and "explanation" in agent_input.get("previous_belief", {}):
        raise AssertionError("previous explanation reached provider input")


def run_qwen_smoke(*, seed=42, artifact_path=None, provider=None):
    """Execute initialization, Day 350, and Day 351, then stop.

    A supplied provider is useful for offline tests. Real execution constructs
    the existing QwenProvider with the frozen neutral prompt builder.
    """
    world = generate_transition(seed, D_PLUS)
    transport_calls = []
    if provider is None:
        # The existing provider's module transport is the configured DashScope
        # mainland transport; avoid copying credentials or endpoint logic here.
        from src.qwen_provider import _http_transport
        transport = lambda payload, api_key, timeout: (
            transport_calls.append({"max_tokens": payload.get("max_tokens")}) or
            _http_transport(payload, api_key, timeout)
        )
        provider = QwenProvider(prompt_builder=build_neutral_prompt, transport=transport)

    calls = []

    def invoke(stage, agent_input):
        _input_audit(agent_input, expected_previous=stage != "initialization")
        output = provider(agent_input)
        belief = _as_belief(output)
        calls.append({"stage": stage, "belief": belief, "history_count": len(agent_input["resolved_history"])})
        return belief, agent_input

    try:
        initialization_input = build_initialization_input(world)
        initialization_belief, _ = invoke("initialization", initialization_input)
        if initialization_belief.status is not BeliefStatus.VALID:
            result = {
                "provider": "qwen", "model": getattr(provider, "model", None),
                "status": "INITIAL BELIEF NOT ESTABLISHED", "real_provider_calls": len(transport_calls) or len(calls),
                "initialization": _safe_belief(initialization_belief), "calls": calls,
            }
        else:
            previous = deepcopy(initialization_belief)
            day350_input = build_runtime_input(world, 350, previous)
            day350_belief, _ = invoke("day350", day350_input)
            previous = deepcopy(day350_belief)
            day351_input = build_runtime_input(world, 351, previous)
            if len(day351_input["resolved_history"]) == 0 or day351_input["resolved_history"][-1] != (
                float(world.iloc[350]["shock"]), float(world.iloc[350]["next_response"])
            ):
                raise AssertionError("Day 350 resolved pair was not available at Day 351")
            if "next_response" in day351_input["current_observation"]:
                raise AssertionError("Day 351 unresolved response was exposed")
            day351_belief, _ = invoke("day351", day351_input)
            result = {
                "provider": "qwen", "model": getattr(provider, "model", None), "status": "PASS",
                "real_provider_calls": len(transport_calls) or len(calls),
                "initialization": _safe_belief(initialization_belief),
                "day350": _safe_belief(day350_belief), "day351": _safe_belief(day351_belief),
                "history_counts": {"initialization": len(initialization_input["resolved_history"]),
                                   "day350": len(day350_input["resolved_history"]),
                                   "day351": len(day351_input["resolved_history"])},
                "day351_gained_day350_pair": True,
                "day351_current_response_absent": True,
                "previous_explanation_propagated": False,
            }
            result["retry_count"] = max(0, result["real_provider_calls"] - len(calls))
            result["retry_reasons"] = (
                ["provider-internal truncation retry"] * result["retry_count"]
            )
        if artifact_path is not None:
            path = Path(artifact_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result
    except Exception as error:
        result = {"provider": "qwen", "model": getattr(provider, "model", None),
                  "status": "FAIL", "failure_type": type(error).__name__,
                  "failure_message": str(error), "real_provider_calls": len(transport_calls),
                  "stages_completed": [call["stage"] for call in calls]}
        if artifact_path is not None:
            path = Path(artifact_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result
