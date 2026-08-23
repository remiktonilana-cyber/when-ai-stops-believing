# Implementation Plan

## 1. Programming Environment

The synthetic market generator will be implemented using Python 3.

Python is selected due to its strong ecosystem for numerical simulation, data processing, and reproducible experiments.

---

## 2. Dependencies

The implementation requires:

- numpy
- pandas

numpy is used for stochastic noise generation and numerical operations.

pandas is used for dataset construction and CSV export.

---

## 3. File Structure

The implementation follows the project structure:

src/
└── market_generator.py

data/
└── synthetic_market.csv


The generator script is responsible for creating the synthetic dataset.

---

## 4. Execution Requirement

The generator should be executable with:

python src/market_generator.py

The execution should produce:

data/synthetic_market.csv

## 5. Output Requirement

The generated dataset must contain:

- experiment_id
- date
- price
- return
- volume
- momentum_20d
- signal
- regime

The regime variable is retained for evaluation purposes and should not be provided to AI systems during benchmark evaluation.

## 6. Codex Implementation Specification

The implementation should follow the predefined architecture and function specifications.

### Role

The coding agent acts as an implementation engineer responsible for translating the design into executable Python code.

### Context

The generator creates a controlled synthetic market environment for evaluating AI belief revision under changing market regimes.

### Constraints

The implementation should:

- Follow the defined modular architecture.
- Preserve the predefined mathematical relationships.
- Avoid introducing additional variables or machine learning models.
- Keep hidden regime information separated from AI-visible inputs.

### Required Functions

The implementation must include:

- load_config()
- get_regime(day)
- calculate_alpha(day, regime)
- generate_return(momentum, alpha)
- update_price(previous_price, return_value)
- calculate_features(price_history)
- save_dataset(data)

### Validation

The implementation should generate:

data/synthetic_market.csv

when executed with:

python src/market_generator.py

## 7. Default Configuration Parameters

The first implementation uses the following default simulation parameters:

| Parameter | Value |
|---|---|
| Total simulation days | 2000 |
| Initial price | 100 |
| Momentum lookback window | 20 days |
| VALID regime | Day 0-999 |
| TRANSITION regime | Day 1000-1299 |
| INVALID regime | Day 1300-1999 |
| Initial alpha | 0.5 |
| Transition alpha | Linear decay from 0.5 to 0 |
| Invalid alpha | 0 |
| Noise distribution | Normal distribution N(0,0.01) |

The first 20 observations are treated as a warm-up period because momentum requires historical data.

These parameters are explicitly defined to ensure reproducibility.