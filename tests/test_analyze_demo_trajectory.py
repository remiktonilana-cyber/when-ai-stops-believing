"""Offline checks for provider-specific analysis paths."""

from pathlib import Path
import unittest

from experiments.analyze_demo_trajectory import (
    DEFAULT_INPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    REPOSITORY_ROOT,
    parse_args,
)


class AnalysisPathTests(unittest.TestCase):
    def test_default_remains_deepseek(self):
        args = parse_args([])
        self.assertEqual(args.provider, "deepseek")
        self.assertEqual(args.input, DEFAULT_INPUT_PATH)
        self.assertEqual(args.output, DEFAULT_OUTPUT_PATH)

    def test_provider_defaults_and_independent_overrides(self):
        for provider in ("deepseek", "codex", "qwen"):
            for override_input, override_output in ((False, False), (True, False), (False, True), (True, True)):
                with self.subTest(provider=provider, input=override_input, output=override_output):
                    argv = ["--provider", provider]
                    if override_input:
                        argv += ["--input", "custom/trajectory.json"]
                    if override_output:
                        argv += ["--output", "custom/analysis.md"]
                    args = parse_args(argv)
                    self.assertEqual(
                        args.input,
                        Path("custom/trajectory.json") if override_input else
                        REPOSITORY_ROOT / "results" / f"demo_{provider}_trajectory.json",
                    )
                    self.assertEqual(
                        args.output,
                        Path("custom/analysis.md") if override_output else
                        REPOSITORY_ROOT / "reports" / f"{provider}_demo_analysis.md",
                    )


if __name__ == "__main__":
    unittest.main()
