# Implementation Plan

## 1. Programming Environment

The synthetic market generator will be implemented using Python 3.

Python is selected due to its strong ecosystem for numerical simulation,
data processing, and reproducible experiments.

---

## 2. Dependencies

The implementation requires:

- numpy
- pandas

numpy is used for stochastic noise generation, numerical operations,
missing-value representation, and the bounded nonlinear transformation used by
the internal momentum driver.

pandas is used for dataset construction and CSV export.

No machine learning framework is required for the synthetic market generator.

---

## 3. File Structure

The implementation follows the project structure:

src/

└── market_generator.py

data/

└── synthetic_market.csv

experiments/

└── calibrate_momentum_driver.py

The generator script is responsible for creating the benchmark synthetic dataset.

The calibration script is used only for parameter calibration, robustness
testing, and falsification of candidate generator parameters.

It is not part of the AI-visible benchmark environment.

---

## 4. Execution Requirement

The benchmark generator must be executable with:

python src/market_generator.py

Execution must produce:

data/synthetic_market.csv

The same configuration and random seed must reproduce the same synthetic
dataset.

No external API, live financial data, system clock state, or nondeterministic
external service may affect generation.

---

## 5. Output Requirement

The generated dataset must contain exactly the following fields:

- experiment_id
- date
- price
- return
- volume
- momentum_20d
- signal
- regime

### 5.1 Temporal Interpretation

Each row represents an observable market state at time t paired with the
subsequent realized return.

The row semantics are:

- date: timestamp of the observable state at time t
- price: Price_t, known before the subsequent return is realized
- volume: observable market activity at time t
- momentum_20d: momentum calculated using information available at time t
- signal: signal derived from Momentum_t at time t
- return: realized next-period return from t to t+1
- regime: hidden ground-truth regime governing the next-period return
- experiment_id: simulation metadata identifying the generated experiment

The temporal relationship is therefore:

Information at time t -> Return from t to t+1

The following row's price must satisfy:

Price_(t+1) = Price_t * (1 + Return_(t+1))

No future information may be used in the calculation of momentum_20d or signal.

### 5.2 Warm-Up Output Semantics

The first 20 observations, Day 0-19, are the warm-up period.

During these observations:

- momentum_20d must be stored as missing;
- signal must be stored as missing;
- price must remain finite and positive;
- return must remain finite;
- volume must remain finite;
- regime remains VALID;
- experiment_id remains defined.

The missing values in momentum_20d and signal are intentional.

They represent unavailable information because a complete 20-period price
history does not yet exist.

They must not be replaced by zero.

In particular:

signal = missing

does not mean:

signal = 0

The first fully defined momentum and signal observation occurs at Day 20.

### 5.3 AI-Visible and Hidden Information

The regime variable is retained exclusively as hidden ground truth for benchmark
evaluation and must not be provided to AI systems.

experiment_id is simulation metadata and should not be treated as an
AI-visible market variable.

The latent momentum driver must not be exported.

AI-visible benchmark inputs must be constructed without exposing hidden regime
information or other variables that reveal the ground-truth regime directly.

Warm-up missingness may remain visible because it truthfully represents the
information available at those times.

---

## 6. Synthetic Market Mechanism

### 6.1 Observable Momentum

The AI-visible momentum feature is defined as classical 20-period price momentum:

Momentum_t = Price_t / Price_(t-20) - 1

This variable preserves the economic interpretation of the belief being tested:

past winners tend to continue winning.

A complete 20-period price history is required.

Therefore:

For Day 0-19:

Momentum_t = missing

For Day 20 onward:

Momentum_t = Price_t / Price_(t-20) - 1

The implementation must not use future prices to fill the warm-up period.

The implementation must not substitute zero momentum during warm-up.

---

### 6.2 Observable Signal

The AI-visible binary signal is derived directly from Momentum_t once Momentum_t
becomes available.

For Day 0-19:

Signal_t = missing

For Day 20 onward:

Signal_t = 1 if Momentum_t > 0

Signal_t = 0 otherwise

The signal threshold is therefore fixed at zero.

The threshold is intentionally not calibrated.

The purpose of the signal is not to maximize strategy performance or benchmark
separation.

It provides a transparent operational representation of the momentum belief:

- positive 20-period momentum -> active momentum signal;
- zero or negative 20-period momentum -> inactive momentum signal.

