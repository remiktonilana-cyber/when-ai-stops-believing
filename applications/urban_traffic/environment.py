"""Minimal configuration simulator; no traffic optimization or movement model."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Intersection:
    intersection_id: str = "synthetic-1"
    step: int = 3
    observation_step: int | None = 3
    ns_queue: int | None = 12
    ew_queue: int | None = 5
    ns_green: int = 30
    ew_green: int = 30
    controller_health: str | None = "HEALTHY"
    context_shift: bool | None = False
    executed_actions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Proposal:
    action_id: str
    intersection_id: str = "synthetic-1"
    cycle: int = 4
    phase: str = "NS"
    from_seconds: int = 30
    to_seconds: int = 35

    @property
    def description(self):
        return (f"At {self.intersection_id}, change {self.phase} green from "
                f"{self.from_seconds} to {self.to_seconds} synthetic seconds "
                f"for cycle {self.cycle}.")


def validate_action(state: Intersection, proposal: Proposal):
    """Restrict execution to the one documented action and current cycle."""
    if (not isinstance(proposal.action_id, str) or not proposal.action_id.strip()
            or proposal.intersection_id != state.intersection_id
            or proposal.phase != "NS"
            or type(proposal.cycle) is not int or proposal.cycle != state.step + 1
            or type(proposal.from_seconds) is not int or proposal.from_seconds != 30
            or type(proposal.to_seconds) is not int or proposal.to_seconds != 35):
        raise ValueError("Action is outside the demo's allowed action space")


def apply_action(state: Intersection, proposal: Proposal):
    """Apply an already gated action once; called only by the simulator."""
    validate_action(state, proposal)
    if proposal.action_id in state.executed_actions:
        return "ALREADY_EXECUTED"
    if state.ns_green != proposal.from_seconds:
        raise ValueError("Timing configuration no longer matches the proposal")
    state.ns_green = proposal.to_seconds
    state.executed_actions.append(proposal.action_id)
    return "EXECUTED"
