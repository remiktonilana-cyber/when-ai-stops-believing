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

---

## 3. Core Causal Flow

At time t, the generator follows the causal sequence:

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

The observable momentum variable and the internal return-generation driver are
deliberately separated.

Momentum_t and Signal_t are AI-visible.

Driver_t is latent and internal to the simulator.

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
- output location.

The configuration layer must provide a single source of truth for numerical
simulation settings.

Frozen core values include:

- total simulation days: 2000
- initial price: 100
- momentum lookback: 20 periods
- transformation scale: 0.10
- VALID beta: 0.005
- TRANSITION beta: linear decay from 0.005 to 0
- INVALID beta: 0
- noise standard deviation: 0.01
- signal rule: 1 if Momentum_t > 0, otherwise 0

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

The first 20 observations require warm-up handling because 20 periods of price
history are required.

The signal is derived exclusively from observable Momentum_t using the fixed
rule:

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

---

### 4.5 Stable Momentum Driver

Purpose:

Transform observable cumulative momentum into a bounded latent variable for
stable return generation.

Internal transformation:

Driver_t = tanh(Momentum_t / 0.10)

The latent driver:

- preserves the sign of momentum;
- limits extreme feedback magnitude;
- remains internal to the simulator;
- is not exported to the benchmark dataset.

This component exists because earlier direct momentum-return feedback produced
unstable recursive price dynamics.

---

### 4.6 Return Generator

Purpose:

Generate the realized next-period market return.

Function:

generate_return(momentum, beta)

Input:

- observable Momentum_t
- regime-dependent beta_t

Internal computation:

Driver_t = tanh(Momentum_t / 0.10)

epsilon_t ~ N(0, 0.01)

Return_(t+1) = beta_t * Driver_t + epsilon_t

Output:

- realized next-period return

The function must not use future market information.

The latent driver should remain internal to this computation unless required
internally for validation.

It must not be added to the exported AI-visible schema.

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

The row semantics are:

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

---

## 5. Execution Flow

The generator follows a sequential causal simulation process.

### Step 1: Load Configuration

Load frozen parameters and reproducibility settings.

This includes:

- simulation length;
- initial price;
- momentum lookback;
- regime boundaries;
- beta schedule;
- transformation scale;
- noise standard deviation;
- random seed;
- fixed signal rule.

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

---

### Step 3: Begin Simulation Loop

For each simulation day t:

1. determine the current hidden regime using get_regime(day);

2. determine beta_t using calculate_beta(day, regime);

3. calculate observable features from information available at time t;

4. calculate Momentum_t from current and historical prices;

5. derive the observable signal using the fixed rule:

   Signal_t = 1 if Momentum_t > 0, otherwise 0;

6. internally transform momentum into:

   Driver_t = tanh(Momentum_t / 0.10);

7. generate:

   Return_(t+1) = beta_t * Driver_t + epsilon_t;

8. record the current time-t observation together with Return_(t+1);

9. update the price using:

   Price_(t+1) = Price_t * (1 + Return_(t+1));

10. append Price_(t+1) to the price history;

11. continue to the next simulation period.

This order is mandatory.

Features must be constructed before the return being predicted is realized.

---

## 6. Temporal Causality Constraint

The generator must preserve the following sequence:

Known information at time t

        ↓

Feature construction

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

---

## 7. Function Specification

### load_config()

Purpose:

Initialize frozen experiment parameters.

Input:

None.

Output:

Configuration object.

The configuration should include all numerical parameters required for
reproducible generation.

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

---

### generate_return(momentum, beta)

Purpose:

Generate the realized next-period return.

Input:

- Momentum_t
- beta_t

Internal computation:

Driver_t = tanh(Momentum_t / 0.10)

Return_(t+1) = beta_t * Driver_t + epsilon_t

where:

epsilon_t ~ N(0, 0.01)

Output:

- Return_(t+1)

The driver is internal and should not be exposed as a benchmark feature.

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

---

### calculate_features(price_history)

Purpose:

Generate AI-observable features from current and historical information.

Input:

- price history available through time t

Output:

- momentum_20d
- signal

Momentum must be calculated as:

Momentum_t = Price_t / Price_(t-20) - 1

The signal must be generated using:

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

### Hidden Ground Truth

The following must remain hidden:

- regime

### Internal Simulation State

The following is used internally but is not an AI-visible benchmark variable:

- Driver_t

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

Reproducibility is required so that AI systems can be evaluated under identical
evidence streams.

---

## 10. Validation Interface

The architecture must support independent validation of the generated market.

Validation should be able to inspect:

- regime boundaries;
- momentum distributions;
- signal frequencies;
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
- downstream benchmark-dependent tuning.

The purpose of the generator is not to reproduce full market complexity.

Its purpose is to create a controlled structural-change environment with known
ground truth.

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

Momentum_t

        ↓

Signal_t

        ↓

Driver_t = tanh(Momentum_t / 0.10)

beta_t + Driver_t + Noise

        ↓

Return_(t+1)

        ↓

Record time-t observation

        ↓

Price_(t+1)

        ↓

Next simulation period

The frozen structural equations are:

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

The signal threshold is fixed at zero and must not be calibrated or optimized
against downstream AI benchmark outcomes.

This architecture supersedes all earlier direct-alpha and clipped-momentum
generator designs.