Signal_t must be calculated exclusively from information available at time t.

It must not depend on:

- Return_(t+1);
- future prices;
- hidden regime;
- latent momentum driver;
- downstream AI benchmark performance.

The signal rule must remain fixed throughout benchmark evaluation.

The warm-up missing signal is not an exception to the zero-threshold rule.

The rule simply does not apply until Momentum_t exists.

---

### 6.3 Stable Momentum Driver

Validation showed that directly feeding raw or clipped cumulative momentum into
the return equation created unstable self-reinforcing market dynamics.

The observable momentum feature is therefore separated from the internal
return-generation driver.

For Day 20 onward:

Driver_t = tanh(Momentum_t / 0.10)

During Day 0-19:

Driver_t = 0

This zero value is an internal initialization convention only.

It must not be exported as:

Momentum_t = 0

or:

Signal_t = 0

Driver_t is used only internally by the simulator.

It must not be exported as an additional AI-visible dataset field.

This separation preserves the classical economic interpretation of the
observable momentum variable while preventing the return-generation mechanism
from entering persistent feedback attractors.

---

### 6.4 Return Generation

The next-period return is generated as:

Return_(t+1) = beta_t * Driver_t + epsilon_t

where:

epsilon_t ~ N(0, 0.01)

beta_t determines the strength of the momentum relationship in each market
regime.

For Day 0-19:

Driver_t = 0

therefore:

Return_(t+1) = epsilon_t

Warm-up returns are therefore generated from Gaussian noise only.

For Day 20 onward:

Driver_t = tanh(Momentum_t / 0.10)

and the standard frozen return equation applies.

---

### 6.5 Regime Schedule

The simulation contains three ground-truth regimes:

VALID:

- Day 0-999
- beta = 0.005

TRANSITION:

- Day 1000-1299
- beta decreases linearly from 0.005 to 0

INVALID:

- Day 1300-1999
- beta = 0

The intended belief lifecycle is therefore:

VALID:

Momentum contains stable predictive information after the warm-up period.

TRANSITION:

Momentum predictive power progressively weakens.

INVALID:

Momentum no longer contributes to return generation.

Day 0-19 remain part of VALID.

The beta value during those observations remains:

beta = 0.005

However:

Driver_t = 0

so:

beta_t * Driver_t = 0

and warm-up returns contain no deterministic momentum contribution.

The regime variable is hidden from AI systems during benchmark evaluation.

---

## 7. Codex Implementation Specification

The implementation must follow the predefined research design, generator
architecture, temporal alignment specification, calibrated parameter values,
frozen signal rule, and frozen warm-up convention.

### Role

The coding agent acts as an implementation engineer.

Its responsibility is to translate the frozen experimental design into executable
Python code.

The coding agent must not independently redesign the experiment or optimize
parameters against benchmark outcomes.

### Context

The generator creates a controlled synthetic market environment for evaluating
AI belief revision under changing market regimes.

The benchmark is designed to test whether an AI system can distinguish temporary
failure from structural invalidation of a previously predictive belief.

### Constraints

The implementation must:

- follow the defined modular architecture;
- preserve the predefined mathematical relationships;
- preserve temporal causality;
- avoid look-ahead information;
- avoid introducing machine learning models into the generator;
- avoid introducing additional AI-visible variables without a documented design
  change;
- keep hidden regime information separated from AI-visible inputs;
- keep the latent momentum driver internal to the simulator;
- preserve reproducibility through deterministic configuration and random
  seeding;
- preserve the calibrated parameters unless the research design is explicitly
  revised;
- implement the signal threshold exactly at zero after warm-up;
- represent warm-up momentum as missing;
- represent warm-up signal as missing;
- use Driver_t = 0 during warm-up;
- generate warm-up returns from Gaussian noise only;
- avoid calibrating or optimizing the signal threshold;
- avoid optimizing generator parameters against downstream AI benchmark
  performance.
- derive independent deterministic random-number streams for return noise and
  volume generation from the canonical seed;
- ensure that changing or removing volume generation does not alter the return
  noise sequence;
- keep volume independent of regime, momentum, signal, driver, beta, and return
  generation;

The coding agent must not independently choose alternative warm-up behavior.

Specifically, it must not:

- set warm-up momentum to zero;
- set warm-up signal to zero;
- forward-fill or back-fill warm-up momentum;
- calculate warm-up momentum using future prices;
- expose Driver_t as an observable substitute for missing momentum;
- change the warm-up length.

