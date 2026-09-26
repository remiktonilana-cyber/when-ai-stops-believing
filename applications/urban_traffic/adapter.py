"""Translate traffic context, without deciding permission."""

from src.reliability_adapter import ReliabilityObservation, to_decision_request


def build_request(scenario):
    state = scenario.state
    observation = ReliabilityObservation.from_agent_belief(
        scenario.belief, evidence_conflict=scenario.evidence_conflict,
        belief_persistence=scenario.belief_persistence,
        timestamp=state.observation_step,
        provenance={"source": "scripted fixture", "scenario": scenario.name},
    )
    queues = (state.ns_queue, state.ew_queue)
    quality = (None if any(value is None for value in queues) else
               "GOOD" if all(type(value) is int and value >= 0 for value in queues)
               else "UNUSABLE")
    if state.observation_step is None:
        freshness = None
    elif (type(state.observation_step) is not int or type(state.step) is not int
          or state.observation_step < 0 or state.observation_step > state.step):
        quality, freshness = "UNUSABLE", None
    else:
        freshness = "FRESH" if state.observation_step == state.step else "STALE"
    request = to_decision_request(
        observation, action_id=scenario.proposal.action_id,
        proposed_action=scenario.proposal.description,
        context_shift=state.context_shift, data_quality=quality,
        data_freshness=freshness, system_health=state.controller_health,
        consequence_level="LOW", reversibility="HIGH",
    )
    return observation, request
