"""Transparent LAI-to-gate translation; no assessment or permission policy."""

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Optional

from src.decision_gate import DecisionRequest, POLICY_ID, POLICY_VERSION
from src.lai_agent_schema import AgentBelief


@dataclass(frozen=True)
class ReliabilityObservation:
    """Reliability snapshot. None means unavailable, not favorable.

    Evidence and metadata are retained here for callers, not interpreted or
    inserted into gate fields that have different meanings. Direct construction
    supports incomplete observations; Decision Gate owns request validation.
    """

    belief_status: Optional[str] = None
    confidence: Optional[float] = None
    supporting_evidence: Optional[tuple[Any, ...]] = None
    contradicting_evidence: Optional[tuple[Any, ...]] = None
    evidence_conflict: Optional[bool] = None
    belief_persistence: Optional[int] = None
    timestamp: Optional[Any] = None
    provenance: Optional[Any] = None

    def __post_init__(self):
        # Detach nested evidence/metadata without narrowing the AgentBelief
        # evidence item schema or converting absent evidence into empty evidence.
        for name in ("supporting_evidence", "contradicting_evidence"):
            value = getattr(self, name)
            if value is not None:
                if not isinstance(value, (list, tuple)):
                    raise ValueError(f"{name} must be a list, tuple, or None")
                object.__setattr__(self, name, tuple(deepcopy(value)))
        for name in ("timestamp", "provenance"):
            object.__setattr__(self, name, deepcopy(getattr(self, name)))

    @classmethod
    def from_agent_belief(
        cls, belief: AgentBelief, *, evidence_conflict=None,
        belief_persistence=None, timestamp=None, provenance=None,
    ):
        """Copy an existing belief; additional observations must be explicit."""
        if not isinstance(belief, AgentBelief):
            raise TypeError("belief must be an AgentBelief")
        return cls(
            belief_status=belief.status, confidence=belief.confidence,
            supporting_evidence=belief.evidence_summary["supporting_evidence"],
            contradicting_evidence=belief.evidence_summary["contradicting_evidence"],
            evidence_conflict=evidence_conflict,
            belief_persistence=belief_persistence,
            timestamp=timestamp, provenance=provenance,
        )


def to_decision_request(
    observation: ReliabilityObservation, *, action_id: str, proposed_action: str,
    context_shift=None, data_quality=None, data_freshness=None,
    system_health=None, consequence_level=None, reversibility=None,
    policy_id=POLICY_ID, policy_version=POLICY_VERSION,
) -> DecisionRequest:
    """Copy reliability fields and explicit application context into a request.

    No permission is computed. Missing signals remain None and malformed signal
    values are left for the gate's validator to reject. Retain the observation
    alongside the request when evidence or provenance is needed for review.
    """
    if not isinstance(observation, ReliabilityObservation):
        raise TypeError("observation must be a ReliabilityObservation")
    return DecisionRequest(
        action_id=action_id, proposed_action=proposed_action,
        belief_status=observation.belief_status,
        confidence=observation.confidence,
        evidence_conflict=observation.evidence_conflict,
        belief_persistence=observation.belief_persistence,
        context_shift=context_shift, data_quality=data_quality,
        data_freshness=data_freshness, system_health=system_health,
        consequence_level=consequence_level, reversibility=reversibility,
        policy_id=policy_id, policy_version=policy_version,
    )
