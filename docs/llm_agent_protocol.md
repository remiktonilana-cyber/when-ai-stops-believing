# LLM Agent Protocol

## 1. Objective

This protocol defines a model-independent interface for evaluating whether an AI system can manage the validity boundary of a previously useful belief under changing evidence.

The benchmark does not evaluate general language ability, financial forecasting skill, or prompt quality.

It evaluates whether an agent can:

1. maintain a belief while evidence remains sufficiently supportive;
2. reduce confidence when evidence becomes increasingly contradictory;
3. avoid abandoning a useful belief because of isolated noise;
4. recognize when a previously useful belief has become unreliable;
5. express belief revision through a standardized belief state.

The central evaluation object is the belief trajectory over time.

---

## 2. Experimental Principle

All agents must operate under the same information boundary.

The agent is not allowed to observe the hidden structural state of the synthetic environment.

The environment determines whether the underlying relationship is structurally VALID, TRANSITION, or INVALID.

The agent must infer belief validity only from observable historical evidence.

The benchmark therefore separates:

- hidden structural truth;
- observable evidence;
- agent belief;
- external evaluation.

This separation is required to distinguish inference from privileged access.

---

## 3. Observation Contract

At each timestep, the LLM agent receives only information available through the benchmark observation interface.

The agent may receive:

- current timestamp;
- current observable market features;
- historical realized observations that are causally available at the current timestep;
- a bounded recent evidence window;
- previous belief state;
- compressed historical evidence summary produced according to the benchmark protocol.

The agent must not receive:

- `regime`;
- `beta`;
- latent driver values;
- future returns;
- future prices;
- future observations;
- any textual statement revealing whether the belief is currently VALID, TRANSITION, or INVALID.

The observation contract must remain identical across all evaluated LLM backends.

---

## 4. Temporal Causality

The agent may only use evidence available at or before the current decision timestep.

A return must not be used to evaluate a prediction before that return has become historically realized.

Future information must never be inserted into:

- prompts;
- summaries;
- memory;
- belief explanations;
- evaluation-visible agent state.

Any violation of temporal causality invalidates the experiment.

### 4.1 Minimum LLM Information Contract

At timestep `t`, the complete LLM-visible information set is:

```text
I_t = {
    current_observation_t,
    previous_belief_state_(t-1),
    recent_resolved_evidence,
    historical_evidence_summary
}
```

`current_observation_t` contains only information causally available at time
`t`. `previous_belief_state_(t-1)` contains the previous model belief; its
timestamp is attached and controlled by the benchmark adapter rather than the
model.

`recent_resolved_evidence` contains at most the latest 50 resolved
prediction-outcome pairs. A prediction may enter this collection only after its
outcome has been realized. An unresolved prediction must never expose its future
outcome.

`historical_evidence_summary` is generated deterministically by the benchmark.
It is not generated, rewritten, or selectively compressed by the LLM. The raw
full history is not included in `I_t`.

The complete LLM-visible input must never expose:

- `regime`;
- `beta`;
- the latent driver;
- the transition date;
- the ground-truth invalidation date;
- a future return;
- a future price.

The static observation dataset is agent-independent and must not contain
dynamic agent belief state. In particular, the benchmark must not write
`previous_belief_state_(t-1)` back into the static observations dataset. A
future model adapter assembles `I_t` dynamically from the static current
observation, benchmark-managed resolved evidence and historical summary, and
the prior model output.

This minimum contract is provider-independent. Provider-specific GPT, Grok,
Qwen, and DeepSeek API integrations are outside the v0.2 minimum contract.

---

## 5. Initial Belief

The benchmark begins with a predefined belief that has demonstrated usefulness during the stable VALID phase of the synthetic environment.

The initial belief is:

> The observable momentum signal contains useful information about the direction of the next-period return.

The initial belief state is:

```json
{
  "belief_status": "VALID",
  "confidence": 0.80
}
```
This initial state is fixed across agents unless a separate experiment explicitly studies prior sensitivity.

The purpose is not to ask whether the model can discover the belief from zero.

The purpose is to test whether the model can manage the continuing validity of a previously useful belief.

## 6. Memory Contract

The LLM agent must not receive an unlimited raw history. Its memory input is
limited to the fields defined by the Minimum LLM Information Contract.

Its state may contain four information classes:

1. current observation;
2. at most the latest 50 resolved prediction-outcome pairs;
3. previous belief state;
4. compressed historical evidence summary.

Memory must contain only causally available observable information.

Memory must not contain hidden environment variables.

The historical evidence summary must be generated deterministically by the
benchmark and must not be generated by the LLM.

This prevents context-window size from becoming the primary source of performance differences.

---

## 7. Belief Output Contract

At every evaluated timestep, the agent must return one structured belief state.

Required schema:

```json
{
  "belief_status": "VALID",
  "confidence": 0.80,
  "explanation": "Short explanation based only on observable evidence.",
  "evidence_summary": {
    "supporting_evidence": [],
    "contradicting_evidence": []
  }
}
```

