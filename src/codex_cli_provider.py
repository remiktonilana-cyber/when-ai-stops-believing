"""Codex CLI provider for the universal LLM runtime."""

import json
import subprocess
import tempfile
from pathlib import Path

from src.llm_prompt import SYSTEM_INSTRUCTIONS, serialize_runtime_context


BELIEF_OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "belief_status",
        "confidence",
        "explanation",
        "evidence_summary",
    ],
    "properties": {
        "belief_status": {
            "type": "string",
            "enum": ["VALID", "UNCERTAIN", "INVALID"],
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "explanation": {"type": "string"},
        "evidence_summary": {
            "type": "object",
            "additionalProperties": False,
            "required": ["supporting_evidence", "contradicting_evidence"],
            "properties": {
                "supporting_evidence": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "contradicting_evidence": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        },
    },
}


def _run_codex(command, prompt, timeout):
    """Run one isolated Codex CLI turn using CLI-owned authentication."""
    try:
        completed = subprocess.run(
            command,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as error:
        raise RuntimeError("Codex CLI executable was not found") from error
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("Codex CLI invocation timed out") from error

    if completed.returncode != 0:
        detail = completed.stderr.strip().splitlines()
        suffix = f": {detail[-1]}" if detail else ""
        raise RuntimeError(f"Codex CLI invocation failed{suffix}")
    return completed.stdout


class CodexCLIProvider:
    """Map one assembled benchmark context through an ephemeral Codex turn."""

    def __init__(self, executable="codex", timeout=300, runner=None):
        self.executable = executable
        self.timeout = timeout
        self.runner = runner or _run_codex

    def __call__(self, context):
        prompt = (
            f"{SYSTEM_INSTRUCTIONS}\n\n"
            "Do not use tools, files, environment state, or prior conversation. "
            "The JSON object below is your complete benchmark information set.\n\n"
            f"{serialize_runtime_context(context)}"
        )

        with tempfile.TemporaryDirectory(prefix="codex-belief-") as directory:
            working_directory = Path(directory)
            schema_path = working_directory / "belief-output-schema.json"
            schema_path.write_text(
                json.dumps(BELIEF_OUTPUT_SCHEMA),
                encoding="utf-8",
            )
            command = [
                self.executable,
                "exec",
                "--ephemeral",
                "--sandbox",
                "read-only",
                "--ignore-user-config",
                "--ignore-rules",
                "--skip-git-repo-check",
                "--cd",
                str(working_directory),
                "--output-schema",
                str(schema_path),
                "-",
            ]
            output = self.runner(command, prompt, self.timeout)

        try:
            model_output = json.loads(output)
        except (TypeError, json.JSONDecodeError) as error:
            raise ValueError("Codex CLI structured output was not valid JSON") from error
        if not isinstance(model_output, dict):
            raise ValueError("Codex CLI structured output must be an object")
        return model_output
