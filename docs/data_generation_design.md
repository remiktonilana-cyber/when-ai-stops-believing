# Data Generation Design

## 1. Objective

The purpose of the synthetic data generation process is to create a controlled market environment for evaluating AI belief revision.

Each variable is designed to support the research question: whether AI systems can distinguish temporary underperformance from permanent structural change.

## 2. Data Schema

The synthetic market dataset consists of three layers:

### 1. Observable Market Variables

Variables provided to AI systems during evaluation.

### 2. Hidden Ground Truth Variables

Variables used only for evaluation and not exposed to AI systems.

### 3. Experiment Metadata

Variables used to ensure reproducibility.

## 3. Dataset Fields

| Variable | Description | AI Visible |
|----------|-------------|------------|
| date | Trading day identifier | Yes |
| price | Synthetic asset price | Yes |
| return | Daily return | Yes |
| volume | Trading activity indicator | Yes |
| momentum_20d | 20-day momentum signal | Yes |
| signal | Trading rule indicator | Yes |
| regime | True market state label | No |

## 4. Variable Generation Logic

The synthetic market is generated through a regime-dependent return process.

The core return generation mechanism is:

Return_t = alpha_t * Momentum_t + noise_t

where:

- Momentum_t represents the 20-day momentum signal.
- alpha_t represents the strength of the momentum relationship.
- noise represents random market fluctuations.

### Price Generation

The asset price evolves according to:

Price_t = Price_(t-1) * (1 + Return_t)

### Regime-dependent Behavior

#### VALID Regime

During the valid regime, momentum has predictive power.

alpha remains positive, meaning stronger past performance increases expected future returns.

#### TRANSITION Regime

During the transition period, alpha gradually decreases.

The relationship between momentum and future returns becomes weaker.

#### INVALID Regime

During the invalid regime, alpha approaches zero or becomes negative.

The original momentum belief no longer provides predictive value.

### Signal Generation

The trading signal is generated from the momentum indicator:

If Momentum_20d > 5%, signal = 1.

Otherwise, signal = 0.

## 5. Data Validation

Before using the synthetic dataset for AI evaluation, the generated environment must be validated.

The validation process ensures that the simulated market follows the intended belief lifecycle.

### 1. Momentum Effect Validation

The relationship between momentum signals and future returns is measured during each regime.

Expected behavior:

- VALID regime: strong positive relationship.
- TRANSITION regime: weakening relationship.
- INVALID regime: no meaningful predictive relationship.

### 2. Regime Transition Validation

The dataset should demonstrate a gradual decrease in momentum effectiveness as the market moves from VALID to INVALID.

### 3. Ground Truth Validation

The predefined regime labels are compared with generated market behavior to ensure that the synthetic environment accurately represents the intended structural change.