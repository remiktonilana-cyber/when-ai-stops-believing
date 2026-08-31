# Data Generation Design

## 1. Objective

The purpose of the synthetic data generation process is to create a controlled
market environment for evaluating AI belief revision.

The benchmark asks whether an AI system can distinguish temporary
underperformance from permanent structural change when a previously predictive
market belief gradually loses validity.

The synthetic market must therefore satisfy two requirements simultaneously:

1. the tested belief must have detectable predictive value during the VALID
   regime; and
2. the simulated market dynamics must remain stable enough that belief revision,
   rather than pathological price feedback, is the object being measured.

The generator is designed as a controlled experimental environment rather than
as a realistic model of an entire financial market.

---

## 2. Data Layers

The synthetic market dataset contains three conceptual layers.

### 2.1 Observable Market Variables

These variables represent information that may be provided to AI systems during
benchmark evaluation.

They include:

- date
- price
- return
- volume
- momentum_20d
- signal

### 2.2 Hidden Ground Truth Variables

These variables exist only for experimental evaluation and must not be exposed
to AI systems.

The primary hidden variable is:

- regime

The regime label provides the ground truth for whether the momentum belief is
currently VALID, transitioning toward invalidity, or INVALID.

### 2.3 Experiment Metadata

Metadata is used for experiment identification and reproducibility.

The primary metadata field is:

- experiment_id

experiment_id is not a market variable and should not be treated as part of the
AI-visible economic information set.

---

## 3. Dataset Schema

The final synthetic dataset contains the following fields:

| Variable | Type | Description | AI Visible |
|---|---|---|---|
| experiment_id | string | Simulation identifier | No |
| date | string / integer | Trading-period identifier | Yes |
| price | float | Observable synthetic asset price at time t | Yes |
| return | float | Realized next-period return from t to t+1 | Yes |
| volume | float | Observable trading activity indicator at time t | Yes |
| momentum_20d | float | Classical 20-period price momentum at time t | Yes |
| signal | integer | Trading-rule indicator derived from information available at time t | Yes |
| regime | string | Hidden true market regime | No |

The dataset is exported to:

data/synthetic_market.csv

The regime variable is retained only for benchmark evaluation.

It must be excluded from AI-visible benchmark inputs.

---

## 4. Temporal Alignment Specification

Each observation represents an observable information state at time t together
with the return realized immediately after that state.

The row semantics are:

- date: observable state time t
- price: Price_t
- volume: information observable at time t
- momentum_20d: momentum computed using prices available at time t
- signal: signal derived from information available at time t
- return: realized return from t to t+1
- regime: hidden regime governing that next-period return
- experiment_id: experiment metadata

The causal ordering is:

Information at time t
→ internal return-generation mechanism
→ Return from t to t+1
→ Price_(t+1)

The price transition must satisfy:

Price_(t+1) = Price_t * (1 + Return_(t+1))

No information from Price_(t+1) or any later observation may be used to
construct momentum_20d or signal at time t.

This temporal specification is required to prevent look-ahead leakage and to
ensure that AI belief updating is evaluated using information that would have
been available at the decision time.

---

## 5. Observable Momentum Definition

The benchmark tests a classical price-momentum belief.

The AI-visible momentum variable is therefore defined as:

Momentum_t = Price_t / Price_(t-20) - 1

where Price_t is the price observable at time t.

This representation preserves the economic interpretation:

assets with stronger recent price performance may exhibit stronger subsequent
returns while the momentum relationship remains valid.

The first 20 observations constitute a warm-up period because the momentum
feature requires 20 periods of historical price information.

---

## 6. Signal Generation


The signal variable is a simple binary representation of the observable
momentum belief.

It is generated exclusively from information available at time t.

The fixed rule is:

Signal_t = 1 if Momentum_t > 0

Signal_t = 0 otherwise

where:

Momentum_t = Price_t / Price_(t-20) - 1

The zero threshold is intentionally not calibrated.

Its purpose is not to maximize strategy performance or benchmark separation.
It provides a transparent operational interpretation of the momentum belief:

