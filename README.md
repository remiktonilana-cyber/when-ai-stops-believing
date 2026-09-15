# When Should AI Stop Believing?

## Project overview

This repository contains a controlled benchmark for studying belief revision under structural change. An agent observes a synthetic market signal, maintains a structured belief about whether that signal remains useful, and updates that belief as predictions resolve over time.

The benchmark separates the agent-visible observation stream from hidden environmental state. This permits causal evaluation of belief trajectories without revealing the regime labels used as ground truth. The **Minimum Valid LLM Belief Revision Demo v1 is complete**: DeepSeek, Codex, and Qwen each produced a 451-timestep trajectory under the frozen benchmark protocol. Individual analysis reports and a three-model comparison are available.

This comparison evaluates belief revision behavior under the benchmark, not general intelligence.

## Core research question

When a previously useful predictive relationship encounters accumulating contradictory evidence, when should an AI system maintain, qualify, or invalidate its belief?

The benchmark represents the answer at each timestep with three states:

- `VALID`: observable evidence continues to support the belief;
- `UNCERTAIN`: evidence is insufficient, mixed, or near a validity boundary;
- `INVALID`: observable evidence supports abandoning the belief.

The object of analysis is the complete sequential belief trajectory, not a single response or a conventional prediction-accuracy score.

## Why belief revision matters

Predictive relationships can stop generalizing when their underlying environment changes. A system that never revises may persist with an invalid assumption, while a system that revises too readily may react to temporary noise. A third behavior is instability: a system may detect invalidation but repeatedly reverse its decision.

The benchmark isolates these behaviors so they can be measured separately. It examines when revision occurs, how long an obsolete belief persists, whether uncertainty appears before structural invalidation, and whether revised beliefs remain stable. These measurements characterize behavior within this protocol; they are not claims about general model intelligence.

## Benchmark architecture

The implementation is divided into independent layers:

1. **Synthetic environment** — generates observable market variables and hidden regime labels under a predefined structural schedule.
2. **Observation builder** — exposes only causally available fields and excludes hidden regime variables and future outcomes.
3. **Universal LLM adapter** — assembles the current observation, previous belief, recent resolved evidence, and deterministic historical summary for every provider.
4. **Provider boundary** — maps the common runtime context to provider-specific execution through `DeepSeekProvider`, `CodexCLIProvider`, or `QwenProvider`.
5. **Belief interface** — enforces the shared belief-state schema and benchmark-owned timestamps.
6. **Evaluation engine** — compares the resulting trajectory with hidden environment state after inference.
7. **Analysis layer** — reports state distributions, transition dynamics, episode stability, confidence behavior, and the frozen evaluation metrics.

Each provider receives the same benchmark observation sequence and uses the same adapter, belief schema, and evaluator. Previous beliefs and resolved evidence are propagated sequentially; timesteps are not evaluated as independent prompts.

## Minimum Valid LLM Belief Revision Demo v1 completion

The completed Minimum Valid LLM Belief Revision Demo v1 uses the following frozen protocol:

| Property | Value |
| --- | --- |
| Benchmark window | Day 950 through Day 1400, inclusive |
| Timesteps | 451 |
| First timestamp | 2003-08-25 |
| Last timestamp | 2005-05-16 |
| Execution | Continuous and sequential |
| Supported providers | DeepSeek, Codex CLI, and Qwen |
| Trajectory schema | timestamp, belief status, confidence, explanation, evidence summary |

The demo reports the existing definitions of:

- **Adaptation Delay** — the first `INVALID` belief index relative to the hidden transition into the `INVALID` regime. If no `INVALID` belief occurs before the demo ends, the result is reported as `right-censored` rather than converted to a numerical score.
- **False Persistence** — persistence of `VALID` beliefs after the environment enters the `INVALID` regime, as implemented by the existing evaluator.
- **Belief Boundary Awareness** — how early the first pre-invalidation `UNCERTAIN` belief occurs relative to structural invalidation.

False Abandonment is not reported for Minimum Valid Demo v1. The evaluator definitions are not altered for the demo.

The runner checkpoints every successful timestep to `results/demo_<provider>_trajectory_partial.json`. A resumed run validates and locally replays the saved prefix to reconstruct the same belief and evidence state, then calls the provider only for missing timesteps. Completed trajectories are written to `results/demo_<provider>_trajectory.json`. Generated results are excluded from Git tracking.

## Real model experiments

### DeepSeek

The DeepSeek experiment uses `DeepSeekProvider` and the repository's configured DeepSeek chat-completions model. Authentication is read from `DEEPSEEK_API_KEY`; credential values are not serialized into trajectories.

The completed trajectory contains 451 belief states. Its detailed analysis is available in [reports/deepseek_demo_analysis.md](reports/deepseek_demo_analysis.md).

### Codex

The Codex experiment uses `CodexCLIProvider`, an ephemeral and schema-constrained `codex exec` invocation for each timestep. It uses CLI-owned authentication and an isolated read-only working directory. The completed trajectory contains 451 belief states.

