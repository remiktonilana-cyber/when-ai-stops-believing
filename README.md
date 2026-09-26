# When AI Stops Believing

Belief revision, reliability monitoring, and decision authorization for AI systems operating in changing environments.

As AI systems move from producing information toward influencing decisions and actions, their outputs need more than a prediction check. A model can continue producing coherent, confident outputs after the environment in which its belief was useful has changed.

This repository investigates that reliability boundary through controlled research and prototypes a **Decision Gate** that separates AI output from permission to act.

## The problem

| Question | Concern |
| --- | --- |
| “What does the model predict?” | Prediction |
| “Should the underlying belief still be trusted under current conditions?” | Reliability |
| “Should this output be allowed to affect the real system?” | Authorization |

These are different problems: **Intelligence ≠ Reliability. Prediction ≠ Authorization.** A useful prediction does not, by itself, establish that execution is appropriate in the current operating context.

## What exists today

| Component | Status | Role |
| --- | --- | --- |
| LAI / belief-revision research | Research evidence | Studies belief persistence and revision under controlled synthetic transitions. |
| Reliability Adapter | Implemented prototype | Translates supplied reliability information into the gate contract. |
| Decision Gate | Implemented prototype | Produces deterministic GREEN / YELLOW / RED authorization decisions. |
| Urban Traffic Demo | Scripted demonstration | Shows the same proposal and belief receiving different permissions as operational conditions change. |
| Critical Transition Detection | Future research | Asks whether approaching regime changes can be detected before existing beliefs visibly fail. No operational monitor is implemented. |

See the [documentation status map](docs/README.md) for implementation and research references.

## Architecture

![Current research and authorization architecture, with future research separated](docs/assets/architecture.svg)

LAI research evaluates belief behavior under specified protocols. The **Reliability Adapter translates supplied information**; it does not independently infer real-world reliability. Application context—such as data freshness, system health, consequence, and reversibility—enters separately.

The **Decision Gate** applies deterministic prototype policy to permit execution, require review, or block execution. It is not a calibrated probability-of-safety model. Execution and enforcement remain separate application responsibilities. Hidden benchmark truth and retrospective evaluation metrics are not runtime gate inputs.

Read the [current architecture](docs/current_architecture.md) for contracts and boundaries. The future monitor shown separately in the diagram is not part of the current runtime.

## See the demo

**Same AI proposal. Same belief. Different reality. Different permission.**

![Three synthetic scenarios with the same belief: GREEN executes, YELLOW holds, and RED blocks](docs/assets/urban-traffic-demo.png)

| Scenario | Permission | Execution result |
| --- | --- | --- |
| Normal | GREEN | EXECUTED |
| Environment shift | YELLOW | HELD |
| Operational failure | RED | BLOCKED |

The belief information alone does not determine whether an action should be authorized. An explicit context shift causes a hold; an unhealthy controller blocks execution even with the same VALID belief.

This is a **synthetic scenario with scripted belief input and simulated execution**, with no live traffic control. It demonstrates authorization behavior, not traffic optimization or real-city safety. Traffic is an application example, not the core research problem.

[Run and inspect the Urban Traffic demo](applications/urban_traffic/README.md).

## Research foundation

**When an environment changes, can an AI agent appropriately revise a previously supported belief?**

Controlled synthetic transition experiments provide known environmental ground truth while keeping hidden variables outside the [agent observation contract](docs/lai_agent_contract.md).

The later LAI paired-transition experiments recorded cases where agents continued to output VALID beliefs after the benchmark evidence reference for structural change. Belief changes also occurred in controls without the structural transition. A single belief switch is therefore insufficient evidence of reliable adaptation in these experiments. The reference time is an evaluation benchmark, not a uniquely correct revision time.

These are observations under the repository's protocols, not universal model behavior or rankings. Read the [frozen transition specification](reports/lai_agent_transition_specification.md), [canonical transition audit](reports/lai_canonical_transition_audit.md), and recorded [Qwen](reports/lai_qwen_paired_analysis.md) and [DeepSeek](reports/lai_deepseek_paired_analysis.md) paired analyses.