- positive 20-period momentum -> active momentum signal;
- zero or negative 20-period momentum -> inactive momentum signal.

The signal-generation rule must remain fixed throughout benchmark evaluation.

It must not use:

- Return_(t+1);
- future prices;
- the hidden regime;
- the latent momentum driver;
- downstream AI benchmark performance.

The signal is an observable representation of the momentum belief rather than a
component of the latent market-generation mechanism.

---

## 7. Current Frozen Return-Generation Mechanism

The synthetic market uses a Stable Momentum Driver.

The observable momentum feature and the internal return-generation driver are
deliberately separated.

This separation is necessary because directly feeding cumulative price momentum
back into returns was found to create unstable recursive price dynamics.

The current frozen mechanism consists of four stages:

Observable price history

→ Observable Momentum_t

→ Internal Driver_t

→ Regime-dependent beta_t

→ Return_(t+1)

---

## 8. Internal Stable Momentum Driver

The observable momentum variable is transformed internally as:

Driver_t = tanh(Momentum_t / 0.10)

The transformation scale is therefore:

scale = 0.10

Driver_t is a latent simulation variable.

It exists only inside the synthetic market generator and must not be exported as
an AI-visible field.

The nonlinear transformation limits the influence of extreme cumulative
momentum while preserving its sign and relative direction.

Importantly, this transformation does not redefine the observable economic
feature.

AI systems continue to observe classical 20-period price momentum:

Momentum_t = Price_t / Price_(t-20) - 1

The distinction is therefore:

Observable belief variable:
Momentum_t

Internal simulation driver:
Driver_t = tanh(Momentum_t / 0.10)

---

## 9. Return Generation

The realized next-period return is generated according to:

Return_(t+1) = beta_t * Driver_t + epsilon_t

where:

epsilon_t ~ N(0, 0.01)

and beta_t determines how strongly the momentum belief affects subsequent
returns.

The deterministic component is:

beta_t * Driver_t

The stochastic component is:

epsilon_t

The momentum component must be detectable during VALID without dominating the
stochastic component strongly enough to generate a deterministic price
attractor.

---

## 10. Regime Logic

The benchmark contains three hidden market regimes.

### 10.1 VALID

Simulation period:

Day 0-999

Parameter:

beta = 0.005

During VALID, momentum contains stable positive predictive information.

The intended relationship is:

higher Momentum_t
→ higher expected Return_(t+1)

The relationship is intentionally noisy rather than deterministic.

---

### 10.2 TRANSITION

Simulation period:

Day 1000-1299

During TRANSITION:

beta decreases linearly from 0.005 to 0.

Momentum therefore progressively loses predictive strength.

The transition is deliberately gradual rather than instantaneous.

This creates the central epistemic challenge of the benchmark:

an AI system must determine whether recent failures represent ordinary noise or
evidence that the previously valid relationship is structurally disappearing.

---

### 10.3 INVALID

Simulation period:

Day 1300-1999

Parameter:

beta = 0

Therefore:

Return_(t+1) = epsilon_t

Momentum no longer contributes to expected return generation.

Any finite-sample momentum-return correlation observed during INVALID should
arise from stochastic variation rather than from the ground-truth data-generating
process.

---

## 11. Intended Belief Lifecycle

The synthetic environment represents the following lifecycle:

VALID
→ momentum is genuinely predictive

TRANSITION
→ predictive strength progressively decays

INVALID
→ momentum no longer has predictive value

The benchmark does not tell the AI when these structural changes occur.

The AI must infer the change from the observable evidence stream.

The experimental objective is therefore not merely to test prediction accuracy.

It is to measure how an AI system updates confidence in a previously successful
belief as contradictory evidence accumulates.

---

## 12. Historical Design Revisions

The current Stable Momentum Driver was reached through validation and
falsification of earlier generator designs.

These earlier mechanisms are retained here only as methodological history.

They are superseded and must not be implemented as the current benchmark
generator.

### 12.1 Initial Momentum Representation

An early implementation represented momentum using average trailing returns.