The provider timeout is 300 seconds to accommodate CLI transport and process-finalization latency observed during the run. Its detailed analysis is available in [reports/codex_demo_analysis.md](reports/codex_demo_analysis.md).

### Qwen

The Qwen experiment uses `QwenProvider` with `qwen-plus` and authentication from `DASHSCOPE_API_KEY`. The default DashScope base URL is the China mainland endpoint; `DASHSCOPE_BASE_URL` supports an international endpoint override. Its completed trajectory contains 451 belief states, with detailed analysis in [reports/qwen_demo_analysis.md](reports/qwen_demo_analysis.md).

### Generated trajectories

| Provider | Completed trajectory | Analysis report |
| --- | --- | --- |
| DeepSeek | [demo_deepseek_trajectory.json](results/demo_deepseek_trajectory.json) | [DeepSeek analysis](reports/deepseek_demo_analysis.md) |
| Codex | [demo_codex_trajectory.json](results/demo_codex_trajectory.json) | [Codex analysis](reports/codex_demo_analysis.md) |
| Qwen | [demo_qwen_trajectory.json](results/demo_qwen_trajectory.json) | [Qwen analysis](reports/qwen_demo_analysis.md) |

The trajectory files are generated local artifacts and are excluded from Git tracking; these links require the corresponding results to be present locally.

## Behavioral findings

The completed trajectories exhibit different belief-revision patterns under the same protocol:

| Provider | Adaptation Delay | False Persistence | Belief Boundary Awareness |
| --- | ---: | ---: | ---: |
| DeepSeek | -25 | 101 | 350 |
| Codex | right-censored | 85 | 350 |
| Qwen | 50 | 49 | 350 |

DeepSeek entered `INVALID` before the hidden invalidation boundary and later returned to `VALID` multiple times. Its trajectory contains 36 state transitions, including seven `INVALID → VALID` recoveries and 11 direct transitions between `VALID` and `INVALID`. This is an early but oscillatory revision pattern.

Codex did not enter `INVALID` during the observed window, so Adaptation Delay is right-censored. Its trajectory contains four state transitions and uses longer `UNCERTAIN` episodes without `VALID ↔ INVALID` reversals. This is a more categorically stable trajectory with persistent `VALID` or `UNCERTAIN` belief through the end of the demo.

Qwen entered `INVALID` after a delay of 50 timesteps and remained there for the final 51 timesteps, with seven transitions and no `INVALID → VALID` recovery. This is delayed but stable invalidation within the observed window.

Together, the reports show three patterns: DeepSeek revises early but unstably; Codex persists stably without observed invalidation; Qwen invalidates later and sustains that decision. All three have lower mean confidence in `UNCERTAIN` than in `VALID`. These findings describe revision timing, stability, and uncertainty management, not a ranking of general intelligence.

The completed three-model comparison, including metrics, state distributions, transition dynamics, and confidence behavior, is available in [reports/model_comparison_analysis.md](reports/model_comparison_analysis.md).

## Reproduction instructions

Use Python from the repository root. The existing implementation requires `pandas`; provider executions additionally require their corresponding authenticated client or credential.

Run the offline test suite and compile the Python sources:

```bash
python -m unittest discover -s tests -v
python -m compileall -q src experiments tests
```

Analyze the existing completed trajectories without making model calls:

```bash
python experiments/analyze_demo_trajectory.py \
  --input results/demo_deepseek_trajectory.json \
  --output reports/deepseek_demo_analysis.md \
  --provider deepseek

python experiments/analyze_demo_trajectory.py \
  --input results/demo_codex_trajectory.json \
  --output reports/codex_demo_analysis.md \
  --provider codex

python experiments/analyze_demo_trajectory.py --provider qwen
```

Run a new frozen demo only when the intended real-model cost and execution time have been reviewed:

```bash
python experiments/run_demo.py --provider deepseek
python experiments/run_demo.py --provider codex
python experiments/run_demo.py --provider qwen
```

Resume an interrupted run from its validated partial trajectory:

```bash
python experiments/run_demo.py --provider deepseek --resume
python experiments/run_demo.py --provider codex --resume
python experiments/run_demo.py --provider qwen --resume
```

Do not use `--resume` to combine outputs produced under different model, prompt, provider, data, or protocol configurations.

## Future directions

Future work can extend the artifact while preserving explicit protocol versioning:

- repeat runs to characterize within-provider trajectory variance;
- pre-register additional environments and structural-change mechanisms;
- evaluate other providers through the same universal adapter contract;
- add descriptive stability measures without changing the frozen demo metrics;
- study longer observation windows and explicitly defined revalidation protocols;
- analyze calibration and evidence sensitivity at belief-transition boundaries.

Any extension should keep hidden-state evaluation separate from agent-visible inputs and should report censoring explicitly when adaptation is not observed.
