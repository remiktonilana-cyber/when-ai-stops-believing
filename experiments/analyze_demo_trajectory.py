"""Analyze an existing Minimum Demo belief trajectory without model calls."""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from experiments.run_demo import END_DAY, START_DAY, evaluate_trajectory
from src.universal_llm_adapter import validate_model_output


DEFAULT_INPUT_PATH = REPOSITORY_ROOT / "results" / "demo_deepseek_trajectory.json"
DEFAULT_OUTPUT_PATH = REPOSITORY_ROOT / "reports" / "deepseek_demo_analysis.md"
DEFAULT_MARKET_PATH = REPOSITORY_ROOT / "data" / "synthetic_market.csv"
BELIEF_STATUSES = ("VALID", "UNCERTAIN", "INVALID")


def _model_output_from_belief(belief):
    return {
        "belief_status": belief["belief_status"],
        "confidence": belief["confidence"],
        "explanation": belief["explanation"],
        "evidence_summary": belief["evidence_summary"],
    }


def load_trajectory(path):
    """Load and validate the stored benchmark-owned belief states."""
    trajectory = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(trajectory, list) or not trajectory:
        raise ValueError("Trajectory must be a non-empty JSON array")
    expected_fields = {
        "timestamp",
        "belief_status",
        "confidence",
        "explanation",
        "evidence_summary",
    }
    for belief in trajectory:
        if not isinstance(belief, dict) or set(belief) != expected_fields:
            raise ValueError("Trajectory contains a malformed belief state")
        validate_model_output(_model_output_from_belief(belief))
    return trajectory


def identify_transitions(trajectory):
    transitions = []
    for index in range(1, len(trajectory)):
        previous = trajectory[index - 1]["belief_status"]
        current = trajectory[index]["belief_status"]
        if current != previous:
            transitions.append(
                {
                    "index": index,
                    "timestamp": trajectory[index]["timestamp"],
                    "from": previous,
                    "to": current,
                }
            )
    return transitions


def state_episode_durations(trajectory):
    durations = defaultdict(list)
    current_status = trajectory[0]["belief_status"]
    current_duration = 1
    for belief in trajectory[1:]:
        status = belief["belief_status"]
        if status == current_status:
            current_duration += 1
        else:
            durations[current_status].append(current_duration)
            current_status = status
            current_duration = 1
    durations[current_status].append(current_duration)
    return durations


def analyze_trajectory(trajectory, market, provider):
    counts = Counter(belief["belief_status"] for belief in trajectory)
    transitions = identify_transitions(trajectory)
    episodes = state_episode_durations(trajectory)
    confidence_by_status = {
        status: [
            float(belief["confidence"])
            for belief in trajectory
            if belief["belief_status"] == status
        ]
        for status in BELIEF_STATUSES
    }
    direct_reversals = [
        transition
        for transition in transitions
        if {transition["from"], transition["to"]} == {"VALID", "INVALID"}
    ]
    recoveries = [
        transition
        for transition in transitions
        if transition["from"] == "INVALID" and transition["to"] == "VALID"
    ]
    demo_market = market.iloc[START_DAY : END_DAY + 1].reset_index(drop=True)
    metrics = evaluate_trajectory(demo_market, trajectory)
    return {
        "provider": provider,
        "length": len(trajectory),
        "first_timestamp": trajectory[0]["timestamp"],
        "last_timestamp": trajectory[-1]["timestamp"],
        "counts": counts,
        "transitions": transitions,
        "episodes": episodes,
        "confidence_by_status": confidence_by_status,
        "direct_reversal_count": len(direct_reversals),
        "recovery_count": len(recoveries),
        "metrics": metrics,
    }


def _format_metric(value):
    return "not observed" if value is None else str(value)


