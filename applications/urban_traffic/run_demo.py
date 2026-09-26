"""Run with python -m applications.urban_traffic.run_demo --output-dir PATH."""

import argparse
import json
from pathlib import Path

from applications.urban_traffic.fixtures import scenarios
from applications.urban_traffic.simulator import run_scenario
from applications.urban_traffic.visualization import render_report


def run_demo(output_dir):
    results = [run_scenario(scenario) for scenario in scenarios()]
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "demo_results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    (output / "index.html").write_text(render_report(results), encoding="utf-8")
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    for result in run_demo(args.output_dir):
        print(f"{result['scenario']}: {result['decision']['permission']} / {result['execution_result']}")


if __name__ == "__main__":
    main()
