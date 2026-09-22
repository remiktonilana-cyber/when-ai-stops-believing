import json

import pytest

from src.lai_agent_schema import BeliefStatus
from src.lai_qwen_paired_experiment import run_paired_experiment
from src.lai_transition_environment import generate_transition
from src.lai_transition_reference import D_PLUS


def _raw(status="VALID", confidence=.8, explanation="ok"):
    return {"belief_status": status, "confidence": confidence, "explanation": explanation,
            "evidence_summary": {"supporting_evidence": [], "contradicting_evidence": []}}


class FakeProvider:
    model = "fake"

    def __init__(self, init_status="VALID", fail_after=None):
        self.calls = []
        self.init_status = init_status
        self.fail_after = fail_after

    def __call__(self, value):
        self.calls.append(value)
        if self.fail_after is not None and len(self.calls) > self.fail_after:
            raise RuntimeError("synthetic network failure")
        if len(self.calls) == 1:
            return _raw(self.init_status, .9, "initial explanation must not recur")
        return _raw("VALID", .7, f"step {len(self.calls)}")


def _worlds():
    return generate_transition(1000, D_PLUS), generate_transition(1000, D_PLUS, control=True)


def test_paired_runner_order_causality_and_safe_fields(tmp_path):
    transition, control = _worlds()
    provider = FakeProvider()
    result = run_paired_experiment(provider, transition_world=transition, control_world=control,
                                   artifact_dir=tmp_path, start=350, end=352)
    assert result["status"] == "PASS"
    assert len(provider.calls) == 1 + 3 + 3
    assert provider.calls[1]["previous_belief"] == provider.calls[4]["previous_belief"]
    assert provider.calls[1]["previous_belief"] is not provider.calls[4]["previous_belief"]
    assert "next_response" not in provider.calls[1]["current_observation"]
    assert "explanation" not in provider.calls[1]["previous_belief"]
    assert provider.calls[2]["resolved_history"][-1] == (
        float(transition.iloc[350]["shock"]), float(transition.iloc[350]["next_response"])
    )
    assert len(provider.calls[2]["resolved_history"]) <= 50
    forbidden = {"alpha", "latent_state", "latent_stress", "T_warning", "T_structural",
                 "T_delta", "T_evidence", "future_response", "future_observations"}
    assert not forbidden.intersection(provider.calls[1])
    assert not forbidden.intersection(provider.calls[1]["current_observation"])
    assert result["transition_length"] == result["control_length"] == 3


def test_non_valid_initialization_stops_without_retry(tmp_path):
    transition, control = _worlds()
    provider = FakeProvider(init_status="UNCERTAIN")
    result = run_paired_experiment(provider, transition_world=transition, control_world=control,
                                   artifact_dir=tmp_path, start=350, end=352)
    assert result["status"] == "INITIAL BELIEF NOT ESTABLISHED"
    assert len(provider.calls) == 1
    assert not (tmp_path / "transition_trajectory.jsonl").exists()


def test_resume_does_not_repeat_successful_records(tmp_path):
    transition, control = _worlds()
    first = FakeProvider(fail_after=3)  # init + two Transition steps
    with pytest.raises(RuntimeError):
        run_paired_experiment(first, transition_world=transition, control_world=control,
                               artifact_dir=tmp_path, start=350, end=352)
    assert len(first.calls) == 4
    second = FakeProvider()
    result = run_paired_experiment(second, transition_world=transition, control_world=control,
                                   artifact_dir=tmp_path, start=350, end=352)
    assert result["status"] == "PASS"
    # initialization and two saved Transition steps are reused; remaining step + 3 Control.
    assert len(second.calls) == 4
    lines = (tmp_path / "transition_trajectory.jsonl").read_text().splitlines()
    assert [json.loads(line)["timestep"] for line in lines] == [350, 351, 352]


def test_initialization_has_only_day349_causal_history(tmp_path):
    transition, control = _worlds()
    provider = FakeProvider()
    run_paired_experiment(provider, transition_world=transition, control_world=control,
                           artifact_dir=tmp_path, start=350, end=350)
    init_input = provider.calls[0]
    assert len(init_input["resolved_history"]) == 50
    assert init_input["historical_summary"]["resolved_count"] == 349
    assert "current_observation" not in init_input