Validation showed that this behaved more like a short-horizon return feature
than the classical cumulative price-momentum belief intended by the experiment.

The observable feature was therefore revised to:

Momentum_t = Price_t / Price_(t-20) - 1

This revised momentum definition remains part of the current benchmark.

### 12.2 Superseded Direct Alpha Model

An early return-generation design used a direct relationship of the form:

Return = alpha * Momentum + noise

This approach treated observable cumulative momentum directly as a recursive
return driver.

It is no longer part of the benchmark specification.

### 12.3 Superseded Clipped-Momentum Model

A later stabilization attempt bounded cumulative momentum before applying it to
the return process.

Conceptually, this took the form:

bounded momentum
→ regime-dependent coefficient
→ return

Although clipping limited magnitude, validation showed that it did not eliminate
the underlying recursive feedback problem.

Instead, the system entered persistent boundary saturation in the VALID regime.

This design is also superseded.

### 12.4 Dynamic Feedback Failure

Under the superseded direct-feedback design, VALID became dominated by a
persistent negative-momentum attractor.

Diagnostic validation showed approximately:

- mean VALID momentum: -0.637
- positive VALID momentum rate: 0%
- clipped-state rate: approximately 99.5%
- mean VALID daily return: approximately -5.0%

The resulting process did not represent a noisy but predictive momentum market.

Instead, the generator had produced a recursive deterministic state.

This demonstrated that bounding variable magnitude alone was insufficient.

The observable economic feature had to be separated from the internal
market-generation driver.

### 12.5 Stable Momentum Driver Revision

The current design therefore introduced:

Driver_t = tanh(Momentum_t / scale)

and:

Return_(t+1) = beta_t * Driver_t + noise_t

This architecture preserves classical momentum as the observable belief while
controlling the feedback strength of the internal simulation process.

Only this Stable Momentum Driver specification is active in the frozen
benchmark design.

---

## 13. Parameter Calibration Criteria

The Stable Momentum Driver parameters were calibrated before being frozen.

Calibration was not performed to maximize benchmark separation or downstream AI
performance.

Its purpose was to identify a dynamically stable parameter region that still
contains a detectable belief signal.

Candidate parameters included:

- momentum transformation scale
- VALID beta
- noise standard deviation

A candidate parameter set was considered acceptable only if it satisfied the
following conditions.

### 13.1 Numerical Stability

- no infinite prices;
- no undefined prices;
- no NaN-driven simulation failure;
- no persistent driver saturation.

### 13.2 Momentum-State Diversity

During VALID:

- both positive and negative momentum observations should occur;
- neither momentum sign should dominate nearly the entire regime.

### 13.3 Detectable VALID Relationship

Momentum should exhibit a positive predictive relationship with next-period
return during VALID.

### 13.4 Transitional Decay

Predictive strength should weaken, on average, as the system moves through
TRANSITION.

Because TRANSITION is short and explicitly non-stationary, strict correlation
ordering is not required for every individual random seed.

### 13.5 INVALID Neutrality

Momentum-return predictive information should be approximately zero during
INVALID.

### 13.6 Signal-to-Noise Balance

The deterministic momentum component must be strong enough to detect
statistically but weak enough that it does not dominate stochastic market noise.

### 13.7 Multi-Seed Robustness

Candidate selection must not depend on a single favorable random seed.

Parameters must be evaluated across multiple fixed seeds before being frozen.

---

## 14. Final Calibrated Parameters

Following single-seed parameter exploration, multi-seed candidate comparison,
and a 20-seed falsification stress test, the Stable Momentum Driver parameters
are frozen as follows:

| Parameter | Frozen Value |
|---|---|
| Total simulation days | 2000 |
| Initial price | 100 |
| Momentum lookback | 20 periods |
| Momentum transformation scale | 0.10 |
| VALID period | Day 0-999 |
| TRANSITION period | Day 1000-1299 |
| INVALID period | Day 1300-1999 |
| VALID beta | 0.005 |
| TRANSITION beta | Linear decay from 0.005 to 0 |
| INVALID beta | 0 |
| Noise standard deviation | 0.01 |

