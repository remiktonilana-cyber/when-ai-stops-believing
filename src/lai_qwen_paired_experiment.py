"""Resumable Qwen paired run for the frozen LAI canonical benchmark.

The runner is deliberately provider-independent at its orchestration boundary:
it receives a callable that maps a causal Agent input to a raw belief object.
Convenience functions configure Qwen or DeepSeek over the same pipeline.
"""

from copy import deepcopy
import json
import hashlib
import os
import fcntl
from functools import wraps
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
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("invalid checkpoint object")
    return value


def _atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".pending-write")
    # Leave interrupted writes for explicit inspection; never silently replay.
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    directory = os.open(str(path.parent), os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _write_json(path, value):
    _atomic_write(path, json.dumps(value, indent=2, sort_keys=True))


def _append_jsonl(path, value):
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    _atomic_write(path, existing + json.dumps(value, sort_keys=True) + "\n")


def _records(path):
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if not text or not text.endswith("\n"):
        raise ValueError("incomplete trajectory checkpoint")
    result = {}
    for line in text.splitlines():
        record = json.loads(line)
        if not isinstance(record, dict) or "timestep" not in record:
            raise ValueError("invalid trajectory checkpoint record")
        timestep = record["timestep"]
        if type(timestep) is not int:
            raise ValueError("invalid checkpoint timestamp")
        if timestep in result:
            raise ValueError("duplicate checkpoint timestamp")
        result[timestep] = record
    return result


def _locked_run(function):
    @wraps(function)
    def locked(*args, **kwargs):
        directory = Path(kwargs["artifact_dir"])
        directory.mkdir(parents=True, exist_ok=True)
        with (directory / ".runtime.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ValueError("checkpoint already in use") from None
            try:
                if list(directory.glob("*.pending-write")):
                    raise ValueError("incomplete atomic checkpoint write")
                return function(*args, **kwargs)
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)
    return locked


def _checkpoint_belief(record, identity):
    if any(record.get(key) != value for key, value in identity.items()):
        raise ValueError("inconsistent checkpoint provenance")
    return _belief({"belief_status": record["status"], "confidence": record["confidence"],
                    "explanation": record["explanation"], "evidence_summary": record["evidence_summary"]})


def _failure(directory, stage, timestep, error, audit):
    # Only fixed categories and numeric counters; no exception/provider text.
    _write_json(Path(directory) / "failure.json", {
        "stage": stage, "timestep": timestep,
        "error_category": "validation" if isinstance(error, ValueError) else "provider_failure",
        "technical_retry_count": len(audit.get("technical_retries", [])),
        "provider_diagnostics": None,
    })


def _call_and_checkpoint(provider, agent_input, directory, stage, timestep, persist, call_audit=None):
    directory = Path(directory)
    pending = directory / "inflight.json"
    _write_json(pending, {"stage": stage, "timestep": timestep})
    audit = {}
    if call_audit is not None:
        call_audit.setdefault("logical_calls", []).append({"world": stage, "timestep": timestep})
    try:
        belief = _invoke_validated(provider, agent_input, audit)
    except Exception as error:
        _failure(directory, stage, timestep, error, audit)
        pending.unlink()
        raise
    finally:
        if call_audit is not None:
            call_audit.setdefault("technical_retries", []).extend(audit.get("technical_retries", []))
    # If persistence fails, keep the marker: the successful call must not replay.
    persist(belief)
    pending.unlink()
    return belief


def _record(experiment_id, provider, model, world_name, timestep, belief):
    return {"experiment_id": experiment_id, "provider": provider, "model": model,
            "world": world_name, "timestep": timestep, **_safe_belief(belief)}


def _invoke_validated(provider, agent_input, audit=None):
    """Accept one valid response, with one bounded technical-format retry."""
    for attempt in range(2):
        try:
            raw = provider(agent_input)
            belief = _belief(raw)
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
            belief = _call_and_checkpoint(
                provider, agent_input, artifact_dir, world_name, timestep,
                lambda value: _append_jsonl(path, _record(
                    experiment_id, provider_name, model, world_name, timestep, value)), call_audit)
            record = _record(experiment_id, provider_name, model, world_name, timestep, belief)
            records[timestep] = record
        input_data = build_runtime_input(world, timestep, previous)
        trajectory.append(timestep, input_data["current_observation"], belief)
        previous = deepcopy(belief)
    return trajectory, records


@_locked_run
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
    metadata["world_fingerprints"] = {
        name: hashlib.sha256(world.to_csv(index=True, float_format="%.17g").encode()).hexdigest()
        for name, world in (("Transition", transition_world), ("Control", control_world))
    }
    metadata_path = artifact_dir / "run_metadata.json"
    existing_metadata = _read_json(metadata_path)
    init_data = _read_json(init_path)
    saved = {name: _records(artifact_dir / f"{name.lower()}_trajectory.jsonl")
             for name in ("Transition", "Control")}
    identity = {"experiment_id": experiment_id, "provider": provider_name, "model": model}
    if existing_metadata is not None and existing_metadata != metadata:
        raise ValueError("inconsistent checkpoint configuration")
    if existing_metadata is None and (init_data is not None or any(saved.values())):
        raise ValueError("checkpoint metadata missing")
    if init_data is None and any(saved.values()):
        raise ValueError("checkpoint initialization missing")
    init_belief = None if init_data is None else _checkpoint_belief(init_data, {**identity, "timestep": 349})
    for name, records in saved.items():
        if list(records) != list(range(start, start + len(records))) or len(records) > end - start + 1:
            raise ValueError("non-contiguous or out-of-range checkpoint")
        for timestep, record in records.items():
            _checkpoint_belief(record, {**identity, "world": name, "timestep": timestep})
    if saved["Control"] and len(saved["Transition"]) != end - start + 1:
        raise ValueError("control checkpoint precedes completed transition")
    if any(saved.values()) and init_belief.status is not BeliefStatus.VALID:
        raise ValueError("trajectory checkpoint has non-valid initialization")
    pending_path = artifact_dir / "inflight.json"
    if pending_path.exists():
        pending = _read_json(pending_path)
        completed = (pending == {"stage": "initialization", "timestep": 349} and init_data is not None)
        completed = completed or any(pending == {"stage": name, "timestep": timestep}
                                     for name, records in saved.items() for timestep in records)
        if not completed:
            raise ValueError("unresolved in-flight call; refusing regeneration")
        pending_path.unlink()
    if existing_metadata is None:
        _write_json(metadata_path, metadata)
    if init_data is None:
        init_input = build_initialization_input(transition_world, initialization_timestep=349)
        _audit_input(init_input, previous_required=False)
        init_belief = _call_and_checkpoint(
            provider, init_input, artifact_dir, "initialization", 349,
            lambda value: _write_json(init_path, {**identity, "timestep": 349, **_safe_belief(value)}))
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


def run_deepseek_paired_experiment(*, artifact_dir="results/lai_deepseek_e63c"):
    """Explicit DeepSeek configuration over the unchanged canonical pipeline."""
    from src.deepseek_provider import DeepSeekProvider
    provider = DeepSeekProvider(model="deepseek-v4-flash", prompt_builder=build_neutral_prompt)
    return run_paired_experiment(
        provider, transition_world=generate_transition(42, D_PLUS, control=False),
        control_world=generate_transition(42, D_PLUS, control=True),
        artifact_dir=artifact_dir, experiment_id="lai_deepseek_e63c_seed42",
        provider_name="deepseek", model="deepseek-v4-flash", start=350, end=950)
