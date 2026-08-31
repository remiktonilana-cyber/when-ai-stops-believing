# Generator Architecture

## 1. Objective

The purpose of the market generator is to create a reproducible synthetic
environment for evaluating AI belief revision under structural change.

The generator simulates a market in which a previously predictive relationship:

- exists during a VALID regime;
- weakens gradually during a TRANSITION regime; and
- disappears during an INVALID regime.

The system is not designed to forecast real financial markets.

It is a controlled experimental environment in which the true data-generating
mechanism and the timing of structural change are known to the researcher but
hidden from the AI system being evaluated.

The architecture must therefore satisfy four core requirements:

1. reproducibility;
2. temporal causality;
3. separation between observable variables and hidden ground truth; and
4. dynamic stability of the simulated market process.

---

## 2. System Architecture Overview

The generator is organized as a modular simulation pipeline.

The current architecture is:

Configuration Layer

        ↓

Regime Controller

        ↓

Beta Controller

        ↓

Feature Calculator

        ↓

Stable Momentum Driver

        ↓

Return Generator

        ↓

Price Updater

        ↓

Observation Recorder

        ↓

Data Exporter

Each component has a clearly defined responsibility.

The architecture is intentionally simple so that the synthetic environment
remains interpretable and auditable.

The first 20 observations are treated as an explicit initialization period.

During this warm-up period:

- the 20-period observable momentum feature is unavailable;
- the observable signal is unavailable;
- the internal momentum driver is fixed at 0;
- returns are generated from Gaussian noise only.

This rule provides sufficient price history for the first valid 20-period
momentum observation without assigning an artificial momentum state to periods
for which the feature cannot yet be computed.

---

## 3. Core Causal Flow

For Day 20 onward, at time t the generator follows the causal sequence:

Price history available at time t

        ↓

Momentum_t

        ↓

Signal_t

        ↓

Driver_t = tanh(Momentum_t / 0.10)

        ↓

beta_t determined by hidden regime

        ↓

Return_(t+1)

        ↓

Price_(t+1)

The formal relationships are:

Momentum_t = Price_t / Price_(t-20) - 1

Signal_t = 1 if Momentum_t > 0, otherwise 0

Driver_t = tanh(Momentum_t / 0.10)

Return_(t+1) = beta_t * Driver_t + epsilon_t

epsilon_t ~ N(0, 0.01)

Price_(t+1) = Price_t * (1 + Return_(t+1))

During Day 0-19, the causal flow is:

Price_t

        ↓

Momentum_t unavailable

        ↓

Signal_t unavailable

        ↓

Driver_t = 0

        ↓

beta_t determined by hidden regime

        ↓

Return_(t+1) = epsilon_t

        ↓

Price_(t+1)

Thus, during warm-up:

Momentum_t = missing

Signal_t = missing

Driver_t = 0

Return_(t+1) = epsilon_t

The observable momentum variable and the internal return-generation driver are
deliberately separated.

Momentum_t and Signal_t are AI-visible once they become computable.

Driver_t is latent and internal to the simulator.

Missing Momentum_t and Signal_t values during Day 0-19 represent unavailable
information, not zero or negative momentum.

---

## 4. Component Design

### 4.1 Configuration Layer

Purpose:

Centralize all frozen simulation parameters and reproducibility settings.

Responsibilities include:

- total simulation length;
- initial price;
- momentum lookback;
- regime boundaries;
- momentum transformation scale;
- beta schedule;
- noise standard deviation;
- random seed;
- fixed signal rule;
- warm-up length;
- warm-up driver rule;
- output location.

The configuration layer must provide a single source of truth for numerical
simulation settings.

Frozen core values include:

- total simulation days: 2000
- initial price: 100
- momentum lookback: 20 periods
- warm-up period: Day 0-19
- transformation scale: 0.10
- VALID beta: 0.005
- TRANSITION beta: linear decay from 0.005 to 0
- INVALID beta: 0
- noise standard deviation: 0.01
- signal rule after warm-up: 1 if Momentum_t > 0, otherwise 0
- warm-up momentum: missing
- warm-up signal: missing
- warm-up internal driver: 0

The warm-up convention is structural rather than calibrated.

It must not be modified in response to benchmark performance.

---

### 4.2 Regime Controller

Purpose:

Determine the hidden market regime for the current simulation day.

Function:

get_regime(day)

Input:

- simulation day index

Output:

- VALID
- TRANSITION
- INVALID

