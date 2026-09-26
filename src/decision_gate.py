"""Provider-neutral permission assessment; no execution or human-approval bypass.

Inputs are caller-supplied observations, not new scientific measurements. None
means unavailable. Freshness is evaluated upstream against application needs.
Policy v1 is an explicit prototype policy, not a calibrated risk estimator.
"""

from dataclasses import dataclass, fields
from math import isfinite
from numbers import Real
from typing import Optional

from src.lai_agent_schema import BeliefStatus


POLICY_ID = "minimum-universal-gate"
POLICY_VERSION = "1"


@dataclass(frozen=True)
class DecisionRequest:
    action_id: str
    proposed_action: str
    belief_status: Optional[str] = None
    confidence: Optional[float] = None
    evidence_conflict: Optional[bool] = None
    # Number of consecutive observations retaining the current belief status.
    # Descriptive only: no persistence threshold implies correctness.
    belief_persistence: Optional[int] = None
    context_shift: Optional[bool] = None
    data_quality: Optional[str] = None  # GOOD | DEGRADED | UNUSABLE
    data_freshness: Optional[str] = None  # FRESH | STALE
    system_health: Optional[str] = None  # HEALTHY | UNHEALTHY
    consequence_level: Optional[str] = None  # LOW | HIGH
    reversibility: Optional[str] = None  # HIGH | LOW
    policy_id: Optional[str] = POLICY_ID
    policy_version: Optional[str] = POLICY_VERSION


@dataclass(frozen=True)
class Assessment:
    missing_fields: tuple[str, ...]
    blocking_reasons: tuple[str, ...]
    review_reasons: tuple[str, ...]


@dataclass(frozen=True)
class GateDecision:
    permission: str
    reason_codes: tuple[str, ...]
    requires_human_review: bool
    action_id: str
    proposed_action: str
    policy_id: str
    policy_version: str
    assessment: Assessment


def _validate(request):
    if not isinstance(request, DecisionRequest):
        raise TypeError("request must be a DecisionRequest")
    for name in ("action_id", "proposed_action"):
        value = getattr(request, name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a nonempty string")
    choices = {
        "belief_status": tuple(status.value for status in BeliefStatus),
        "data_quality": ("GOOD", "DEGRADED", "UNUSABLE"),
        "data_freshness": ("FRESH", "STALE"),
        "system_health": ("HEALTHY", "UNHEALTHY"),
        "consequence_level": ("LOW", "HIGH"),
        "reversibility": ("HIGH", "LOW"),
    }
    for name, allowed in choices.items():
        value = getattr(request, name)
        if value is not None and (not isinstance(value, str) or value not in allowed):
            raise ValueError(f"{name} must be one of {allowed} or None")
    for name in ("evidence_conflict", "context_shift"):
        value = getattr(request, name)
        if value is not None and type(value) is not bool:
            raise ValueError(f"{name} must be a bool or None")
    value = request.confidence
    if value is not None and (
        isinstance(value, bool) or not isinstance(value, Real)
        or not isfinite(value) or not 0 <= value <= 1
    ):
        raise ValueError("confidence must be finite and between 0 and 1, or None")
    value = request.belief_persistence
    if value is not None and (type(value) is not int or value < 0):
        raise ValueError("belief_persistence must be a nonnegative integer or None")
    for name in ("policy_id", "policy_version"):
        value = getattr(request, name)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"{name} must be a nonempty string or None")


def evaluate(request: DecisionRequest) -> GateDecision:
    """Validate and assess one action. Malformed inputs raise; missing inputs block.

    RED takes precedence over YELLOW. There is intentionally no confirmation
    parameter: YELLOW is a review requirement, never an execution authorization.
    Returned decisions are snapshots, not durable production execution tokens.
    """
    _validate(request)
    missing = tuple(field.name for field in fields(request)
                    if getattr(request, field.name) is None)
    blocking = []
    review = []
    if missing:
        blocking.append("MISSING_REQUIRED_INFORMATION")
    if ((request.policy_id is not None and request.policy_id != POLICY_ID)
            or (request.policy_version is not None and request.policy_version != POLICY_VERSION)):
        blocking.append("UNSUPPORTED_POLICY")
    for condition, reason in (
        (request.data_freshness == "STALE", "STALE_REQUIRED_DATA"),
        (request.data_quality == "UNUSABLE", "UNUSABLE_REQUIRED_DATA"),
        (request.system_health == "UNHEALTHY", "SYSTEM_UNHEALTHY"),
        (request.belief_status == "INVALID", "BELIEF_INVALID"),
    ):
        if condition:
            blocking.append(reason)
    for condition, reason in (
        (request.belief_status == "UNCERTAIN", "BELIEF_UNCERTAIN"),
        (request.evidence_conflict is True, "EVIDENCE_CONFLICT"),
        (request.context_shift is True, "CONTEXT_SHIFT"),
        (request.data_quality == "DEGRADED", "DEGRADED_REQUIRED_DATA"),
        (request.consequence_level == "HIGH", "HIGH_CONSEQUENCE"),
        (request.reversibility == "LOW", "LOW_REVERSIBILITY"),
    ):
        if condition:
            review.append(reason)
    permission = "RED" if blocking else "YELLOW" if review else "GREEN"
    reasons = tuple(blocking + review)
    if permission == "YELLOW":
        reasons += ("HUMAN_REVIEW_REQUIRED",)
    elif permission == "GREEN":
        reasons = ("POLICY_REQUIREMENTS_MET",)
    return GateDecision(
        permission, reasons, permission == "YELLOW",
        request.action_id, request.proposed_action, POLICY_ID, POLICY_VERSION,
        Assessment(missing, tuple(blocking), tuple(review)),
    )
