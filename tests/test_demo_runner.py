"""Deterministic validation for the frozen Minimum Demo runner."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from experiments.run_demo import DemoRunError, END_DAY, START_DAY, run_demo
from src.belief_interface import validate_belief_state
from src.evaluation_engine import load_belief_history


class DeterministicFakeProvider:
    def __init__(self):
        self.contexts = []

    def __call__(self, context):
        self.contexts.append(deepcopy(context))
        timestep = len(self.contexts) - 1
        if timestep < 340:
            status = "VALID"
        elif timestep < 355:
            status = "UNCERTAIN"
        else:
            status = "INVALID"
        return {
            "belief_status": status,
            "confidence": 0.8,
            "explanation": "Deterministic Minimum Demo test response.",
            "evidence_summary": {
                "supporting_evidence": [],
                "contradicting_evidence": [],
            },
        }


class DemoRunnerTests(unittest.TestCase):
    def test_complete_fake_provider_demo(self):
        provider = DeterministicFakeProvider()
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "trajectory.json"
            partial_path = Path(directory) / "trajectory_partial.json"
            report = run_demo(
                "fake",
                output_path=output_path,
                partial_output_path=partial_path,
                provider=provider,
            )
            trajectory = json.loads(output_path.read_text(encoding="utf-8"))
            partial_trajectory = json.loads(partial_path.read_text(encoding="utf-8"))
            evaluator_history = load_belief_history(output_path)

        market = pd.read_csv("data/synthetic_market.csv")
        self.assertEqual(report["start_day"], START_DAY)
        self.assertEqual(report["end_day"], END_DAY)
        self.assertEqual(report["timesteps"], 451)
        self.assertEqual(len(provider.contexts), 451)
        self.assertEqual(len(trajectory), 451)
        self.assertEqual(partial_trajectory, trajectory)
        self.assertEqual(len(evaluator_history), 451)
        self.assertEqual(evaluator_history.iloc[0]["belief_status"], "VALID")
        self.assertEqual(trajectory[0]["timestamp"], market.iloc[START_DAY]["date"])
        self.assertEqual(trajectory[-1]["timestamp"], market.iloc[END_DAY]["date"])

        self.assertIsNone(provider.contexts[0]["previous_belief_state"])
        for index in range(1, len(trajectory)):
            self.assertEqual(
                provider.contexts[index]["previous_belief_state"],
                trajectory[index - 1],
            )
        self.assertEqual(provider.contexts[0]["recent_resolved_evidence"], [])
        self.assertEqual(
            provider.contexts[-1]["historical_evidence_summary"]["resolved_count"],
            450,
        )

        self.assertTrue(all(validate_belief_state(belief) for belief in trajectory))
        self.assertEqual(
            set(report["metrics"]),
            {
                "adaptation_delay",
                "false_persistence",
                "belief_boundary_awareness",
            },
        )
        self.assertEqual(report["metrics"]["adaptation_delay"], 5)
        self.assertEqual(report["metrics"]["false_persistence"], 0)
        self.assertEqual(report["metrics"]["belief_boundary_awareness"], 10)

    def test_unobserved_adaptation_is_right_censored(self):
        class AlwaysValidProvider(DeterministicFakeProvider):
            def __call__(self, context):
                output = super().__call__(context)
                output["belief_status"] = "VALID"
                return output

        with tempfile.TemporaryDirectory() as directory:
            report = run_demo(
                "fake",
                output_path=Path(directory) / "trajectory.json",
                partial_output_path=Path(directory) / "trajectory_partial.json",
                provider=AlwaysValidProvider(),
            )

        self.assertEqual(report["metrics"]["adaptation_delay"], "right-censored")

    def test_failure_checkpoint_and_resume(self):
        class FailingProvider(DeterministicFakeProvider):
            def __call__(self, context):
                if len(self.contexts) == 12:
                    raise RuntimeError("deterministic failure")
                return super().__call__(context)

        class ResumeProvider(DeterministicFakeProvider):
            pass

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "trajectory.json"
            partial_path = Path(directory) / "trajectory_partial.json"
            with self.assertRaises(DemoRunError) as raised:
                run_demo(
                    "fake",
                    output_path=output_path,
                    partial_output_path=partial_path,
                    provider=FailingProvider(),
                )

            failure = raised.exception
            checkpoint = json.loads(partial_path.read_text(encoding="utf-8"))
            self.assertEqual(failure.failed_timestep, START_DAY + 12)
            self.assertEqual(failure.completed_timesteps, 12)
            self.assertEqual(failure.partial_output_path, str(partial_path))
            self.assertEqual(len(checkpoint), 12)
            self.assertFalse(output_path.exists())

            resume_provider = ResumeProvider()
            report = run_demo(
                "fake",
                output_path=output_path,
                partial_output_path=partial_path,
                provider=resume_provider,
                resume=True,
            )
            final_trajectory = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(len(resume_provider.contexts), 451 - 12)
        self.assertEqual(final_trajectory[:12], checkpoint)
        self.assertEqual(len(final_trajectory), 451)
        self.assertEqual(report["timesteps"], 451)
        self.assertEqual(
            len({belief["timestamp"] for belief in final_trajectory}),
            451,
        )


if __name__ == "__main__":
    unittest.main()
