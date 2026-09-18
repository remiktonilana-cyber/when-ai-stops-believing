"""Deterministic mock Agent for pipeline validation only.

This agent is not used for scientific evaluation. It has no model calls, no
hidden-state access, and no claim of calibrated or rational behavior.
"""

from collections.abc import Mapping, Sequence

from src.lai_agent_schema import AgentBelief, BeliefStatus


OBSERVATION_FIELDS = frozenset({
    "fragility", "crowding", "liquidity_stress", "context_signal", "current_shock",
})
WARNING_STRESS_THRESHOLD = 0.65
CONTRADICTION_DEVIATION_THRESHOLD = 0.75
CONTRADICTION_COUNT_THRESHOLD = 3


class MockAgent:
    """Fixed-rule Agent used to validate downstream pipeline wiring."""

    def __init__(self):
        self._previous_status = None

    def __call__(self, observation, resolved_history=None, historical_summary=None):
        return self.respond(observation, resolved_history, historical_summary)

    def respond(self, observation, resolved_history=None, historical_summary=None):
        """Return one validated belief from Agent-visible inputs only.

        A contradiction is counted when at least three resolved pairs have
        ``abs(response - shock) > 0.75``. Otherwise, mean F/C/L >= 0.65 is a
        warning-like stress condition. These thresholds are pipeline fixtures,
        not scientific criteria.
        """
        if not isinstance(observation, Mapping):
            raise ValueError("observation must be a mapping")
        missing = OBSERVATION_FIELDS.difference(observation)
        if missing:
            raise ValueError(f"observation missing fields: {', '.join(sorted(missing))}")

        history = [] if resolved_history is None else list(resolved_history)
        contradiction_count = sum(
            abs(response - shock) > CONTRADICTION_DEVIATION_THRESHOLD
            for shock, response in (_resolved_pair(pair) for pair in history)
        )
        stress = sum(float(observation[field]) for field in (
            "fragility", "crowding", "liquidity_stress")) / 3.0

        if contradiction_count >= CONTRADICTION_COUNT_THRESHOLD:
            status = BeliefStatus.INVALID
            confidence = 0.9
            explanation = "Resolved contradiction evidence exceeds the mock rule."
            contradicting = ["resolved shock-response deviation"] * contradiction_count
            supporting = []
        elif stress >= WARNING_STRESS_THRESHOLD:
            status = BeliefStatus.UNCERTAIN
            confidence = 0.5
            explanation = "Observable stress exceeds the mock warning rule."
            supporting = ["warning-like observable stress"]
            contradicting = []
        else:
            status = BeliefStatus.VALID
            confidence = 0.8
            explanation = "Observable conditions remain within the mock normal range."
            supporting = ["normal observable conditions"]
            contradicting = []

        belief = AgentBelief(status, confidence, explanation, {
            "supporting_evidence": supporting,
            "contradicting_evidence": contradicting,
        })
        self._previous_status = belief.status
        return belief


def _resolved_pair(pair):
    """Read a visible resolved pair supplied as a 2-sequence or mapping."""
    if isinstance(pair, Mapping):
        if "shock" not in pair or "response" not in pair:
            raise ValueError("resolved evidence mappings need shock and response")
        return float(pair["shock"]), float(pair["response"])
    if isinstance(pair, Sequence) and not isinstance(pair, (str, bytes)) and len(pair) == 2:
        return float(pair[0]), float(pair[1])
    raise ValueError("resolved evidence must contain (shock, response) pairs")

