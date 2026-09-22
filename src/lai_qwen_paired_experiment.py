"""Resumable Qwen paired run for the frozen LAI canonical benchmark.

The runner is deliberately provider-independent at its orchestration boundary:
it receives a callable that maps a causal Agent input to a raw belief object.
Only the optional convenience function constructs the existing Qwen adapter.
"""

from copy import deepcopy
import json
from pathlib import Path

from src.lai_agent_contract import build_initialization_input, build_runtime_input, build_neutral_prompt
from src.lai_agent_schema import AgentBelief, BeliefStatus
from src.lai_agent_trajectory import AgentTrajectory
from src.lai_belief_metrics import compute_belief_metrics
from src.lai_paired_evaluator import compare_paired_trajectories
from src.lai_transition_environment import generate_transition
from src.lai_transition_reference import D_PLUS
from src.universal_llm_adapter import validate_model_output


EXPERIMENT_ID = "lai_qwen_e63a_seed42"
PROVIDER = "qwen"
MODEL = "qwen-plus"
SEED = 42
START_DAY = 350
END_DAY = 950


def _belief(raw):
    """Validate a provider object and construct the strict AgentBelief."""
    validate_model_output(raw)
    return AgentBelief(raw["belief_status"], raw["confidence"], raw["explanation"],
                       deepcopy(raw["evidence_summary"]))


def _safe_belief(belief):
    return {
        "status": belief.status.value,
        "confidence": belief.confidence,
        "explanation": belief.explanation,
        "evidence_summary": deepcopy(dict(belief.evidence_summary)),
    }


def _read_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")


def _append_jsonl(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, sort_keys=True) + "\n")


def _records(path):
    if not path.exists():
        return {}
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        result[int(record["timestep"])] = record
    return result


def _record(experiment_id, provider, model, world_name, timestep, belief):
    return {"experiment_id": experiment_id, "provider": provider, "model": model,
            "world": world_name, "timestep": timestep, **_safe_belief(belief)}


def _invoke_validated(provider, agent_input, audit=None):
    """Accept one valid response, with one bounded technical-format retry."""
    for attempt in range(2):
        try:
            raw = provider(agent_input)
            belief = _belief(raw)
            if audit is not None:
                audit.setdefault("technical_retries", []).extend(
                    [{"reason": "malformed structured output", "attempt": attempt}]
                    if attempt else []
                )
            return belief
        except ValueError as error:
            message = str(error)
            format_error = any(token in message.lower() for token in
                               ("malformed", "structured output", "evidence_summary", "json"))
            if not format_error or attempt == 1:
                raise
            if audit is not None:
                audit.setdefault("technical_retries", []).append(
                    {"reason": "malformed structured output", "attempt": attempt + 1}
                )
    raise AssertionError("unreachable")


def _audit_input(agent_input, previous_required):
    forbidden = {"alpha", "latent_state", "latent_stress", "phase", "regime",
                 "T_warning", "T_structural", "T_delta", "T_evidence",
                 "future_response", "future_observations", "next_response",
                 "response", "evidence_detector"}
    if forbidden.intersection(agent_input):
        raise AssertionError("hidden field reached provider input")
    if forbidden.intersection(agent_input.get("current_observation", {})):
        raise AssertionError("hidden field reached current observation")
    if len(agent_input.get("resolved_history", [])) > 50:
        raise AssertionError("resolved history exceeded 50")
    previous = agent_input.get("previous_belief")
    if previous_required and (previous is None or "explanation" in previous):
        raise AssertionError("previous explanation or belief missing")


def _trajectory_from_records(world, records, start=START_DAY, end=END_DAY):
    trajectory = AgentTrajectory()
    previous = None
    for timestep in range(start, end + 1):
        record = records[timestep]
        belief = _belief({"belief_status": record["status"], "confidence": record["confidence"],
                          "explanation": record["explanation"],
                          "evidence_summary": record["evidence_summary"]})
        input_data = build_runtime_input(world, timestep, previous)
        trajectory.append(timestep, input_data["current_observation"], belief)
        previous = belief
    return trajectory


