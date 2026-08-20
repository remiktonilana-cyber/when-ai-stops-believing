# Synthetic Market Design

## 1. Objective

This synthetic market environment is designed to evaluate whether AI systems can recognize when a previously profitable market belief becomes invalid.

The goal is not to predict future returns, but to create a controlled environment where the true moment of structural change is known.

## 2. Market Rule

The benchmark uses a momentum-based market belief.

The initial assumption is:

Assets that have performed strongly in the recent past are more likely to continue performing well in the near future.

During the first stage, this relationship is intentionally designed to be profitable.

The experiment then introduces a structural change where the relationship gradually weakens and eventually disappears.

## 3. Regime Structure

The synthetic market consists of three regimes:

### Regime 1: Momentum Works

Duration: 1000 trading days

The momentum relationship is valid and generates positive expected returns.

### Regime 2: Transition Period

Duration: 300 trading days

The momentum advantage gradually decreases until the previous relationship becomes unreliable.

### Regime 3: Momentum Dies

Duration: 700 trading days

The original momentum relationship no longer provides predictive value.