def render_markdown(analysis):
    length = analysis["length"]
    lines = [
        f"# {analysis['provider'].title()} Minimum Demo Trajectory Analysis",
        "",
        "## Basic information",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Provider | {analysis['provider']} |",
        f"| Trajectory length | {length} |",
        f"| First timestamp | {analysis['first_timestamp']} |",
        f"| Last timestamp | {analysis['last_timestamp']} |",
        "",
        "## Belief state statistics",
        "",
        "| Belief status | Count | Percentage |",
        "| --- | ---: | ---: |",
    ]
    for status in BELIEF_STATUSES:
        count = analysis["counts"][status]
        lines.append(f"| {status} | {count} | {count / length * 100:.2f}% |")

    lines.extend(
        [
            "",
            "## Transition analysis",
            "",
            f"Transition count: **{len(analysis['transitions'])}**",
            "",
            "| # | Timestamp | Transition |",
            "| ---:| ---|---|",
        ]
    )
    for number, transition in enumerate(analysis["transitions"], start=1):
        lines.append(
            f"| {number} | {transition['timestamp']} | "
            f"{transition['from']} → {transition['to']} |"
        )

    lines.extend(
        [
            "",
            "## Belief oscillation analysis",
            "",
            "A reversal is counted here only when VALID and INVALID are adjacent "
            "episodes, without an intervening UNCERTAIN state.",
            "",
            f"- Direct VALID ↔ INVALID reversals: "
            f"**{analysis['direct_reversal_count']}**",
            f"- INVALID → VALID recoveries: **{analysis['recovery_count']}**",
            "",
            "| Belief status | Episode count | Average episode duration (timesteps) |",
            "| --- | ---: | ---: |",
        ]
    )
    for status in BELIEF_STATUSES:
        durations = analysis["episodes"].get(status, [])
        average = sum(durations) / len(durations) if durations else 0.0
        lines.append(f"| {status} | {len(durations)} | {average:.2f} |")

    lines.extend(
        [
            "",
            "## Confidence analysis",
            "",
            "| Belief status | Mean confidence | Confidence range |",
            "| --- | ---: | ---: |",
        ]
    )
    for status in BELIEF_STATUSES:
        values = analysis["confidence_by_status"][status]
        if values:
            lines.append(
                f"| {status} | {sum(values) / len(values):.4f} | "
                f"{min(values):.4f}–{max(values):.4f} |"
            )
        else:
            lines.append(f"| {status} | n/a | n/a |")

    metrics = analysis["metrics"]
    lines.extend(
        [
            "",
            "## Existing demo metrics",
            "",
            "These values use the existing evaluation engine definitions without modification.",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
            f"| Adaptation Delay | {_format_metric(metrics['adaptation_delay'])} |",
            f"| False Persistence | {_format_metric(metrics['false_persistence'])} |",
            "| Belief Boundary Awareness | "
            f"{_format_metric(metrics['belief_boundary_awareness'])} |",
            "",
            "## Interpretation",
            "",
            "Invalidation detection and oscillatory belief revision describe different behavior "
            "dimensions. Adaptation Delay records when INVALID is first reached relative "
            "to structural invalidation, while repeated reversals and recoveries describe the "
            "stability of the trajectory around that decision. A trajectory may detect "
            "invalidation yet continue alternating between incompatible belief states, or remain "
            "stable without detecting invalidation. These observations compare belief-revision "
            "stability, not overall model intelligence.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--market", type=Path, default=DEFAULT_MARKET_PATH)
    parser.add_argument("--provider", default="deepseek", choices=("deepseek", "codex", "qwen"))
    args = parser.parse_args(argv)
    if args.input is None:
        args.input = REPOSITORY_ROOT / "results" / f"demo_{args.provider}_trajectory.json"
    if args.output is None:
        args.output = REPOSITORY_ROOT / "reports" / f"{args.provider}_demo_analysis.md"
    return args


def main(argv=None):
    args = parse_args(argv)
    trajectory = load_trajectory(args.input)
    market = pd.read_csv(args.market)
    analysis = analyze_trajectory(trajectory, market, args.provider)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(analysis), encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