def _run_world(provider, world, world_name, artifact_dir, initialization_belief,
               *, experiment_id=EXPERIMENT_ID, start=START_DAY, end=END_DAY,
               provider_name=PROVIDER, model=MODEL, call_audit=None):
    path = Path(artifact_dir) / f"{world_name.lower()}_trajectory.jsonl"
    records = _records(path)
    trajectory = AgentTrajectory()
    previous = deepcopy(initialization_belief)
    for timestep in range(start, end + 1):
        if timestep not in records and any(existing > timestep for existing in records):
            raise ValueError(f"non-contiguous persisted records for {world_name}")
        if timestep in records:
            belief = _belief({"belief_status": records[timestep]["status"],
                              "confidence": records[timestep]["confidence"],
                              "explanation": records[timestep]["explanation"],
                              "evidence_summary": records[timestep]["evidence_summary"]})
        else:
            agent_input = build_runtime_input(world, timestep, previous)
            _audit_input(agent_input, previous_required=True)
            if timestep == 351:
                pair = agent_input["resolved_history"][-1]
                expected = (float(world.iloc[350]["shock"]), float(world.iloc[350]["next_response"]))
                if pair != expected:
                    raise AssertionError("Day 350 resolved pair missing at Day 351")
            try:
                if call_audit is not None:
                    call_audit.setdefault("logical_calls", []).append({"world": world_name, "timestep": timestep})
                belief = _invoke_validated(provider, agent_input, call_audit)
            except Exception as error:
                _write_json(Path(artifact_dir) / "failure.json", {
                    "experiment_id": experiment_id, "stage": world_name,
                    "timestep": timestep, "failure_type": type(error).__name__,
                    "failure_message": str(error),
                    "technical_retry_count": 1 if isinstance(error, ValueError) else 0,
                    "technical_retry_reason": "malformed structured output" if isinstance(error, ValueError) else None,
                    "provider_diagnostics": deepcopy(getattr(provider, "last_response_diagnostics", None)),
                })
                raise
            record = _record(experiment_id, provider_name, model, world_name, timestep, belief)
            _append_jsonl(path, record)
            records[timestep] = record
        input_data = build_runtime_input(world, timestep, previous)
        trajectory.append(timestep, input_data["current_observation"], belief)
        previous = deepcopy(belief)
    return trajectory, records


def run_paired_experiment(provider, *, transition_world, control_world,
                          artifact_dir, experiment_id=EXPERIMENT_ID,
                          start=START_DAY, end=END_DAY, provider_name=PROVIDER,
                          model=MODEL):
    """Run/resume initialization, transition, then control in that order."""
    artifact_dir = Path(artifact_dir)
    init_path = artifact_dir / "initialization.json"
    metadata = {"experiment_id": experiment_id, "provider": provider_name,
                "model": model, "worlds": ["Transition", "Control"],
                "start_day": start, "end_day": end}
    _write_json(artifact_dir / "run_metadata.json", metadata)
    init_data = _read_json(init_path)
    if init_data is None:
        init_input = build_initialization_input(transition_world, initialization_timestep=349)
        _audit_input(init_input, previous_required=False)
        init_belief = _invoke_validated(provider, init_input)
        _write_json(init_path, {"experiment_id": experiment_id, "provider": provider_name,
                                "model": model, "timestep": 349, **_safe_belief(init_belief)})
    else:
        init_belief = _belief({"belief_status": init_data["status"], "confidence": init_data["confidence"],
                               "explanation": init_data["explanation"],
                               "evidence_summary": init_data["evidence_summary"]})
    if init_belief.status is not BeliefStatus.VALID:
        return {"status": "INITIAL BELIEF NOT ESTABLISHED", "initialization": _safe_belief(init_belief),
                "initialization_calls": 1, "transition": None, "control": None}

    transition, transition_records = _run_world(
        provider, transition_world, "Transition", artifact_dir, deepcopy(init_belief),
        experiment_id=experiment_id, start=start, end=end, provider_name=provider_name, model=model)
    control, control_records = _run_world(
        provider, control_world, "Control", artifact_dir, deepcopy(init_belief),
        experiment_id=experiment_id, start=start, end=end, provider_name=provider_name, model=model)
    metrics = {"Transition": compute_belief_metrics(transition.steps()),
               "Control": compute_belief_metrics(control.steps())}
    paired = compare_paired_trajectories(transition.steps(), control.steps())
    _write_json(artifact_dir / "metrics.json", metrics)
    _write_json(artifact_dir / "paired_evaluation.json", paired)
    result = {"status": "PASS", "initialization": _safe_belief(init_belief),
            "initialization_calls": 1, "transition": metrics["Transition"],
            "control": metrics["Control"], "paired": paired,
            "successful_model_responses": 1 + len(transition_records) + len(control_records),
            "transition_length": len(transition), "control_length": len(control)}
    _write_json(artifact_dir / "run_summary.json", result)
    return result


def run_qwen_paired_experiment(*, artifact_dir="results/lai_qwen_e63a", seed=SEED,
                               d_plus=D_PLUS, start=START_DAY, end=END_DAY):
    """Construct the frozen canonical worlds and call the existing Qwen adapter."""
    from src.lai_agent_contract import build_neutral_prompt
    from src.qwen_provider import QwenProvider
    transition_world = generate_transition(seed, d_plus, control=False)
    control_world = generate_transition(seed, d_plus, control=True)
    provider = QwenProvider(prompt_builder=build_neutral_prompt)
    return run_paired_experiment(provider, transition_world=transition_world,
                                 control_world=control_world, artifact_dir=artifact_dir,
                                 model=getattr(provider, "model", MODEL))
