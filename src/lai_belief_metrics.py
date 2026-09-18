"""Deterministic metrics for stored LAI Agent belief trajectories.

The functions consume recorded ``TrajectoryStep`` objects (or equivalent
objects with ``timestamp`` and ``belief`` attributes). They inspect only the
recorded belief status/confidence and timestamps; no environment ground truth
or provider code is involved.
"""

from collections import Counter

from src.lai_agent_schema import BeliefStatus


PHASE_WINDOWS = {
    "350-399": (350, 399), "400-599": (400, 599), "600-674": (600, 674),
    "675-709": (675, 709), "710-899": (710, 899), "900-950": (900, 950),
}
TRANSITION_KEYS = (
    "VALID->UNCERTAIN", "VALID->INVALID", "UNCERTAIN->VALID",
    "UNCERTAIN->INVALID", "INVALID->VALID", "INVALID->UNCERTAIN",
)


def _steps(trajectory):
    result = list(trajectory)
    for step in result:
        if not hasattr(step, "timestamp") or not hasattr(step, "belief"):
            raise ValueError("trajectory steps must contain timestamp and belief")
        if not isinstance(step.belief.status, BeliefStatus):
            raise ValueError("trajectory beliefs must use BeliefStatus")
    return result


def compute_timing_metrics(trajectory, stable_horizon=20):
    """Return first uncertainty/invalidation and stable-invalid timestamps."""
    if stable_horizon < 1:
        raise ValueError("stable_horizon must be positive")
    steps = _steps(trajectory)
    statuses = [step.belief.status for step in steps]
    first_uncertain = next((s.timestamp for s in steps if s.belief.status is BeliefStatus.UNCERTAIN), None)
    first_invalid = next((s.timestamp for s in steps if s.belief.status is BeliefStatus.INVALID), None)
    onset = confirmed = None
    for index in range(len(statuses) - stable_horizon + 1):
        if all(status is BeliefStatus.INVALID for status in statuses[index:index + stable_horizon]):
            onset = steps[index].timestamp
            confirmed = steps[index + stable_horizon - 1].timestamp
            break
    return {"T_U": first_uncertain, "T_I": first_invalid,
            "T_SI_onset": onset, "T_SI_confirmed": confirmed}


def compute_relative_timing(timing, evidence_time=710):
    """Return uncertainty/invalidation times relative to evidence time."""
    return {
        "T_U_relative": None if timing.get("T_U") is None else timing["T_U"] - evidence_time,
        "T_I_relative": None if timing.get("T_I") is None else timing["T_I"] - evidence_time,
    }


def compute_transition_matrix(trajectory):
    """Count the six directed status transitions requested by the benchmark."""
    steps = _steps(trajectory)
    counts = Counter(f"{a.belief.status.value}->{b.belief.status.value}" for a, b in zip(steps, steps[1:]))
    return {key: counts[key] for key in TRANSITION_KEYS}


def find_invalid_episodes(trajectory):
    """Return inclusive timestamp boundaries and lengths of INVALID episodes."""
    steps = _steps(trajectory)
    episodes, start = [], None
    for index, step in enumerate(steps):
        invalid = step.belief.status is BeliefStatus.INVALID
        if invalid and start is None:
            start = index
        if start is not None and (not invalid or index == len(steps) - 1):
            end = index if invalid else index - 1
            episodes.append({"start": steps[start].timestamp, "end": steps[end].timestamp,
                             "length": end - start + 1})
            start = None
    return episodes


def compute_phase_occupancy(trajectory):
    """Summarize status percentages and confidence in fixed inclusive windows."""
    steps, result = _steps(trajectory), {}
    for name, (start, end) in PHASE_WINDOWS.items():
        selected = []
        for step in steps:
            try:
                if start <= step.timestamp <= end:
                    selected.append(step)
            except TypeError as error:
                raise ValueError("phase occupancy requires numeric timestamps") from error
        count = len(selected)
        if not count:
            result[name] = {"VALID_percentage": None, "UNCERTAIN_percentage": None,
                            "INVALID_percentage": None, "mean_confidence": None,
                            "median_confidence": None}
            continue
        status_counts = Counter(step.belief.status.value for step in selected)
        confidences = sorted(step.belief.confidence for step in selected)
        midpoint = count // 2
        median = confidences[midpoint] if count % 2 else (confidences[midpoint - 1] + confidences[midpoint]) / 2
        result[name] = {
            "VALID_percentage": 100 * status_counts["VALID"] / count,
            "UNCERTAIN_percentage": 100 * status_counts["UNCERTAIN"] / count,
            "INVALID_percentage": 100 * status_counts["INVALID"] / count,
            "mean_confidence": sum(confidences) / count,
            "median_confidence": median,
        }
    return result


def compute_post_evidence_valid_ratio(trajectory, start=710, end=950):
    """Return the inclusive-window ratio of VALID beliefs, or None if empty."""
    selected = [s for s in _steps(trajectory) if start <= s.timestamp <= end]
    return None if not selected else sum(s.belief.status is BeliefStatus.VALID for s in selected) / len(selected)


def compute_belief_metrics(trajectory, evidence_time=710, stable_horizon=20):
    """Return all deterministic belief metrics in one dictionary."""
    timing = compute_timing_metrics(trajectory, stable_horizon=stable_horizon)
    return {**timing, **compute_relative_timing(timing, evidence_time),
            "transition_matrix": compute_transition_matrix(trajectory),
            "invalid_episodes": find_invalid_episodes(trajectory),
            "phase_occupancy": compute_phase_occupancy(trajectory),
            "post_evidence_valid_ratio": compute_post_evidence_valid_ratio(trajectory)}