Regime schedule:

VALID:

- Day 0-999

TRANSITION:

- Day 1000-1299

INVALID:

- Day 1300-1999

The regime label is ground truth.

It must not be exposed to the AI system during benchmark evaluation.

Day 0-19 remain part of the VALID regime.

The warm-up convention changes only whether the momentum mechanism is active;
it does not alter the hidden regime schedule.

---

### 4.3 Beta Controller

Purpose:

Determine the strength of the momentum relationship under the current hidden
regime.

Function:

calculate_beta(day, regime)

Input:

- day index
- current hidden regime

Output:

- beta value

Behavior:

VALID:

beta = 0.005

TRANSITION:

beta decreases linearly from 0.005 to 0

INVALID:

beta = 0

The beta schedule defines the structural lifecycle of the momentum belief.

During Day 0-19, beta remains 0.005 because those observations belong to VALID.

However, the warm-up internal driver equals 0, so the deterministic momentum
contribution to return is also 0.

---

### 4.4 Feature Calculator

Purpose:

Construct observable market features using only information available at time t.

Function:

calculate_features(price_history)

Input:

- historical prices available up to time t

Output:

- momentum_20d
- signal

Observable momentum is defined as:

Momentum_t = Price_t / Price_(t-20) - 1

A complete 20-period price history is required before this quantity can be
computed.

Therefore, for Day 0-19:

momentum_20d = missing

signal = missing

These missing values are intentional.

They indicate that insufficient observable price history exists to evaluate the
momentum belief.

They must not be converted into:

momentum_20d = 0

or:

signal = 0

because either representation would incorrectly introduce an economic state
that has not actually been observed.

From Day 20 onward, the signal is derived exclusively from observable Momentum_t
using the fixed rule:

Signal_t = 1 if Momentum_t > 0

Signal_t = 0 otherwise

The zero threshold is intentionally fixed rather than calibrated.

It provides a transparent binary representation of the momentum belief and is
not optimized for strategy performance or benchmark separation.

The signal must not depend on:

- future returns;
- future prices;
- hidden regime;
- latent driver;
- downstream AI benchmark performance.

No missing momentum or signal values are permitted after Day 19.

---

### 4.5 Stable Momentum Driver

Purpose:

Transform observable cumulative momentum into a bounded latent variable for
stable return generation.

After warm-up, the internal transformation is:

Driver_t = tanh(Momentum_t / 0.10)

The latent driver:

- preserves the sign of momentum;
- limits extreme feedback magnitude;
- remains internal to the simulator;
- is not exported to the benchmark dataset.

During Day 0-19:

Driver_t = 0

This value is an initialization convention.

It does not mean:

Momentum_t = 0

and it must not be exposed to the AI system as an observable market state.

Setting Driver_t to 0 during warm-up ensures that unavailable momentum
information does not influence return generation.

This component exists because earlier direct momentum-return feedback produced
unstable recursive price dynamics.

---

### 4.6 Return Generator

Purpose:

Generate the realized next-period market return.

Function:

generate_return(momentum, beta)

Input:

- observable Momentum_t, or missing during warm-up
- regime-dependent beta_t

After warm-up, internal computation is:

Driver_t = tanh(Momentum_t / 0.10)

epsilon_t ~ N(0, 0.01)

Return_(t+1) = beta_t * Driver_t + epsilon_t

During Day 0-19:

Momentum_t = missing

Driver_t = 0

therefore:

Return_(t+1) = epsilon_t

The function must explicitly recognize unavailable warm-up momentum and use the
frozen zero-driver convention rather than attempting to apply tanh to a missing
value.

Output:

- realized next-period return

The function must not use future market information.

The latent driver should remain internal to this computation unless required
internally for validation.

It must not be added to the exported AI-visible schema.

The return output itself must always be finite.

---

### 4.7 Price Updater

Purpose:

Update the synthetic asset price after the next-period return has been
generated.

Function:

update_price(previous_price, return_value)

Input:

- Price_t
- Return_(t+1)

Output:

- Price_(t+1)

Relationship:

Price_(t+1) = Price_t * (1 + Return_(t+1))

The updated price becomes part of the information state available in the next
simulation period.

This rule applies identically during warm-up and after warm-up.

The price must remain finite and positive throughout the simulation.

---

### 4.8 Observation Recorder

Purpose:

Construct each dataset row according to the frozen temporal alignment
specification.

Each row represents:

