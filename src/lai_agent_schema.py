"""Minimal LAI Agent belief schema.

This module validates provider-independent belief data only. It does not run an
agent, assemble a trajectory, or expose hidden environment state.
"""

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from numbers import Real
from typing import Any, Mapping


MAX_EVIDENCE_ITEMS = 3


class BeliefStatus(str, Enum):
    """The three allowed qualitative belief states."""

    VALID = "VALID"
    UNCERTAIN = "UNCERTAIN"
    INVALID = "INVALID"


@dataclass
class AgentBelief:
    """A minimal belief produced after processing one causal observation."""

    status: BeliefStatus
    confidence: float
    explanation: str
    evidence_summary: Mapping[str, Any]

    def __post_init__(self):
        try:
            self.status = (
                self.status
                if isinstance(self.status, BeliefStatus)
                else BeliefStatus(self.status)
            )
        except (TypeError, ValueError) as error:
            raise ValueError("status must be VALID, UNCERTAIN, or INVALID") from error

        if isinstance(self.confidence, bool) or not isinstance(self.confidence, Real):
            raise ValueError("confidence must be numeric")
        if not isfinite(float(self.confidence)) or not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        self.confidence = float(self.confidence)

        if not isinstance(self.explanation, str):
            raise ValueError("explanation must be a string")
        if not isinstance(self.evidence_summary, Mapping):
            raise ValueError("evidence_summary must be a mapping")
        expected = {"supporting_evidence", "contradicting_evidence"}
        if set(self.evidence_summary) != expected:
            raise ValueError("evidence_summary must contain supporting and contradicting evidence")
        lists = [self.evidence_summary[name] for name in expected]
        if any(not isinstance(items, list) for items in lists):
            raise ValueError("evidence entries must be lists")
        for name, items in zip(expected, lists):
            if len(items) > MAX_EVIDENCE_ITEMS:
                raise ValueError(
                    f"{name} cannot contain more than {MAX_EVIDENCE_ITEMS} items"
                )
