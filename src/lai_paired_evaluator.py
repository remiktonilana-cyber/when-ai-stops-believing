"""Descriptive comparison utilities for matched LAI belief trajectories.

Only timestamps and belief status/confidence are read. Observation payloads are
intentionally ignored, so hidden environment fields cannot affect comparison.
No score, ranking, or pass/fail judgment is produced.
"""

from src.lai_agent_schema import BeliefStatus


PRE_DIVERGENCE_START = 350
PRE_DIVERGENCE_END = 599


def _steps(trajectory):
    steps = list(trajectory)
    for step in steps:
        if not hasattr(step, "timestamp") or not hasattr(step, "belief"):
            raise ValueError("trajectory steps must contain timestamp and belief")
        if not isinstance(step.belief.status, BeliefStatus):
            raise ValueError("trajectory beliefs must use BeliefStatus")
    return steps


def _paired_steps(transition, control):
    transition_steps, control_steps = _steps(transition), _steps(control)
    if len(transition_steps) != len(control_steps):
        raise ValueError("paired trajectories must have equal length")
    pairs = []
    for transition_step, control_step in zip(transition_steps, control_steps):
        if transition_step.timestamp != control_step.timestamp:
            raise ValueError("paired trajectories must have matching timestamps")
        pairs.append((transition_step, control_step))
    return pairs


def pre_divergence_agreement(transition, control):
    """Compare status and confidence over inclusive timestamps 350 through 599."""
    pairs = [
        pair for pair in _paired_steps(transition, control)
        if PRE_DIVERGENCE_START <= pair[0].timestamp <= PRE_DIVERGENCE_END
    ]
    count = len(pairs)
    status_matches = sum(a.belief.status is b.belief.status for a, b in pairs)
    confidence_differences = [abs(a.belief.confidence - b.belief.confidence) for a, b in pairs]
    return {
        "window_start": PRE_DIVERGENCE_START,
        "window_end": PRE_DIVERGENCE_END,
        "n_compared": count,
        "status_agreement_count": status_matches,
        "status_agreement_rate": status_matches / count if count else None,
        "confidence_exact_agreement_count": sum(diff == 0 for diff in confidence_differences),
        "confidence_mean_absolute_difference": (
            sum(confidence_differences) / count if count else None
        ),
        "confidence_max_absolute_difference": max(confidence_differences, default=None),
    }


def first_status_divergence(transition, control):
    """Return the first paired timestamp whose statuses differ, or None."""
    for transition_step, control_step in _paired_steps(transition, control):
        if transition_step.belief.status is not control_step.belief.status:
            return {
                "timestamp": transition_step.timestamp,
                "transition_status": transition_step.belief.status.value,
                "control_status": control_step.belief.status.value,
            }
    return None


def control_abandonment(control):
    """Report whether and when the control belief first entered INVALID."""
    steps = _steps(control)
    first_invalid = next(
        (step.timestamp for step in steps if step.belief.status is BeliefStatus.INVALID),
        None,
    )
    return {"entered_invalid": first_invalid is not None, "first_invalid_timestamp": first_invalid}


def compare_paired_trajectories(transition, control):
    """Return the complete descriptive summary for a matched trajectory pair."""
    return {
        "pre_divergence_agreement": pre_divergence_agreement(transition, control),
        "first_status_divergence": first_status_divergence(transition, control),
        "control_abandonment": control_abandonment(control),
    }