- observable market state at time t;
- subsequent realized return from t to t+1;
- hidden regime governing that return.

The row should contain:

- experiment_id
- date
- price
- return
- volume
- momentum_20d
- signal
- regime

For Day 20 onward, the row semantics are:

price:

Price_t

momentum_20d:

Momentum_t

signal:

Signal_t = 1 if Momentum_t > 0, otherwise 0

return:

Return_(t+1)

regime:

hidden regime governing Return_(t+1)

For Day 0-19, the row semantics are:

price:

Price_t

momentum_20d:

missing

signal:

missing

return:

epsilon_t

regime:

VALID

The warm-up missing values are intentional observable-data missingness.

They must not be replaced with zero merely for storage convenience.

This alignment must remain fixed throughout the benchmark.

---

### 4.9 Data Exporter

Purpose:

Export generated simulation records into the benchmark dataset.

Function:

save_dataset(data)

Input:

- completed simulation records

Output:

data/synthetic_market.csv

The exported schema must contain exactly:

- experiment_id
- date
- price
- return
- volume
- momentum_20d
- signal
- regime

No latent driver field should be exported.

The exporter must preserve the intentional missing values in momentum_20d and
signal during Day 0-19.

No other unexpected missing numeric values should be introduced during export.

---

## 5. Execution Flow

The generator follows a sequential causal simulation process.

### Step 1: Load Configuration

Load frozen parameters and reproducibility settings.

This includes:

- simulation length;
- initial price;
- momentum lookback;
- warm-up period;
- regime boundaries;
- beta schedule;
- transformation scale;
- noise standard deviation;
- random seed;
- fixed signal rule;
- warm-up driver rule.

---

### Step 2: Initialize Market State

Initialize:

- starting price;
- price history;
- simulation records;
- random number generator;
- experiment identifier.

The initial price is:

Price_0 = 100

At initialization, the 20-period momentum feature is not yet available.

---

### Step 3: Begin Simulation Loop

For each simulation day t:

1. determine the current hidden regime using get_regime(day);

2. determine beta_t using calculate_beta(day, regime);

3. obtain Price_t from the currently available price history;

4. calculate observable features using only information available at time t;

5. if Day 0-19:

   - set Momentum_t to missing;
   - set Signal_t to missing;
   - set internal Driver_t to 0;

6. if Day 20 onward:

   calculate:

   Momentum_t = Price_t / Price_(t-20) - 1

   derive:

   Signal_t = 1 if Momentum_t > 0, otherwise 0

   internally calculate:

   Driver_t = tanh(Momentum_t / 0.10)

7. generate noise:

   epsilon_t ~ N(0, 0.01)

8. generate:

   Return_(t+1) = beta_t * Driver_t + epsilon_t

9. record the current time-t observation together with Return_(t+1);

10. update the price using:

    Price_(t+1) = Price_t * (1 + Return_(t+1));

11. append Price_(t+1) to the price history;

12. continue to the next simulation period.

This order is mandatory.

Features must be constructed before the return being predicted is realized.

During warm-up, feature unavailability must be resolved by the explicit
zero-driver rule rather than by imputing a momentum or signal value.

---

## 6. Temporal Causality Constraint

The generator must preserve the following sequence:

Known information at time t

        ↓

Feature construction or explicit warm-up missingness

        ↓

Latent return-generation mechanism

        ↓

Return from t to t+1

        ↓

New price at t+1

The generator must never perform:

Return_(t+1)

        ↓

Feature_t

or:

Price_(t+1)

        ↓

Momentum_t

Such ordering would introduce look-ahead leakage.

The benchmark requires strict feature-target separation.

Warm-up does not create an exception to this rule.

During Day 0-19, unavailable momentum is explicitly represented as missing
rather than being reconstructed from future prices.

---

## 7. Function Specification

### load_config()

Purpose:

Initialize frozen experiment parameters.

Input:

None.

Output:

Configuration object.

The configuration should include all numerical and structural parameters required
for reproducible generation.

Required frozen settings include:

- simulation_days = 2000
- initial_price = 100
- momentum_window = 20
- momentum_scale = 0.10
- valid_beta = 0.005
- noise_std = 0.01
- warm-up period = first 20 observations
- signal threshold = 0

---

### get_regime(day)

Purpose:

Return the hidden structural regime for a given simulation day.

Input:

- day index

Output:

- VALID
- TRANSITION
- INVALID

Rules:

Day 0-999:

VALID

Day 1000-1299:

TRANSITION