---

## 8. Required Functions

The implementation must include the following functional responsibilities:

- load_config()
- get_regime(day)
- calculate_beta(day, regime)
- generate_return(momentum, beta)
- update_price(previous_price, return_value)
- calculate_features(price_history)
- save_dataset(data)

### Function Semantics

#### load_config()

Loads the frozen simulation configuration and reproducibility parameters.

The configuration must include all numerical and structural values required to
reproduce the synthetic market.

Required values include:

- simulation_days = 2000
- initial_price = 100
- momentum_window = 20
- momentum_scale = 0.10
- signal_threshold = 0
- valid_beta = 0.005
- noise_std = 0.01
- VALID end = Day 999
- TRANSITION = Day 1000-1299
- INVALID begins = Day 1300
- warm-up length = 20 observations

The fixed zero-threshold signal rule and warm-up convention are part of the
configuration specification.

---

#### get_regime(day)

Returns the hidden ground-truth regime corresponding to the simulation day.

Rules:

Day 0-999:

VALID

Day 1000-1299:

TRANSITION

Day 1300-1999:

INVALID

---

#### calculate_beta(day, regime)

Returns the momentum-driver coefficient for the current regime.

It must implement:

- VALID: beta = 0.005
- TRANSITION: linear decay from 0.005 to 0
- INVALID: beta = 0

The transition must satisfy the frozen endpoint convention:

Day 1000:

beta = 0.005

Day 1299:

beta = 0

Warm-up does not alter beta.

Day 0-19 therefore retain beta = 0.005.

---

#### calculate_features(price_history)

Calculates the observable 20-period momentum feature and its derived signal using
only information available before the subsequent return is generated.

Let the current observable price be the final element of price_history.

If fewer than 21 prices are currently available:

momentum_20d = missing

signal = missing

This corresponds exactly to Day 0-19.

Once at least 21 prices are available:

Momentum_t = Price_t / Price_(t-20) - 1

and:

Signal_t = 1 if Momentum_t > 0

Signal_t = 0 otherwise

The signal threshold is fixed at zero.

It must not be calibrated or optimized against downstream benchmark outcomes.

No future information may be used.

The function must not return signal = 0 when momentum is unavailable.

---

#### generate_return(momentum, beta)

Generates the realized next-period return.

If momentum is missing:

Driver_t = 0

Otherwise:

Driver_t = tanh(momentum / 0.10)

Then:

epsilon_t ~ N(0, 0.01)

and:

Return_(t+1) = beta_t * Driver_t + epsilon_t

Therefore, during warm-up:

Return_(t+1) = epsilon_t

The implementation may detect missing momentum using an appropriate numpy or
pandas missing-value check.

However, it must not convert the exported observable momentum value itself to
zero.

The internal driver must not be added to the exported dataset schema.

---

#### update_price(previous_price, return_value)

Updates the market price according to:

Price_(t+1) = Price_t * (1 + Return_(t+1))

The function must reject or otherwise prevent invalid non-positive price
transitions.

The resulting price must remain finite.

---

#### save_dataset(data)

Exports the completed synthetic market dataset to:

data/synthetic_market.csv

The exporter must preserve the required column order:

experiment_id

date

price

return

volume

momentum_20d

signal

regime

The exporter must preserve intentional missing values in:

- momentum_20d during Day 0-19;
- signal during Day 0-19.

It must not introduce unexpected missing values elsewhere.

---

## 9. Frozen Simulation Parameters

The benchmark generator uses the following calibrated and frozen configuration:

| Parameter | Frozen Value |
|---|---|
| Total simulation days | 2000 |
| Initial price | 100 |
| Momentum lookback window | 20 periods |
| Momentum definition | Price_t / Price_(t-20) - 1 |
| Signal rule after warm-up | 1 if Momentum_t > 0, otherwise 0 |
| Signal threshold | 0 |
| Momentum transformation | tanh |
| Momentum transformation scale | 0.10 |
| VALID regime | Day 0-999 |
| TRANSITION regime | Day 1000-1299 |
| INVALID regime | Day 1300-1999 |
| VALID beta | 0.005 |
| TRANSITION beta | Linear decay from 0.005 to 0 |
| INVALID beta | 0 |
| Noise distribution | Normal distribution N(0, 0.01) |
| Warm-up period | Day 0-19 |
| Warm-up momentum_20d | Missing |
| Warm-up signal | Missing |
| Warm-up internal driver | 0 |
| Warm-up return mechanism | Gaussian noise only |
| Canonical random seed | 42 |
| Start date | 2000-01-03 |
| Experiment ID | momentum_decay_seed_42 |
| Volume distribution | ln(Volume_t) ~ Normal(ln(1,000,000), 0.25^2) |
| RNG architecture | SeedSequence(42).spawn(2): first child = return noise; second child = volume |
The zero signal threshold is a design choice rather than a calibrated parameter.

