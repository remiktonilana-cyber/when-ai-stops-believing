# Research roadmap: transition proximity and operational boundaries

## Central future question

> When is a system approaching a transition, and where is the operational
> boundary at which an existing belief becomes fragile?

**Current question:** When the underlying relationship changes, can an AI system
revise an existing belief appropriately?

**Future question:** Can observable pre-transition signals indicate that the
system is approaching a regime change before the old belief has clearly failed?

The repository already contains [synthetic transition research](../reports/lai_agent_transition_specification.md)
and [recorded agent analyses](README.md). The future objective is broader:
validate an operational transition/early-warning monitor and its information
contract. That module is not implemented today. The existing reliability adapter
translates supplied information; it is not that monitor.

## Complex-system motivation and candidate questions

These are proposed research questions, not findings about real systems:

- **Latent internal state:** How could partially observed internal conditions
  affect the usefulness of an existing relationship? What observable evidence
  could distinguish those conditions without access to hidden truth?
- **Response to perturbations:** Could responses become nonlinear or show
  amplification near sensitive regimes? Under what assumptions would changes in
  response be informative rather than noise or a measurement artifact?
- **Shocks and state:** How could external shocks interact with internal system
  state, rather than shock magnitude alone explaining the observed response?
- **Transition proximity:** Can proximity to a specified regime change be
  operationally defined, and with what uncertainty? A warning boundary and the
  decision boundary for a particular action need not coincide.

The [existing system-layer study](../reports/lai_system_experiment_a.md) examines
state-dependent amplification in a frozen synthetic data-generating process.
Its constructed mechanism does not establish nonlinear dynamics, criticality,
or a natural critical point in a real system. It motivates controlled extensions,
not extrapolation of its results to a population or application domain.

## Candidate signal families to investigate

| Candidate | Research question and qualification |
| --- | --- |
| Recovery dynamics / critical slowing down | Could slower recovery after perturbations provide useful warning under specified dynamical assumptions? Such assumptions must be tested, not presumed. |
| Changing variance | Could variability distinguish transition-related changes from changing noise or sampling? |
| Changing autocorrelation | Could temporal dependence add warning information beyond ordinary persistence and data-processing effects? |
| Coupling/correlation structure | Could changing relationships between components provide information beyond shared external forcing? |
| Change-point or regime-shift evidence | Could evidence of distributional change support assessment? Detecting a change after onset is not automatically pre-transition warning. |

These are possible signal families, not universally valid critical-point
detectors. Some transitions may offer no usable early signal; apparent warnings
may occur without a transition. No thresholds, calibrated probabilities, or
validated operational measures are introduced here.

## Proposed future architecture

```text
Complex System
    ↓
Transition/Early-Warning Monitor   [future research; not implemented]
    ↓
Reliability Assessment            [future integration to validate]
    ↓
Decision Gate                    [existing deterministic prototype]
    ↓
Permission
```

A future monitor would supply causally available evidence and explicit uncertainty,
not authorization. Any new interface would require its own design and validation;
the current adapter must not silently reinterpret new signals. Application
consequences and reversibility would still inform permission separately.

## Validation path, not a capability claim

1. Define transition targets, observation limits, perturbations, and actionable
   horizons before examining outcomes. Distinguish warning from retrospective
   change detection.
2. Specify controlled transition and no-transition worlds, competing explanations,
   and baseline methods. Preserve causal information boundaries.
3. Evaluate false warnings, missed transitions, lead times, robustness to noise,
   and uncertainty on held-out conditions, with definitions fixed in advance.
4. Only after signal validation, study whether using those signals changes
   authorization behavior meaningfully under explicit application policies.

Possible future validation domains include financial markets, urban systems,
climate/weather dynamic systems, and other adaptive operational systems. These
are examples, not commitments or evidence of domain transfer. This repository
has not modeled Typhoon Dolphin, El Niño, actual financial markets, or any other
real system. Its synthetic market and traffic examples are not real-system
models or deployment validations.

Return to the [current architecture](current_architecture.md) or
[documentation index](README.md) for what exists today.
