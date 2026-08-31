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
and the bounded nonlinear transformation used by the internal momentum driver.

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

The calibration script is used only for parameter calibration, robustness testing,
and falsification of candidate generator parameters. It is not part of the
AI-visible benchmark environment.

---

## 4. Execution Requirement

The benchmark generator should be executable with:

python src/market_generator.py

Execution should produce:

data/synthetic_market.csv

The same configuration and random seed must reproduce the same synthetic dataset.

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

### Temporal Interpretation

Each row represents an observable market state at time t paired with the
subsequent realized return.

The row semantics are:

- date: timestamp of the observable state at time t
- price: Price_t, known before the subsequent return is realized
- volume: observable market activity at time t
- momentum_20d: momentum calculated using information available at time t
- signal: binary signal derived from Momentum_t at time t using the frozen zero-threshold rule
- return: realized next-period return from t to t+1
- regime: hidden ground-truth regime governing the next-period return
- experiment_id: simulation metadata identifying the generated experiment

The temporal relationship is therefore:

Information at time t -> Return from t to t+1

The following row's price must satisfy:

Price_(t+1) = Price_t * (1 + Return_(t+1))

No future information may be used in the calculation of momentum_20d or signal.

### AI-Visible and Hidden Information

The regime variable is retained exclusively as hidden ground truth for benchmark
evaluation and must not be provided to AI systems.

experiment_id is simulation metadata and should not be treated as an
AI-visible market variable.

AI-visible benchmark inputs must be constructed without exposing hidden regime
information or other variables that reveal the ground-truth regime directly.

---

## 6. Synthetic Market Mechanism

### 6.1 Observable Momentum

The AI-visible momentum feature is defined as classical 20-period price momentum:

Momentum_t = Price_t / Price_(t-20) - 1

This variable preserves the economic interpretation of the belief being tested:

past winners tend to continue winning.

The first 20 observations are treated as a warm-up period because the momentum
feature requires historical price information.

---

### 6.2 Observable Signal

The AI-visible binary signal is derived directly from Momentum_t.

The frozen rule is:

Signal_t = 1 if Momentum_t > 0

Signal_t = 0 otherwise

The signal threshold is therefore fixed at zero.

The threshold is intentionally not calibrated.

The purpose of the signal is not to maximize strategy performance or benchmark
separation. It provides a transparent operational representation of the
momentum belief:

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

---

### 6.3 Stable Momentum Driver

Validation showed that directly feeding raw or clipped cumulative momentum into
the return equation created unstable self-reinforcing market dynamics.

The observable momentum feature is therefore separated from the internal
return-generation driver.

The internal latent driver is:

Driver_t = tanh(Momentum_t / 0.10)

Driver_t is used only internally by the simulator.

It must not be exported as an additional AI-visible dataset field.

This separation preserves the classical economic interpretation of the observable
momentum variable while preventing the return-generation mechanism from entering
persistent feedback attractors.

---

### 6.4 Return Generation

The next-period return is generated as:

Return_(t+1) = beta_t * Driver_t + epsilon_t

where:

epsilon_t ~ N(0, 0.01)

beta_t determines the strength of the momentum relationship in each market regime.

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

Momentum contains stable predictive information.

TRANSITION:

Momentum predictive power progressively weakens.

INVALID:

Momentum no longer contributes to return generation.

The regime variable is hidden from AI systems during benchmark evaluation.

---

## 7. Codex Implementation Specification

The implementation must follow the predefined research design, generator
architecture, temporal alignment specification, calibrated parameter values,
and frozen signal rule.

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

- Follow the defined modular architecture.
- Preserve the predefined mathematical relationships.
- Preserve temporal causality.
- Avoid look-ahead information.
- Avoid introducing machine learning models into the generator.
- Avoid introducing additional AI-visible variables without a documented design change.
- Keep hidden regime information separated from AI-visible inputs.
- Keep the latent momentum driver internal to the simulator.
- Preserve reproducibility through deterministic configuration and random seeding.
- Preserve the calibrated parameters unless the research design is explicitly revised.
- Implement the signal threshold exactly at zero.
- Avoid calibrating or optimizing the signal threshold.
- Avoid optimizing generator parameters against downstream AI benchmark performance.

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

The configuration must include all numerical values required to reproduce the
synthetic market, including the fixed zero-threshold signal rule.

---

#### get_regime(day)

Returns the hidden ground-truth regime corresponding to the simulation day.

---

#### calculate_beta(day, regime)

Returns the momentum-driver coefficient for the current regime.

It must implement:

- VALID: beta = 0.005
- TRANSITION: linear decay from 0.005 to 0
- INVALID: beta = 0

---

#### calculate_features(price_history)

Calculates the observable 20-period momentum feature and its derived signal using
only information available before the subsequent return is generated.

