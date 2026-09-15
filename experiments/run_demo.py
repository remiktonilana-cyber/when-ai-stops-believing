"""Run the frozen 451-timestep Minimum Demo protocol."""

import argparse
import json
import sys
import traceback
from pathlib import Path
from urllib.error import HTTPError

import pandas as pd


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from src.codex_cli_provider import CodexCLIProvider
from src.deepseek_provider import DeepSeekProvider
from src.evaluation_engine import (
    calculate_adaptation_delay,
    calculate_belief_boundary_awareness,
    calculate_false_persistence,
)
from src.observation_builder import build_observation_sequence
from src.qwen_provider import QwenProvider
from src.universal_llm_adapter import run_llm_agent, validate_model_output


START_DAY = 950
END_DAY = 1400
DEMO_TIMESTEPS = END_DAY - START_DAY + 1
DEFAULT_MARKET_PATH = REPOSITORY_ROOT / "data" / "synthetic_market.csv"
RESULTS_DIRECTORY = REPOSITORY_ROOT / "results"


def select_demo_window(market):
    """Return aligned market rows and observations for Days 950 through 1400."""
    if len(market) <= END_DAY:
        raise ValueError(
            f"Benchmark data must contain Day {END_DAY}; found {len(market)} rows"
        )

    observations = build_observation_sequence(market)
    demo_market = market.iloc[START_DAY : END_DAY + 1].reset_index(drop=True)
    demo_observations = observations[START_DAY : END_DAY + 1]

    if len(demo_market) != DEMO_TIMESTEPS or len(demo_observations) != DEMO_TIMESTEPS:
        raise ValueError("Demo window must contain exactly 451 timesteps")
    return demo_market, demo_observations


def create_provider(provider_name):
    """Construct one of the providers supported by the frozen demo."""
    providers = {
        "codex": CodexCLIProvider,
        "deepseek": DeepSeekProvider,
        "qwen": QwenProvider,
    }
    try:
        return providers[provider_name]()
    except KeyError as error:
        raise ValueError(f"Unsupported provider: {provider_name}") from error


def evaluate_trajectory(demo_market, trajectory):
    """Run only the three metrics specified for the Minimum Demo."""
    belief_history = pd.DataFrame(trajectory)
    adaptation_delay = calculate_adaptation_delay(demo_market, belief_history)
    boundary_awareness = calculate_belief_boundary_awareness(
        demo_market,
        belief_history,
    )
    return {
        "adaptation_delay": (
            "right-censored" if adaptation_delay is None else int(adaptation_delay)
        ),
        "false_persistence": int(
            calculate_false_persistence(demo_market, belief_history)
        ),
        "belief_boundary_awareness": (
            None if boundary_awareness is None else int(boundary_awareness)
        ),
    }


