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

## 4. Signal Definition

The synthetic market uses a momentum signal to represent the market belief being evaluated.

### Momentum Signal

The momentum signal is defined as the cumulative return over the previous 20 trading days.

Formula:

Momentum_t = (P_t - P_(t-20)) / P_(t-20)

where P_t represents the current price and P_(t-20) represents the price 20 trading days earlier.

### Trading Rule

A positive momentum signal above 5% is considered a valid momentum opportunity.

The simulated strategy follows:

- If 20-day momentum > 5%, enter a position.
- Hold the position for 5 trading days.
- Evaluate subsequent returns.

### Parameter Choice

The selected parameters are designed to balance interpretability and realism:

- Lookback window: 20 trading days
- Signal threshold: 5%
- Holding period: 5 trading days

## 5. Ground Truth

The synthetic environment provides a predefined ground truth to identify when the momentum belief changes.

The market contains three labeled states:

### Regime 1: VALID

Period:
Day 0-999

The momentum relationship generates positive expected returns.

### Regime 2: TRANSITION

Period:
Day 1000-1299

The momentum advantage gradually decreases.

This period represents uncertainty, where the previous belief may still work temporarily but becomes increasingly unreliable.

### Regime 3: INVALID

Period:
Day 1300-1999

The momentum relationship no longer provides predictive value.

This represents the death of the original market belief.

The predefined labels allow evaluation of whether AI systems can correctly identify structural changes.