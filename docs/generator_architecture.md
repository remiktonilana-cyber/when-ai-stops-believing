# Generator Architecture

## 1. Objective

The purpose of the market generator is to create a reproducible synthetic environment for evaluating AI belief revision capabilities.

The generator should simulate a market where a previously profitable relationship can emerge, weaken, and eventually disappear.

The system is not designed to predict financial returns. Instead, it creates a controlled environment where the true timing of structural change is known and AI adaptation can be measured.

## 2. System Architecture Overview

The generator is designed as a modular synthetic environment engine.

The system consists of five major components:

Configuration Layer
        ↓
Regime Controller
        ↓
Market Simulator
        ↓
Feature Calculator
        ↓
Data Exporter

Each component has a clearly defined responsibility to ensure reproducibility, interpretability, and future extensibility.

### Configuration Layer

Manages experiment parameters, including initial conditions, simulation length, and signal parameters.

### Regime Controller

Determines the current market state and controls the transition between VALID, TRANSITION, and INVALID regimes.

### Market Simulator

Generates market returns according to the current regime and the relationship between momentum signals and future returns.

### Feature Calculator

Transforms raw market observations into features visible to AI systems, such as momentum indicators and trading signals.

### Data Exporter

Stores generated observations into a structured dataset for downstream AI evaluation.

## 3. Module Design

### Configuration Layer

Purpose:
Manage experiment parameters and simulation settings.

Main responsibility:
Provide centralized control over simulation parameters.

---

### Regime Controller

Purpose:
Determine the current market regime.

Function:
get_regime(day)

Input:
Trading day index.

Output:
VALID, TRANSITION, or INVALID.

---

### Market Simulator

Purpose:
Generate synthetic market returns.

Function:
generate_return()

Input:
Momentum signal, regime-dependent alpha, and random noise.

Output:
Daily return.

Core mechanism:

Return = alpha × Momentum + Noise

---

### Feature Calculator

Purpose:
Generate observable variables available to AI systems.

Function:
calculate_features()

Input:
Price history.

Output:
Momentum indicators and trading signals.

---

### Data Exporter

Purpose:
Store generated market observations.

Function:
save_dataset()

Output:
synthetic_market.csv

## 4. Execution Flow

The generator follows a sequential simulation pipeline.

### Step 1: Initialize Configuration

Load experiment parameters including simulation length, initial price, and signal settings.

### Step 2: Initialize Market State

Create the initial market environment and starting price.

### Step 3: Daily Simulation Loop

For each trading day:

1. Determine the current market regime.
2. Calculate the regime-dependent momentum strength (alpha).
3. Generate daily returns based on momentum effects and noise.
4. Update asset price.
5. Calculate observable features.
6. Store the daily observation.

### Step 4: Export Dataset

After simulation completion, export all observations into:

data/synthetic_market.csv

The execution flow ensures that the generated environment is reproducible, interpretable, and consistent with the predefined market belief lifecycle.

## 5. Function Specification

### load_config()

Purpose:
Initialize experiment parameters.

Input:
None.

Output:
Configuration object.


### get_regime(day)

Purpose:
Determine the current market regime.

Input:
Trading day index.

Output:
VALID, TRANSITION, or INVALID.


### calculate_alpha(day, regime)

Purpose:
Determine the strength of the historical belief.

Input:
Day index and market regime.

Output:
Alpha value.


### generate_return(momentum, alpha)

Purpose:
Generate synthetic returns.

Input:
Momentum signal and alpha.

Output:
Daily return.


### update_price(previous_price, return_value)

Purpose:
Update asset price.

Input:
Previous price and daily return.

Output:
New price.


### calculate_features(price_history)

Purpose:
Generate AI-observable features.

Input:
Historical prices.

Output:
Momentum indicator and trading signal.


### save_dataset(data)

Purpose:
Export generated observations.

Input:
Simulation records.

Output:
synthetic_market.csv.