def save_trajectory(trajectory, output_path):
    """Persist the benchmark-owned belief trajectory as JSON."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_name(f".{output_path.name}.tmp")
    temporary_path.write_text(
        json.dumps(trajectory, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(output_path)


def _model_output_from_belief(belief):
    return {
        "belief_status": belief["belief_status"],
        "confidence": belief["confidence"],
        "explanation": belief["explanation"],
        "evidence_summary": belief["evidence_summary"],
    }


def load_partial_trajectory(partial_path, observations):
    """Load and validate a saved prefix of the frozen demo trajectory."""
    partial_path = Path(partial_path)
    if not partial_path.exists():
        raise ValueError(f"Resume requested but partial trajectory was not found: {partial_path}")
    trajectory = json.loads(partial_path.read_text(encoding="utf-8"))
    if not isinstance(trajectory, list) or len(trajectory) > DEMO_TIMESTEPS:
        raise ValueError("Partial trajectory is not a valid demo prefix")
    for index, belief in enumerate(trajectory):
        if not isinstance(belief, dict) or set(belief) != {
            "timestamp",
            "belief_status",
            "confidence",
            "explanation",
            "evidence_summary",
        }:
            raise ValueError("Partial trajectory contains a malformed belief")
        if belief.get("timestamp") != observations[index]["timestamp"]:
            raise ValueError("Partial trajectory timestamps do not match the demo window")
        validate_model_output(_model_output_from_belief(belief))
    return trajectory


def failure_diagnostics(error, provider_name, timestep, timestamp):
    """Capture the exception chain and available metadata, without request headers."""
    diagnostics = {
        "provider": provider_name,
        "timestep": timestep,
        "timestamp": timestamp,
        "exception_class": type(error).__name__,
        "exception_message": str(error),
        "traceback": "".join(traceback.format_exception(type(error), error, error.__traceback__)),
        "http_status": None,
        "finish_reason": None,
        "token_usage": None,
        "exception_chain": [],
    }
    seen = set()
    current = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        diagnostics["exception_chain"].append({
            "exception_class": type(current).__name__, "message": str(current),
        })
        metadata = {
            "http_status": vars(current).get("http_status"),
            "finish_reason": vars(current).get("finish_reason"),
            "token_usage": vars(current).get("token_usage"),
        }
        if isinstance(current, HTTPError):
            metadata["http_status"] = current.code
        response = vars(current).get("response")
        if isinstance(response, dict):
            metadata["token_usage"] = metadata["token_usage"] or response.get("usage")
            choices = response.get("choices")
            if isinstance(choices, list) and choices and isinstance(choices[0], dict):
                metadata["finish_reason"] = metadata["finish_reason"] or choices[0].get("finish_reason")
        for key, value in metadata.items():
            if diagnostics[key] is None and value is not None:
                try:
                    json.dumps(value, allow_nan=False)
                except (TypeError, ValueError):
                    continue
                diagnostics[key] = value
        current = current.__cause__ or (
            None if current.__suppress_context__ else current.__context__
        )
    return diagnostics


class DemoRunError(RuntimeError):
    """Report a failed demo while retaining its completed checkpoint."""

    def __init__(self, failed_timestep, completed_timesteps, partial_output_path):
        self.failed_timestep = failed_timestep
        self.completed_timesteps = completed_timesteps
        self.partial_output_path = str(partial_output_path)
        self.diagnostics_path = None
        self.diagnostics_write_error = None
        super().__init__(
            f"Demo failed at Day {failed_timestep}; "
            f"completed timesteps: {completed_timesteps}; "
            f"partial output: {partial_output_path}"
        )

    def as_dict(self):
        return {
            "failed_timestep": self.failed_timestep,
            "completed_timestep_count": self.completed_timesteps,
            "partial_output_path": self.partial_output_path,
            "diagnostics_path": self.diagnostics_path,
            "diagnostics_write_error": self.diagnostics_write_error,
        }


def run_demo(
    provider_name,
    market_path=DEFAULT_MARKET_PATH,
    output_path=None,
    provider=None,
    resume=False,
    partial_output_path=None,
):
    """Execute, save, and evaluate one continuous Minimum Demo trajectory."""
    market = pd.read_csv(market_path)
    demo_market, observations = select_demo_window(market)
    selected_provider = provider if provider is not None else create_provider(provider_name)

    destination = Path(output_path) if output_path else (
        RESULTS_DIRECTORY / f"demo_{provider_name}_trajectory.json"
    )
    partial_destination = Path(partial_output_path) if partial_output_path else (
        RESULTS_DIRECTORY / f"demo_{provider_name}_trajectory_partial.json"
    )
    saved_prefix = (
        load_partial_trajectory(partial_destination, observations) if resume else []
    )
    if not resume:
        save_trajectory([], partial_destination)
    replay_count = len(saved_prefix)
    latest_trajectory = []
    call_index = 0

    def replay_then_generate(context):
        nonlocal call_index
        if call_index < replay_count:
            output = _model_output_from_belief(saved_prefix[call_index])
        else:
            output = selected_provider(context)
        call_index += 1
        return output

    def checkpoint(trajectory):
        save_trajectory(trajectory, partial_destination)
        latest_trajectory[:] = trajectory

    try:
        trajectory = run_llm_agent(
            observations,
            replay_then_generate,
            belief_callback=checkpoint,
        )
    except Exception as error:
        completed_timesteps = len(latest_trajectory)
        failure = DemoRunError(
            failed_timestep=START_DAY + completed_timesteps,
            completed_timesteps=completed_timesteps,
            partial_output_path=partial_destination,
        )
        diagnostics_path = partial_destination.with_name(
            f"{partial_destination.stem}_failure.json"
        )
        try:
            diagnostics = failure_diagnostics(
                error, provider_name, failure.failed_timestep,
                observations[completed_timesteps]["timestamp"],
            )
            save_trajectory(diagnostics, diagnostics_path)
            failure.diagnostics_path = str(diagnostics_path)
        except Exception as diagnostics_error:
            # A diagnostics filesystem failure must not replace the original cause.
            failure.diagnostics_write_error = (
                f"{type(diagnostics_error).__name__}: {diagnostics_error}"
            )
        raise failure from error

    save_trajectory(trajectory, destination)
    return {
        "provider": provider_name,
        "start_day": START_DAY,
        "end_day": END_DAY,
        "timesteps": len(trajectory),
        "trajectory_path": str(destination),
        "partial_trajectory_path": str(partial_destination),
        "metrics": evaluate_trajectory(demo_market, trajectory),
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", required=True, choices=("codex", "deepseek", "qwen"))
    parser.add_argument("--market", type=Path, default=DEFAULT_MARKET_PATH)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        report = run_demo(args.provider, args.market, args.output, resume=args.resume)
    except DemoRunError as error:
        print(json.dumps(error.as_dict(), indent=2), file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