It must not be modified in response to generator validation results or downstream
AI benchmark performance.

The warm-up convention is also a structural design choice.

It must not be modified based on generator validation results or downstream AI
benchmark performance.

These values supersede the earlier alpha-based implementation.

The previous configuration using alpha = 0.5 and direct clipped momentum feedback
is deprecated and must not be used by the benchmark generator.

---

## 10. Calibration and Robustness Basis

The frozen Stable Momentum Driver parameters were selected through:

1. single-seed parameter exploration;
2. multi-seed candidate comparison; and
3. a 20-seed falsification stress test.

The selected configuration was not chosen to maximize predictive correlation.

It was selected to provide a minimum sufficient momentum signal that remains
statistically detectable without producing persistent self-reinforcing market
dynamics.

For the frozen Candidate A configuration:

- scale = 0.10
- VALID beta = 0.005
- noise standard deviation = 0.01

the 20-seed falsification test produced approximately:

- mean VALID momentum-return correlation: 0.258
- mean TRANSITION momentum-return correlation: 0.101
- mean INVALID momentum-return correlation: -0.007

Additional robustness results:

- VALID correlation was positive in 20/20 runs.
- Absolute INVALID correlation remained below 0.10 in 20/20 runs.
- All 20 simulations remained finite without NaN-driven simulation failure.
- Maximum VALID driver saturation was approximately 3.7%.
- Strict VALID > TRANSITION > INVALID correlation ordering occurred in 17/20
  runs.

The absence of strict ordering in every finite sample is not treated as generator
failure because the TRANSITION regime is deliberately non-stationary and noisy.

The calibrated Stable Momentum Driver parameters are now frozen and should not
be further optimized against downstream benchmark results.

The signal threshold was not selected through this calibration procedure.

It is fixed independently at zero to preserve a simple and interpretable binary
representation of the observable momentum belief.

The explicit warm-up missing-value convention was documented after the
calibration exercise.

It does not alter:

- scale = 0.10;
- beta = 0.005;
- noise standard deviation = 0.01;
- the post-warm-up Stable Momentum Driver equation.

The historical calibration statistics must not be silently rewritten as though
they were newly recomputed under a modified implementation.

If the final implementation is regenerated under the clarified warm-up
convention, its behavior must be validated independently against the frozen
acceptance criteria.

---

## 11. Validation Requirements

Before the benchmark generator implementation is considered final, it must pass
the following validation checks.

### 11.1 Structural Validation

- Exactly 2000 observations are generated.
- Required dataset fields are present.
- Column order matches the frozen schema.
- Regime boundaries match the frozen schedule.
- Day 0-19 are labeled VALID.
- Day 0-19 momentum_20d values are missing.
- Day 0-19 signal values are missing.
- Day 20 onward momentum_20d values are fully defined.
- Day 20 onward signal values are fully defined.
- No unexpected missing values occur.
- No infinite numeric values occur.
- Price, return, and volume contain no missing values.

The only expected exported missing values are:

- momentum_20d during Day 0-19;
- signal during Day 0-19.

### 11.2 Warm-Up Validation

For every observation from Day 0 through Day 19:

- Momentum_t must be unavailable;
- Signal_t must be unavailable;
- internal Driver_t must equal 0;
- the deterministic momentum contribution beta_t * Driver_t must equal 0;
- Return_(t+1) must therefore consist only of epsilon_t.

Validation must not interpret missing signal as signal = 0.

At Day 20:

- Momentum_20d must become available for the first time;
- it must equal Price_20 / Price_0 - 1;
- Signal_20 must be derived from Momentum_20 using the frozen zero threshold.

### 11.3 Temporal Validation

