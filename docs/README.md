# Current documentation index

This index describes the repository as of 2026-09-27. It distinguishes recorded
research from executable prototypes, scripted demonstrations, and future work.
The [root README](../README.md) is the current public entry point for the reliability
problem, research foundation, implemented prototypes, application demo, limitations,
and future research. This index provides detailed navigation and historical context.

## Status map

| Category | Component | Status and evidence |
| --- | --- | --- |
| Research evidence | Earlier synthetic-market belief-revision benchmark | Recorded trajectories and analyses under its own [benchmark protocol](benchmark_protocol.md); see the [original comparison](../reports/model_comparison_analysis.md), which is not a general model ranking. |
| Research evidence | LAI synthetic system and transition studies | [System-layer experiment](../reports/lai_system_experiment_a.md), [frozen transition specification](../reports/lai_agent_transition_specification.md), and [canonical transition audit](../reports/lai_canonical_transition_audit.md). Conclusions are bounded by their synthetic designs. |
| Research evidence | Later LAI paired-transition agent research | Recorded [Qwen](../reports/lai_qwen_paired_analysis.md) and [DeepSeek](../reports/lai_deepseek_paired_analysis.md) analyses under a shared causal contract; no universal model-behavior claim. |
| Implemented prototype | Reliability Adapter | [Translation contract](decision_gate/lai_integration.md), [source](../src/reliability_adapter.py), and [tests](../tests/test_reliability_adapter.py). Translates supplied information; does not infer real-world reliability. |
| Implemented prototype | Universal Decision Gate | [Policy documentation](decision_gate_prototype.md), [source](../src/decision_gate.py), and [tests](../tests/test_decision_gate.py). Deterministic GREEN/YELLOW/RED authorization assessment. |
| Scripted demonstration | Urban Traffic Decision Gate | [Application guide](../applications/urban_traffic/README.md) and [integration tests](../tests/test_urban_traffic_demo.py). Exactly three offline fixtures; simulated configuration changes only. |
| Future research | Critical Transition Detection / Early Warning | [Roadmap](roadmap.md). A general operational monitor is not implemented or validated today. Existing synthetic transition studies are foundations, not a deployed detector. |

## Navigation by reader intent

- **Understand the research:** Start with the two research tracks below and the
  [LAI information contract](lai_agent_contract.md).
- **Understand the architecture:** Read [current architecture](current_architecture.md)
  and its [diagram](assets/architecture.svg).
- **Inspect the Decision Gate:** Read the [prototype policy](decision_gate_prototype.md)
  and [LAI integration contract](decision_gate/lai_integration.md).
- **Run the demo:** Follow the [application guide](../applications/urban_traffic/README.md).
  It uses scripted inputs without model or API calls.
- **Reproduce research:** Consult the original [benchmark instructions](../README.md),
  the frozen specifications and report provenance below. Distinguish offline
  analysis from provider-backed experiments, which require separate credentials
  and model calls. This documentation task does not run them.
- **Explore future work:** Read the [research roadmap](roadmap.md).

## Two distinct research tracks

The earlier synthetic-market benchmark studies belief revision about a predictive
relationship. Its [market design](synthetic_market_design.md),
[belief design](belief_state_design.md), and [evaluation design](evaluation_engine_design.md)
provide protocol-specific context. Recorded analyses cover
[DeepSeek](../reports/deepseek_demo_analysis.md), [Codex](../reports/codex_demo_analysis.md),
and [Qwen](../reports/qwen_demo_analysis.md).

The later LAI paired-transition research uses synthetic shock-response transition
and matched-control worlds. Read the [frozen specification](../reports/lai_agent_transition_specification.md),
[causal contract](lai_agent_contract.md), [Qwen paired analysis](../reports/lai_qwen_paired_analysis.md),
and [DeepSeek paired analysis](../reports/lai_deepseek_paired_analysis.md).
The [system calibration](../reports/lai_calibration_analysis.md) and
[transition calibration](../reports/lai_transition_calibration_analysis.md) document
separate design checks. Do not merge metrics across these research tracks.

Most generated trajectories under `results/` are local, ignored artifacts rather
than files available in a fresh clone. Tracked reports provide public evidence
and execution provenance; they do not imply that all raw outputs are distributed.
The demo's HTML/JSON are also generated locally in a user-selected directory.

## Historical documents and scope

Keep these documents at their original paths. Their time-local statements are
not the current repository status map:

| Document | How to read it |
| --- | --- |
| [Project architecture](project_architecture.md) | Historical architectural intent. Its “Next” and “Future” milestones predate current implementations. |
| [Research protocol](research_protocol.md) | Early research framing, including proposed real-market validation and earlier output terminology; not the current gate contract. |
| [Implementation plan](implementation_plan.md) | Historical, detailed synthetic-market implementation specification, including frozen definitions; not a project-wide current roadmap. |
| [LAI transition specification](../reports/lai_agent_transition_specification.md) | Frozen experiment design and contemporaneous provenance; later analyses document subsequent runs. |

Historical labels do not invalidate frozen definitions. Use each experiment's own
specification and report together. No existing document or scientific artifact is
renamed, moved, or rewritten by this documentation layer.