Allowed values for `belief_status` are:

- `VALID`
- `UNCERTAIN`
- `INVALID`

`confidence` must be a numeric value between `0.0` and `1.0`.

The explanation must describe evidence rather than claim access to hidden structural truth.

The LLM is responsible only for the model-generated belief fields shown above.

The benchmark adapter must attach the current observation timestamp before constructing the complete belief state required by the benchmark belief interface. The model must not be asked to generate or infer the timestamp.

---

## 8. Meaning of Belief States

### VALID

The agent judges that the belief remains sufficiently supported for continued use.

VALID does not mean certainty.

### UNCERTAIN

The agent judges that current evidence is insufficient to confidently maintain or reject the belief.

UNCERTAIN represents an explicit validity-boundary state rather than a formatting failure or missing answer.

### INVALID

The agent judges that accumulated evidence is sufficiently inconsistent with the belief that the belief should no longer be treated as currently reliable.

INVALID does not imply that the belief can never become useful again.

Revalidation must be handled explicitly if later experiments allow belief recovery.

---

## 9. Reasoning Constraint

The agent may reason about:

- predictive success and failure;
- persistence of contradictory evidence;
- recent versus historical reliability;
- uncertainty;
- possible structural change;
- whether observed failures are consistent with noise.

The agent must not be instructed that a regime transition occurs at a known date.

The agent must not receive evaluation thresholds derived from hidden regime boundaries.

The benchmark should test belief revision, not reproduction of benchmark labels.

---

## 10. Fairness Across Models

When comparing different LLMs, the following must remain fixed:

- synthetic environment;
- observation sequence;
- initial belief;
- memory construction;
- recent evidence window;
- system-level task definition;
- required output schema;
- evaluation engine;
- temperature or sampling policy where technically comparable;
- retry and parsing policy.

Model-specific API formatting may differ, but semantic information supplied to the model must remain equivalent.

Prompt modifications made specifically to improve one model's benchmark score must be documented as a separate experimental condition.

---

## 11. Leakage Prevention

Before running an experiment, the complete model-visible input must be checked for prohibited information.

The following strings or semantic equivalents must not reveal hidden state:

- VALID regime;
- TRANSITION regime;
- INVALID regime;
- beta decay;
- structural break date;
- ground-truth invalidation date.

The evaluation engine may use hidden regime information after model inference.

The agent may not.

This creates a strict separation:

```text
Hidden Environment State
        |
        | not visible
        v
Observable Evidence
        |
        v
LLM Belief Agent
        |
        v
Belief State
        |
        v
Evaluation Engine
        |
        +---- accesses hidden ground truth
```

---

## 12. Failure Handling

A model response is not automatically treated as a belief revision if it fails to satisfy the output contract.

Examples include:

- invalid JSON;
- missing belief status;
- confidence outside `[0, 1]`;
- unsupported belief-status label;
- refusal to provide a belief state;
- malformed evidence fields.

Such events must be recorded separately as protocol failures.

The benchmark must distinguish:

- reasoning failure;
- belief-revision failure;
- interface/parsing failure.

---

## 13. Baseline Comparison

The LLM agent must be evaluated using the same evaluation engine used for the deterministic baseline agent.

Primary comparison metrics include:

- Adaptation Delay;
- False Persistence;
- False Abandonment;
- Belief Boundary Awareness.

Additional metrics may later evaluate:

- confidence calibration;
- trajectory stability;
- contradiction sensitivity;
- revalidation behavior.

The benchmark should not assume that an LLM must outperform the rule-based baseline.

A simpler agent outperforming an LLM is itself a meaningful experimental result.

---

## 14. Real-World Interpretation

The synthetic momentum belief is an experimental proxy for a broader class of real-world assumptions.

Examples include:

- a predictive model that previously generalized well;
- a fraud rule whose effectiveness changes after adversarial adaptation;
- a medical decision rule applied to a shifting patient population;
- a recommendation policy affected by changing user behavior;
- a scientific hypothesis facing accumulating contradictory observations;
- an autonomous operational policy whose environment has changed.

The benchmark therefore studies a general system problem:

> How should an intelligent system manage the validity of knowledge that was once useful but may no longer describe its environment?

The synthetic environment is used because structural truth can be controlled and hidden from the agent.

---

## 15. Scope Boundary

Version 0.2 focuses only on belief management after a previously useful relationship begins to weaken.

It does not yet test:

- autonomous discovery of new beliefs;
- optimal replacement-belief generation;
- causal explanation of structural change;
- multi-belief competition;
- early-warning prediction before observable degradation;
- open-world environment discovery.

These capabilities may be introduced in later benchmark tracks.

The current objective is narrower:

> Determine whether an AI agent can recognize and manage the validity boundary of one previously useful belief using only causally available evidence.