The **earlier synthetic-market benchmark** is a separate research track with its own [protocol](docs/benchmark_protocol.md), [evaluation design](docs/evaluation_engine_design.md), and [recorded analysis](reports/model_comparison_analysis.md). Its metrics should not be merged with the later paired-transition findings. The [research index](docs/README.md#two-distinct-research-tracks) connects both tracks and their provenance.

## Decision Gate

The gate asks a different question from the model:

> Given the available reliability information, operating context, system health, and decision impact, what level of execution permission is appropriate?

| Permission | Meaning under prototype policy |
| --- | --- |
| GREEN | Automatic execution permitted. |
| YELLOW | Hold; human confirmation required. The demo does not implement an approval workflow. |
| RED | Block or hold execution; ordinary human confirmation cannot bypass the block. |

**VALID does not automatically imply GREEN. Confidence alone does not determine permission.** Confidence describes certainty in the belief status, not probability of successful execution. Missing required information does not become favorable input, and hard operational blocks override favorable signals.

See the [policy](docs/decision_gate_prototype.md), [integration contract](docs/decision_gate/lai_integration.md), [gate implementation](src/decision_gate.py), and [reliability adapter](src/reliability_adapter.py).

## Run locally

From the repository root, generate the offline demo:

```sh
python -m applications.urban_traffic.run_demo --output-dir /tmp/urban-traffic-demo
```

Open the generated `index.html`; `demo_results.json` contains the corresponding records. This demo requires no model or API calls.

Run the tests in an environment with pytest and the repository's scientific dependencies available:

```sh
python -m pytest -q
```

Provider-backed research runs are separate from this quick start. Start with the [research documentation](docs/README.md) and the preserved instructions below. Generated research trajectories are generally ignored local artifacts; tracked reports are the public evidence entry points.

<details>
<summary>Earlier synthetic-market benchmark: reproduction instructions</summary>

These instructions retain the scope of Minimum Valid LLM Belief Revision Demo v1: Days 950–1400, 451 sequential timesteps. They do not run the later LAI paired-transition protocol. Consult the [benchmark protocol](docs/benchmark_protocol.md), [implementation specification](docs/implementation_plan.md), and recorded [DeepSeek](reports/deepseek_demo_analysis.md), [Codex](reports/codex_demo_analysis.md), and [Qwen](reports/qwen_demo_analysis.md) analyses.

Use Python from the repository root. The original runner requires pandas; provider execution additionally requires the relevant authenticated client or credentials. Offline checks from the original instructions:

```sh
python -m unittest discover -s tests -v
python -m compileall -q src experiments tests
```

Analyze existing local trajectories without model calls:

```sh
python experiments/analyze_demo_trajectory.py --input results/demo_deepseek_trajectory.json --output reports/deepseek_demo_analysis.md --provider deepseek
python experiments/analyze_demo_trajectory.py --input results/demo_codex_trajectory.json --output reports/codex_demo_analysis.md --provider codex
python experiments/analyze_demo_trajectory.py --provider qwen
```

These historical analysis commands require the saved trajectories and regenerate their report destinations; they are not read-only viewing commands. Raw trajectories are not supplied by the report links.

The [original runner](experiments/run_demo.py) supports provider-backed execution and validated checkpoint resume:

```sh
python experiments/run_demo.py --provider deepseek
python experiments/run_demo.py --provider codex
python experiments/run_demo.py --provider qwen

python experiments/run_demo.py --provider deepseek --resume
python experiments/run_demo.py --provider codex --resume
python experiments/run_demo.py --provider qwen --resume
```

These commands invoke providers and are not part of the offline demo. Review model access and execution cost before running them. Do not combine checkpoints from different model, prompt, provider, data, or protocol configurations. Completed trajectories use `results/demo_<provider>_trajectory.json`; partial checkpoints use the corresponding `_partial.json` name.

</details>

## Repository and documentation map

Start at the [documentation index](docs/README.md), which distinguishes current interfaces from historical plans and frozen specifications.

| Directory | Contents |
| --- | --- |
| [src/](src/) | Research components, providers, reliability adapter, and Decision Gate. |
| [reports/](reports/) | Recorded analyses, calibration findings, and frozen research specifications. |
| [docs/](docs/) | Current navigation, architecture, contracts, and historical design documents. |
| [applications/urban_traffic/](applications/urban_traffic/) | Scripted application demonstration and offline report renderer. |
| [tests/](tests/) | Contract, policy, application, and research regression tests. |

## Scope and limitations

The repository currently demonstrates controlled belief-revision research, reliability-information translation, deterministic authorization logic, and a synthetic application example.

It does **not** demonstrate production safety certification, calibrated probability of safe action, autonomous detection of real-world critical transitions, live urban infrastructure control, or universal AI reliability measurement.

## Future: before AI stops believing

**What if the system could recognize that an existing belief is becoming fragile before that belief clearly fails?**

Current question: environment changes → evidence accumulates → belief should revise.

Future research question: latent system state changes → transition proximity may increase → old relationships may become fragile → execution authority may need to decrease before obvious failure.

The [roadmap](docs/roadmap.md) explores latent internal state, nonlinear shock-response amplification, transition proximity, and possible critical-transition early-warning signals. These are research directions, not implemented or universally predictive capabilities. No operational critical threshold has been established by this repository.
