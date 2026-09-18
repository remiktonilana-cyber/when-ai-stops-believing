"""Causal storage for future LAI Agent belief trajectories.

This module records only an Agent-visible observation and an :class:`AgentBelief`
at each timestamp. It does not generate observations, run providers, or score
beliefs.
"""

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping

from src.lai_agent_schema import AgentBelief


FORBIDDEN_FIELDS = frozenset(
    {
        "alpha",
        "latent_state",
        "latent_stress",
        "T_warning",
        "T_structural",
        "T_delta",
        "T_evidence",
        "future_response",
        "future_observations",
    }
)


def _reject_forbidden_fields(value):
    """Reject hidden or future fields anywhere in stored mapping data."""
    if isinstance(value, Mapping):
        forbidden = FORBIDDEN_FIELDS.intersection(value)
        if forbidden:
            names = ", ".join(sorted(forbidden))
            raise ValueError(f"Agent trajectory contains forbidden field(s): {names}")
        for nested in value.values():
            _reject_forbidden_fields(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _reject_forbidden_fields(nested)


@dataclass(frozen=True)
class TrajectoryStep:
    """One timestamped, Agent-visible observation and validated belief."""

    timestamp: Any
    observation: Mapping[str, Any]
    belief: AgentBelief


class AgentTrajectory:
    """Append-only chronological storage for Agent belief steps."""

    def __init__(self):
        self._steps = []

    def append(self, timestamp, observation, belief):
        """Validate and append one step, returning the stored step."""
        if timestamp is None:
            raise ValueError("timestamp is required")
        if not isinstance(observation, Mapping):
            raise ValueError("observation is required and must be a mapping")
        if not isinstance(belief, AgentBelief):
            raise ValueError("belief is required and must be an AgentBelief")
        _reject_forbidden_fields(observation)
        _reject_forbidden_fields(belief.evidence_summary)

        if self._steps:
            previous = self._steps[-1].timestamp
            try:
                if timestamp < previous:
                    raise ValueError("trajectory timestamps must be chronological")
            except TypeError as error:
                raise ValueError("timestamps must be mutually orderable") from error

        step = TrajectoryStep(
            timestamp=deepcopy(timestamp),
            observation=deepcopy(observation),
            belief=deepcopy(belief),
        )
        self._steps.append(step)
        return deepcopy(step)

    def __len__(self):
        return len(self._steps)

    @property
    def length(self):
        """Number of recorded steps."""
        return len(self)

    def steps(self):
        """Return a detached list of stored steps in chronological order."""
        return deepcopy(self._steps)

