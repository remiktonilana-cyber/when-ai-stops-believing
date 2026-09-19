"""End-to-end LAI pipeline validation using only the deterministic MockAgent.

This module is engineering validation infrastructure. It is not a scientific
experiment, does not run an LLM, and does not produce model-evaluation scores.
"""

import numpy as np

from src.lai_agent_trajectory import AgentTrajectory
from src.lai_belief_metrics import compute_belief_metrics
from src.lai_mock_agent import MockAgent
from src.lai_paired_evaluator import compare_paired_trajectories
from src.lai_transition_environment import generate_transition
from src.lai_transition_reference import D_PLUS, N, W


FORBIDDEN_AGENT_FIELDS = frozenset({
    "alpha", "latent_state", "latent_stress", "T_warning", "T_structural",
    "T_delta", "T_evidence", "future_response", "future_observations",
})


def build_agent_observation(world, index):
    """Adapt one environment row without exposing hidden or future fields."""
    row = world.iloc[index]
    observation = {
        "fragility": float(row["fragility"]),
        "crowding": float(row["crowding"]),
        "liquidity_stress": float(row["liquidity_stress"]),
        "context_signal": float(row["nuisance"]),
        "current_shock": float(row["shock"]),
    }
    if FORBIDDEN_AGENT_FIELDS.intersection(observation):
        raise AssertionError("adapter exposed a forbidden field")
    return observation


def _historical_summary(history):
    if not history:
        return {"resolved_count": 0, "lifetime_shock_response_slope": None,
                "lifetime_residual_rmse": None}
    shocks = np.asarray([pair[0] for pair in history], dtype=float)
    responses = np.asarray([pair[1] for pair in history], dtype=float)
    denominator = float(shocks @ shocks)
    slope = float((shocks @ responses) / denominator) if denominator else None
    rmse = None if slope is None else float(np.sqrt(np.mean((responses - slope * shocks) ** 2)))
    return {"resolved_count": len(history), "lifetime_shock_response_slope": slope,
            "lifetime_residual_rmse": rmse}


def _run_agent(world):
    agent = MockAgent()
    trajectory = AgentTrajectory()
    resolved_history = []
    for index in range(N):
        observation = build_agent_observation(world, index)
        belief = agent.respond(
            observation,
            resolved_history[-W:],
            _historical_summary(resolved_history),
        )
        trajectory.append(index, observation, belief)
        # Row index i's response resolves when the next observation is available.
        resolved_history.append((float(world.iloc[index]["shock"]), float(world.iloc[index]["next_response"])))
    return trajectory


def run_mock_pipeline(seed=1000, d_plus=D_PLUS):
    """Run both matched worlds and return descriptive pipeline artifacts only."""
    transition_world = generate_transition(seed, d_plus)
    control_world = generate_transition(seed, d_plus, control=True)
    transition_trajectory = _run_agent(transition_world)
    control_trajectory = _run_agent(control_world)
    return {
        "transition_trajectory": transition_trajectory,
        "control_trajectory": control_trajectory,
        "transition_metrics": compute_belief_metrics(transition_trajectory.steps()),
        "control_metrics": compute_belief_metrics(control_trajectory.steps()),
        "paired_summary": compare_paired_trajectories(
            transition_trajectory.steps(), control_trajectory.steps()),
    }
