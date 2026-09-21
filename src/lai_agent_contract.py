"""Causal input builders and neutral prompt text for a future real Agent.

These helpers are provider-independent. They construct only current
Agent-visible information and never invoke a model.
"""

from copy import deepcopy
import json

import numpy as np

from src.lai_agent_schema import AgentBelief


MAX_RESOLVED_HISTORY = 50
OBSERVATION_FIELDS = (
    "fragility", "crowding", "liquidity_stress", "context_signal", "current_shock",
)
FORBIDDEN_FIELDS = frozenset({
    "latent_stress", "latent_state", "alpha", "phase", "regime",
    "T_warning", "T_structural", "T_delta", "T_evidence", "evidence_detector",
    "future_response", "future_observations", "response", "next_response",
})


def _causal_pairs(world, exclusive_end):
    """Return resolved rows i < exclusive_end, oldest first."""
    return [
        (float(world.iloc[index]["shock"]), float(world.iloc[index]["next_response"]))
        for index in range(exclusive_end)
    ]


def _summary(pairs):
    if not pairs:
        return {"resolved_count": 0, "lifetime_shock_response_slope": None,
                "lifetime_residual_rmse": None}
    shocks = np.asarray([pair[0] for pair in pairs], dtype=float)
    responses = np.asarray([pair[1] for pair in pairs], dtype=float)
    denominator = float(shocks @ shocks)
    if denominator == 0:
        slope = rmse = None
    else:
        slope = float((shocks @ responses) / denominator)
        rmse = float(np.sqrt(np.mean((responses - slope * shocks) ** 2)))
    return {"resolved_count": len(pairs), "lifetime_shock_response_slope": slope,
            "lifetime_residual_rmse": rmse}


def _validate_visible_input(value):
    if FORBIDDEN_FIELDS.intersection(value):
        raise AssertionError("causal input contains forbidden information")


def _belief_input(previous_belief):
    if previous_belief is None:
        return None
    if not isinstance(previous_belief, AgentBelief):
        raise TypeError("previous_belief must be an AgentBelief or None")
    result = {
        "belief_status": previous_belief.status.value,
        "confidence": previous_belief.confidence,
        "evidence_summary": deepcopy(previous_belief.evidence_summary),
    }
    _validate_visible_input(result)
    return result


def build_runtime_input(world, timestep, previous_belief=None):
    """Build I_t using row t and only responses from rows i<t."""
    if not isinstance(timestep, int) or isinstance(timestep, bool) or not 0 <= timestep < len(world):
        raise ValueError("timestep must be a valid row index")
    row = world.iloc[timestep]
    observation = {
        "fragility": float(row["fragility"]),
        "crowding": float(row["crowding"]),
        "liquidity_stress": float(row["liquidity_stress"]),
        "context_signal": float(row["nuisance"]),
        "current_shock": float(row["shock"]),
    }
    resolved = _causal_pairs(world, timestep)
    result = {
        "current_observation": observation,
        "previous_belief": _belief_input(previous_belief),
        "resolved_history": resolved[-MAX_RESOLVED_HISTORY:],
        "historical_summary": _summary(resolved),
    }
    _validate_visible_input(observation)
    return result


def build_initialization_input(world, initialization_timestep=349):
    """Build initialization input from resolved rows 0..348 (before day 349)."""
    if initialization_timestep < 0 or initialization_timestep > len(world):
        raise ValueError("initialization_timestep is outside the world")
    resolved = _causal_pairs(world, initialization_timestep)
    return {"resolved_history": resolved[-MAX_RESOLVED_HISTORY:],
            "historical_summary": _summary(resolved)}


def build_neutral_prompt(agent_input):
    """Return provider-independent epistemic instructions plus serialized input."""
    prompt = """You are evaluating one previously established relationship.

The previously established shock-response relationship remains a reliable description of how this system currently responds to external shocks.

Maintain an explicit belief about whether that relationship remains reliable. Use only the supplied current observation, previous belief, resolved history, and historical summary. Consider new evidence according to its relevance and strength. New evidence may support, weaken, or leave the existing belief unchanged. Do not assume that the relationship must change.

VALID: Available evidence does not currently justify abandoning the established relationship as the working belief.
UNCERTAIN: Available evidence materially challenges the established relationship, but does not yet justify treating it as invalid.
INVALID: Available evidence is sufficient to conclude that the established relationship should no longer be treated as a reliable description of the current system.

Confidence is a number from 0 to 1 representing confidence that the selected belief_status is appropriate. It is not the probability that the old relationship is valid.

Return exactly this JSON shape. Keep explanation brief and at most three sentences. Each evidence list may contain at most three items.
{"belief_status":"VALID | UNCERTAIN | INVALID","confidence":0.0,"explanation":"","evidence_summary":{"supporting_evidence":[],"contradicting_evidence":[]}}

Supplied information:
"""
    return prompt + json.dumps(agent_input, default=list, sort_keys=True)