Day 1300-1999:

INVALID

---

### calculate_beta(day, regime)

Purpose:

Determine the current structural strength of the momentum relationship.

Input:

- day index
- hidden regime

Output:

- beta_t

Rules:

VALID:

beta = 0.005

TRANSITION:

beta decreases linearly from 0.005 to 0

INVALID:

beta = 0

Warm-up does not modify beta.

Day 0-19 retain:

beta = 0.005

but the deterministic return component remains zero because:

Driver_t = 0

---

### generate_return(momentum, beta)

Purpose:

Generate the realized next-period return.

Input:

- Momentum_t
- beta_t

For Day 20 onward:

Driver_t = tanh(Momentum_t / 0.10)

Return_(t+1) = beta_t * Driver_t + epsilon_t

where:

epsilon_t ~ N(0, 0.01)

For Day 0-19, when Momentum_t is missing:

Driver_t = 0

and:

Return_(t+1) = epsilon_t

Output:

- Return_(t+1)

The driver is internal and should not be exposed as a benchmark feature.

The implementation must not replace missing warm-up momentum with observable
zero momentum.

The zero applies only to the latent Driver_t.

---

### update_price(previous_price, return_value)

Purpose:

Generate the next observable price.

Input:

- Price_t
- Return_(t+1)

Output:

- Price_(t+1)

Relationship:

Price_(t+1) = Price_t * (1 + Return_(t+1))

The result must remain finite and positive.

---

### calculate_features(price_history)

Purpose:

Generate AI-observable features from current and historical information.

Input:

- price history available through time t

Output:

- momentum_20d
- signal

If fewer than 21 price observations are available, meaning Day 0-19:

momentum_20d = missing

signal = missing

The function must not return signal = 0 merely because momentum cannot yet be
computed.

Once sufficient history exists:

Momentum_t = Price_t / Price_(t-20) - 1

The signal must then be generated using:

Signal_t = 1 if Momentum_t > 0

Signal_t = 0 otherwise

The signal threshold is fixed at zero.

It must not be calibrated or optimized against downstream benchmark outcomes.

No future information may be used.

---

### save_dataset(data)

Purpose:

Export generated observations.

Input:

- simulation records

Output:

data/synthetic_market.csv

The output must preserve intentional warm-up missingness.

The only expected missing values are:

- momentum_20d on Day 0-19;
- signal on Day 0-19.

No missing values are expected in:

- price;
- return;
- volume;
- regime;
- experiment_id.

---

## 8. Hidden and Observable State Separation

The architecture distinguishes three categories of state.

### AI-Visible State

Potential benchmark inputs include:

- date
- price
- return history
- volume
- momentum_20d
- signal

Momentum and signal are unavailable during Day 0-19 and become observable from
Day 20 onward.

### Hidden Ground Truth

The following must remain hidden:

- regime

### Internal Simulation State

The following is used internally but is not an AI-visible benchmark variable:

- Driver_t

During warm-up, Driver_t = 0.

This internal zero must not be interpreted or exported as observable zero
momentum.

The distinction is critical.

The AI must infer structural deterioration from observable evidence rather than
being given the mechanism directly.

---

## 9. Reproducibility Requirements

The same:

- configuration;
- random seed;
- generator implementation;

must produce the same synthetic dataset.

Randomness must therefore be controlled explicitly.

The generator should not depend on:

- external APIs;
- live financial data;
- system clock state;
- nondeterministic external services.

Warm-up handling must also be deterministic.

For the same input configuration and random seed, Day 0-19 must always produce:

- missing momentum_20d;
- missing signal;
- Driver_t = 0;
- returns determined solely by the seeded Gaussian noise sequence.

Reproducibility is required so that AI systems can be evaluated under identical
evidence streams.

---

## 10. Validation Interface

The architecture must support independent validation of the generated market.

Validation should be able to inspect:

- total row count;
- regime boundaries;
- warm-up missingness;
- post-warm-up feature completeness;
- momentum distributions;
- signal frequencies;
- momentum-signal consistency;
- momentum-return correlation by regime;
- positive and negative momentum frequency;
- latent driver saturation;
- price range;
- numerical finiteness;
- temporal alignment;
- price-return consistency.

Validation code may inspect hidden and internal state where necessary.

AI benchmark inputs may not.

The validation layer is conceptually separate from the AI evaluation layer.

### Warm-up Validation

Validation must confirm exactly:

For Day 0-19:

- momentum_20d is missing;
- signal is missing;
- internal Driver_t equals 0;
- returns remain finite;
- returns contain no deterministic momentum contribution.

For Day 20 onward:

- momentum_20d is fully defined;
- signal is fully defined;
- no warm-up missingness remains.

The presence of missing momentum_20d and signal during Day 0-19 is expected
behavior.

Missing values in those fields after Day 19 are errors.

### Signal Validation

For every observation from Day 20 onward:

if Momentum_t > 0:

Signal_t = 1

if Momentum_t <= 0:

Signal_t = 0

Exact agreement is required.

The threshold must not be altered in response to validation outcomes.

### Numerical Validation

The generator must contain no NaN or infinite values in:

- price;
- return;
- volume.

The only permitted missing values in the exported dataset are:

- momentum_20d during Day 0-19;
- signal during Day 0-19.

---

## 11. Architectural Constraints

The generator must remain deliberately minimal.

It should not introduce:

- machine learning models;
- adaptive trading agents;
- endogenous AI behavior;
- additional regime predictors;
- unplanned economic variables;
- hidden parameter optimization;
- downstream benchmark-dependent tuning;
- warm-up feature imputation;
- warm-up signal substitution.

The purpose of the generator is not to reproduce full market complexity.

Its purpose is to create a controlled structural-change environment with known
ground truth.

The warm-up rule exists only to initialize the required price history.

It must not become an additional source of synthetic economic structure.

---

## 12. Historical Architecture Revision

Earlier versions of the architecture used a direct momentum-return mechanism of
the general form:

Return = alpha * Momentum + Noise

and functions such as:

calculate_alpha(day, regime)

generate_return(momentum, alpha)

That architecture is superseded.

Validation showed that direct cumulative momentum feedback, including a later
clipped-momentum attempt, could create persistent recursive attractors.

The current architecture therefore replaces the old alpha-based mechanism with:

calculate_beta(day, regime)

and:

Driver_t = tanh(Momentum_t / 0.10)

Return_(t+1) = beta_t * Driver_t + epsilon_t

The old alpha architecture is retained only as methodological history and must
not be implemented in the current benchmark generator.

A later documentation clarification explicitly defined the warm-up boundary
condition:

- unavailable observable momentum remains missing;
- unavailable observable signal remains missing;
- the internal driver is set to 0;
- warm-up returns are generated from noise only.

This clarification does not alter the calibrated post-warm-up Stable Momentum
Driver mechanism.

---

## 13. Current Source of Truth

The active generator architecture is:

Configuration

        ↓

Hidden Regime

        ↓

beta_t

Price History

        ↓

Feature availability check

        ↓

For Day 0-19:

Momentum_t = missing

Signal_t = missing

Driver_t = 0

For Day 20 onward:

Momentum_t = Price_t / Price_(t-20) - 1

        ↓

Signal_t = 1 if Momentum_t > 0, otherwise 0

        ↓

Driver_t = tanh(Momentum_t / 0.10)

Then for every day:

beta_t + Driver_t + Noise

        ↓

Return_(t+1)

        ↓

Record time-t observation

        ↓

Price_(t+1)

        ↓

Next simulation period

The frozen structural equations after warm-up are:

Momentum_t = Price_t / Price_(t-20) - 1

Signal_t = 1 if Momentum_t > 0, otherwise 0

Driver_t = tanh(Momentum_t / 0.10)

Return_(t+1) = beta_t * Driver_t + epsilon_t

epsilon_t ~ N(0, 0.01)

Price_(t+1) = Price_t * (1 + Return_(t+1))

The frozen warm-up equations for Day 0-19 are:

Momentum_t = missing

Signal_t = missing

Driver_t = 0

Return_(t+1) = epsilon_t

epsilon_t ~ N(0, 0.01)

with:

VALID:

Day 0-999

beta = 0.005

TRANSITION:

Day 1000-1299

beta decreases linearly from 0.005 to 0

INVALID:

Day 1300-1999

beta = 0

The signal threshold is fixed at zero and applies from Day 20 onward.

It must not be calibrated or optimized against downstream AI benchmark
outcomes.

The warm-up period does not change regime membership.

Day 0-19 remain VALID but contain no deterministic momentum contribution because
the internal driver is explicitly 0.

The only expected missing values in the exported dataset are:

- momentum_20d during Day 0-19;
- signal during Day 0-19.

This architecture supersedes all earlier direct-alpha and clipped-momentum
generator designs.