The selected parameter set was not chosen to maximize predictive correlation.

It was selected as the minimum sufficient signal that remained dynamically
stable and statistically detectable across random seeds.

---

## 15. Calibration Evidence

Across the 20-seed falsification stress test, the frozen configuration produced:

- positive VALID momentum-return correlation in 20/20 runs;
- mean VALID correlation of approximately 0.258;
- mean TRANSITION correlation of approximately 0.101;
- mean INVALID correlation of approximately -0.007;
- absolute INVALID correlation below 0.10 in 20/20 runs;
- finite numerical output in 20/20 runs;
- maximum VALID driver saturation of approximately 3.7%;
- strict VALID > TRANSITION > INVALID correlation ordering in 17/20 runs.

Across those runs:

- minimum VALID positive-momentum rate was approximately 27.6%;
- maximum VALID positive-momentum rate was approximately 62.8%;
- minimum simulated price was approximately 4.03;
- maximum simulated price was approximately 518.26;
- minimum VALID momentum-return correlation was approximately 0.179;
- maximum VALID momentum-return correlation was approximately 0.334.

These results indicate that the previous persistent attractor was removed while
the intended momentum relationship remained detectable.

The absence of strict regime-correlation ordering in every random seed is not
treated as a failure.

TRANSITION contains only 300 observations and is deliberately non-stationary, so
finite-sample correlation estimates may fluctuate even when the underlying beta
schedule decreases monotonically.

---

## 16. Validation Requirements

Before a generated dataset is accepted for benchmark use, it must satisfy
structural, temporal, dynamic, and ground-truth validation.

### 16.1 Structural Validation

The generator must:

- produce exactly 2000 observations;
- contain the required dataset fields;
- preserve the frozen regime boundaries;
- handle the 20-period warm-up consistently;
- contain no unexpected NaN or infinite values.

### 16.2 Temporal Validation

The generator must verify that:

- Momentum_t uses only prices available at time t;
- signal uses only information available at time t;
- Return_(t+1) is generated only after time-t features are constructed;
- Price_(t+1) is generated from Price_t and Return_(t+1);
- no future observation contributes to a current feature.

### 16.3 Dynamic Validation

The VALID regime should exhibit:

- both positive and negative momentum states;
- limited driver saturation;
- stable finite prices;
- detectable positive momentum predictive information.

Across the lifecycle:

- predictive strength should weaken on average through TRANSITION;
- momentum predictive information should be approximately zero in INVALID.

### 16.4 Ground Truth Validation

Observed synthetic-market behavior should be checked against the known
regime-generating mechanism.

The hidden regime schedule is:

VALID
→ TRANSITION
→ INVALID

Validation establishes that the generated evidence stream is consistent with the
intended structural change before the dataset is used to evaluate AI systems.

---

## 17. Design Freeze Rule

The Stable Momentum Driver parameters are now frozen for the benchmark.

They must not be further optimized against downstream AI benchmark outcomes.

In particular, AI performance must not be used to retune:

- momentum lookback;
- momentum transformation scale;
- beta values;
- beta transition schedule;
- noise standard deviation;
- regime boundaries;
- temporal alignment;
- observable feature definitions.

Doing so after observing benchmark results would contaminate the experimental
design by allowing the environment to adapt to the systems being evaluated.

Any future modification to these components must therefore be treated as a new
experimental design version rather than as routine implementation tuning.

---

## 18. Current Source of Truth

For the current benchmark version, the active data-generating specification is:

Momentum_t = Price_t / Price_(t-20) - 1

Driver_t = tanh(Momentum_t / 0.10)

Return_(t+1) = beta_t * Driver_t + epsilon_t

epsilon_t ~ N(0, 0.01)

with:

VALID:
beta = 0.005

TRANSITION:
beta decreases linearly from 0.005 to 0

INVALID:
beta = 0

and:

Price_(t+1) = Price_t * (1 + Return_(t+1))

All earlier direct-alpha and clipped-momentum mechanisms are superseded.

This section defines the current frozen data-generation mechanism.