- Momentum uses only information available at time t.
- Signal uses only Momentum_t available at time t.
- Return represents the subsequent t to t+1 realization.
- The next row's price is consistent with the previous row's price and return.
- No look-ahead leakage is present.
- Warm-up momentum must not be reconstructed using future prices.

For Day 20 onward:

Momentum_t = Price_t / Price_(t-20) - 1

must hold exactly within appropriate floating-point tolerance.

### 11.4 Signal Validation

For every observation from Day 20 onward:

- if Momentum_t > 0, Signal_t must equal 1;
- if Momentum_t <= 0, Signal_t must equal 0.

For Day 0-19:

- Signal_t must be missing.

The validation procedure must verify exact agreement between momentum_20d and
signal after warm-up.

The signal threshold must not be adjusted based on these validation results.

### 11.5 Dynamic Validation

During VALID after warm-up:

- both positive and negative momentum states should occur;
- the latent driver should not remain persistently saturated;
- the simulated price process should remain finite and dynamically stable;
- VALID should retain detectable positive momentum predictive information.

Across the lifecycle:

- predictive strength should weaken on average through TRANSITION;
- momentum predictive information should be approximately zero in INVALID.

Dynamic validation is a falsification test of the frozen design.

It is not a parameter-search procedure.

A failed dynamic check must trigger:

1. investigation for an implementation error; or
2. if no implementation error exists, an explicit research-design review.

It must not trigger undocumented parameter tuning.

### 11.6 Reproducibility Validation

Running:

python src/market_generator.py

with the same frozen configuration and random seed must reproduce the same
dataset.

Reproducibility includes:

- identical warm-up missingness;
- identical generated returns;
- identical price path;
- identical volume path;
- identical post-warm-up momentum;
- identical post-warm-up signal;
- identical regime labels.

---

## 12. Implementation Freeze Rule

Once the generator passes the frozen validation requirements, its scientific
mechanism, calibrated parameters, signal rule, and warm-up convention are
considered fixed for the benchmark.

Subsequent AI benchmark results must not be used as justification for tuning the
synthetic market generator.

Any future change to:

- momentum definition
- signal definition
- signal threshold
- warm-up length
- warm-up missing-value semantics
- warm-up driver behavior
- latent driver transformation
- beta schedule
- noise process
- regime schedule
- temporal alignment
- dataset schema

must be treated as an explicit new experimental design revision rather than an
implementation adjustment.

---

## 13. Current Implementation Source of Truth

The current implementation must distinguish two phases.

### Day 0-19: Warm-Up

Price history available at time t

        ↓

Momentum_t = missing

        ↓

Signal_t = missing

        ↓

Driver_t = 0

        ↓

beta_t = 0.005

        ↓

Return_(t+1) = epsilon_t

        ↓

Record time-t observation

        ↓

Price_(t+1)

        ↓

Next simulation period

### Day 20 onward: Standard Mechanism

Price history available at time t

        ↓

Momentum_t

        ↓

Signal_t

        ↓

Driver_t

        ↓

beta_t + Driver_t + Noise

        ↓

Return_(t+1)

        ↓

Record time-t observation

        ↓

Price_(t+1)

        ↓

Next simulation period

The frozen post-warm-up equations are:

Momentum_t = Price_t / Price_(t-20) - 1

Signal_t = 1 if Momentum_t > 0, otherwise 0

Driver_t = tanh(Momentum_t / 0.10)

Return_(t+1) = beta_t * Driver_t + epsilon_t

epsilon_t ~ N(0, 0.01)

Price_(t+1) = Price_t * (1 + Return_(t+1))

The frozen warm-up equations are:

Momentum_t = missing

Signal_t = missing

Driver_t = 0

Return_(t+1) = epsilon_t

epsilon_t ~ N(0, 0.01)

The frozen regime schedule is:

VALID:

Day 0-999

beta = 0.005

TRANSITION:

Day 1000-1299

beta decreases linearly from 0.005 to 0

INVALID:

Day 1300-1999

beta = 0

The signal threshold is fixed at zero from Day 20 onward.

The signal rule must not be calibrated or optimized against downstream AI
benchmark outcomes.

The warm-up convention must not be calibrated or optimized against downstream
AI benchmark outcomes.

The only expected missing values in the exported dataset are:

- momentum_20d during Day 0-19;
- signal during Day 0-19.

This specification supersedes all earlier alpha-based, direct-momentum, and
clipped-momentum generator implementations.