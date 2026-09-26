"""Synchronous gate enforcement over independent synthetic state."""

from dataclasses import asdict

from applications.urban_traffic.adapter import build_request
from applications.urban_traffic.environment import apply_action, validate_action
from src import decision_gate


def run_scenario(scenario):
    before = asdict(scenario.state)
    validate_action(scenario.state, scenario.proposal)
    observation, request = build_request(scenario)
    decision = decision_gate.evaluate(request)
    if (decision.action_id != request.action_id
            or decision.proposed_action != request.proposed_action):
        raise ValueError("Gate decision does not match the pending action")
    if decision.permission == "GREEN":
        execution = apply_action(scenario.state, scenario.proposal)
    elif decision.permission == "YELLOW":
        execution = "HELD"
    elif decision.permission == "RED":
        execution = "BLOCKED"
    else:
        raise ValueError("Unrecognized gate permission")
    return {
        "scenario": scenario.name, "situation": scenario.situation,
        "proposal_source": "scripted", "proposal": asdict(scenario.proposal),
        "observation": asdict(observation), "request": asdict(request),
        "decision": asdict(decision), "execution_result": execution,
        "before": before, "after": asdict(scenario.state),
    }
