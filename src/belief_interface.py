"""Belief state interface for adaptive intelligence benchmark."""

from datetime import datetime


VALID_BELIEF_STATUS = {
    "VALID",
    "UNCERTAIN",
    "INVALID",
}


def create_belief_state(
    timestamp,
    belief_status,
    confidence,
    explanation="",
    evidence_summary=None,
):
    """
    Create a standardized AI belief state.
    """

    validate_belief_status(belief_status)

    if not 0 <= confidence <= 1:
        raise ValueError(
            "confidence must be between 0 and 1"
        )

    if evidence_summary is None:
        evidence_summary = {
            "supporting_evidence": [],
            "contradicting_evidence": [],
        }

    return {
        "timestamp": timestamp,
        "belief_status": belief_status,
        "confidence": confidence,
        "explanation": explanation,
        "evidence_summary": evidence_summary,
    }


def validate_belief_status(
    belief_status
):
    """
    Ensure belief status follows benchmark definition.
    """

    if belief_status not in VALID_BELIEF_STATUS:
        raise ValueError(
            "Invalid belief status"
        )

    return True


def validate_belief_state(
    belief_state
):
    """
    Validate complete belief state structure.
    """

    required_fields = {
        "timestamp",
        "belief_status",
        "confidence",
        "explanation",
        "evidence_summary",
    }

    if not required_fields.issubset(
        belief_state.keys()
    ):
        raise ValueError(
            "Missing belief state fields"
        )

    validate_belief_status(
        belief_state["belief_status"]
    )

    if not (
        0 <= belief_state["confidence"] <= 1
    ):
        raise ValueError(
            "Invalid confidence value"
        )

    return True


def append_belief_history(
    history,
    belief_state
):
    """
    Append a belief state to a temporal trajectory.
    """

    validate_belief_state(
        belief_state
    )

    history.append(
        belief_state
    )

    return history