Momentum must be calculated as:

Momentum_t = Price_t / Price_(t-20) - 1

The signal must be calculated as:

Signal_t = 1 if Momentum_t > 0

Signal_t = 0 otherwise

The signal threshold is fixed at zero.

It must not be calibrated or optimized against downstream benchmark outcomes.

No future information may be used.

---

#### generate_return(momentum, beta)

Internally transforms observable momentum using:

Driver_t = tanh(Momentum_t / 0.10)

and generates:

Return_(t+1) = beta_t * Driver_t + epsilon_t

where:

epsilon_t ~ N(0, 0.01)

The internal driver must not be added to the exported dataset schema.

---

#### update_price(previous_price, return_value)

Updates the market price according to:

Price_(t+1) = Price_t * (1 + Return_(t+1))

---

#### save_dataset(data)

Exports the completed synthetic market dataset to:

data/synthetic_market.csv

---

## 9. Frozen Simulation Parameters

The benchmark generator uses the following calibrated and frozen configuration:

| Parameter | Frozen Value |
|---|---|
| Total simulation days | 2000 |
| Initial price | 100 |
| Momentum lookback window | 20 periods |
| Momentum definition | Price_t / Price_(t-20) - 1 |
| Signal rule | 1 if Momentum_t > 0, otherwise 0 |
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
| Warm-up period | First 20 observations |

The zero signal threshold is a design choice rather than a calibrated parameter.

It must not be modified in response to generator validation results or downstream
AI benchmark performance.

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
- All 20 simulations remained finite without NaN or infinite values.
- Maximum VALID driver saturation was approximately 3.7%.
- Strict VALID > TRANSITION > INVALID correlation ordering occurred in 17/20 runs.

The absence of strict ordering in every finite sample is not treated as generator
failure because the TRANSITION regime is deliberately non-stationary and noisy.

The calibrated Stable Momentum Driver parameters are now frozen and should not
be further optimized against downstream benchmark results.

The signal threshold was not selected through this calibration procedure.

It is fixed independently at zero to preserve a simple and interpretable binary
representation of the observable momentum belief.

---

## 11. Validation Requirements

Before the benchmark generator implementation is considered final, it must pass
the following validation checks.

### Structural Validation

- Exactly 2000 observations are generated.
- Required dataset fields are present.
- Regime boundaries match the frozen schedule.
- Warm-up behavior is handled correctly.
- No unexpected NaN or infinite values occur.

### Temporal Validation

- Momentum uses only information available at time t.
- Signal uses only Momentum_t available at time t.
- Signal follows exactly the frozen zero-threshold rule.
- Return represents the subsequent t to t+1 realization.
- The next row's price is consistent with the previous row's price and return.
- No look-ahead leakage is present.

### Signal Validation

For every observation after warm-up:

- if Momentum_t > 0, Signal_t must equal 1;
- if Momentum_t <= 0, Signal_t must equal 0.

The validation procedure must verify exact agreement between momentum_20d and
signal.

The signal threshold must not be adjusted based on these validation results.

### Dynamic Validation

- Both positive and negative momentum states occur during VALID.
- The latent driver does not remain persistently saturated.
- The simulated price process remains finite and dynamically stable.
- The VALID regime retains detectable positive momentum predictive information.
- Predictive strength weakens on average through TRANSITION.
- Momentum predictive information is approximately zero in INVALID.

The validation objective is falsification of the frozen generator design, not
parameter optimization.

A failed validation check should trigger investigation of implementation errors
or an explicit research-design revision.

It must not trigger undocumented parameter tuning.

### Reproducibility Validation

Running:

python src/market_generator.py

with the same frozen configuration and random seed must reproduce the same dataset.

---

## 12. Implementation Freeze Rule

Once the generator passes the frozen validation requirements, its scientific
mechanism, calibrated parameters, and signal rule are considered fixed for the
benchmark.

Subsequent AI benchmark results must not be used as justification for tuning the
synthetic market generator.

Any future change to:

- momentum definition
- signal definition
- signal threshold
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

The current implementation must follow the causal sequence:

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

The frozen equations are:

Momentum_t = Price_t / Price_(t-20) - 1

Signal_t = 1 if Momentum_t > 0, otherwise 0

Driver_t = tanh(Momentum_t / 0.10)

Return_(t+1) = beta_t * Driver_t + epsilon_t

epsilon_t ~ N(0, 0.01)

Price_(t+1) = Price_t * (1 + Return_(t+1))

with:

VALID:

beta = 0.005

TRANSITION:

beta decreases linearly from 0.005 to 0

INVALID:

beta = 0

The signal threshold is fixed at zero.

The signal rule must not be calibrated or optimized against downstream AI
benchmark outcomes.

This specification supersedes all earlier alpha-based, direct-momentum, and
clipped-momentum generator implementations.