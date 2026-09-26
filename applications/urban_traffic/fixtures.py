"""Exactly three scripted scenarios; these are not live AI observations."""

from __future__ import annotations

from dataclasses import dataclass

from applications.urban_traffic.environment import Intersection, Proposal
from src.lai_agent_schema import AgentBelief


@dataclass
class Scenario:
    name: str
    situation: str
    state: Intersection
    proposal: Proposal
    belief: AgentBelief
    evidence_conflict: bool | None = False
    belief_persistence: int | None = 3


def scenarios():
    """Construct fresh, independent state and belief objects on every call."""
    definitions = (
        ("A Normal", "Normal synthetic arrival pattern.", {}),
        ("B Environment shift", "Scripted EW arrival-pattern change; belief unchanged.",
         {"ew_queue": 20, "context_shift": True}),
        ("C Operational failure", "Simulated controller unavailable.",
         {"controller_health": "UNHEALTHY"}),
    )
    return [Scenario(
        name, situation, Intersection(**changes), Proposal(f"traffic-{name[0]}"),
        AgentBelief("VALID", 0.8, "Scripted belief supporting the proposed timing change.",
                    {"supporting_evidence": ["Scripted prior observations"],
                     "contradicting_evidence": []}),
    ) for name, situation, changes in definitions]
