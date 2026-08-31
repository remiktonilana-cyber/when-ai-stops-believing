# Synthetic Market Design

## 1. Objective

This synthetic market environment is designed to evaluate whether AI systems
can recognize when a previously predictive market belief becomes invalid.

The central research problem is not whether an AI can maximize trading returns.

It is whether an AI can revise a previously justified belief when the underlying
relationship changes.

The benchmark therefore creates a controlled environment in which:

- a momentum relationship initially contains predictive information;
- that relationship gradually weakens;
- the relationship eventually disappears;
- the true structural regime is known to the researcher;
- the true structural regime is hidden from the AI system.

The synthetic market is not intended to reproduce the full complexity of a real
financial market.

Its purpose is to isolate belief revision under structural change.

---

## 2. Market Belief

The benchmark studies a momentum-based market belief.

The tested belief is:

> Assets that have performed strongly in the recent past are more likely to
> continue performing well in the near future.

This belief is intentionally valid during the first part of the synthetic
environment.

Its predictive strength then gradually decreases and ultimately disappears.

The benchmark therefore creates a controlled belief lifecycle:

Valid belief

        ↓

Increasing contradictory evidence

        ↓

Structural deterioration

        ↓

Invalid belief

The AI system must infer this deterioration from observable evidence.

It is not told directly when the underlying market mechanism changes.

---

## 3. Regime Structure

The synthetic market contains 2000 simulated periods divided into three hidden
ground-truth regimes.

### 3.1 VALID

Period:

Day 0-999

During VALID, momentum contains stable positive predictive information about the
subsequent return.

The structural momentum coefficient is:

beta = 0.005

This regime establishes a belief that is initially justified by evidence.

---

### 3.2 TRANSITION

Period:

Day 1000-1299

During TRANSITION, the predictive strength of momentum gradually deteriorates.

beta decreases linearly from:

0.005 -> 0

This regime represents structural uncertainty.

The previously valid belief does not disappear instantaneously.

Instead, evidence supporting the belief becomes progressively weaker while
random variation may still produce temporary successes and failures.

This makes it possible to test whether an AI system can distinguish ordinary
noise from genuine structural deterioration.

---

### 3.3 INVALID

Period:

Day 1300-1999

During INVALID:

beta = 0

Momentum no longer contributes to the data-generating process for subsequent
returns.

The original momentum belief has therefore become structurally invalid.

Any apparent momentum success during this regime arises from noise rather than
from the original predictive mechanism.

---

## 4. Observable Momentum

The primary observable belief variable is classical 20-period price momentum.

It is defined as:

Momentum_t = Price_t / Price_(t-20) - 1

Equivalently:

Momentum_t = (Price_t - Price_(t-20)) / Price_(t-20)

Momentum_t uses only price information available at time t.

The first 20 observations require a warm-up period because a complete
20-period price history is not yet available.

Momentum_t is AI-visible.

It preserves the economic interpretation of the belief being tested while
remaining separate from the internal mechanism used to generate returns.

---

## 5. Signal Definition

The benchmark also provides a simple binary representation of the observable
momentum belief.

The frozen signal rule is:

Signal_t = 1 if Momentum_t > 0

Signal_t = 0 otherwise

The signal threshold is therefore fixed at zero.

The interpretation is:

- positive 20-period momentum -> active momentum signal;
- zero or negative 20-period momentum -> inactive momentum signal.

The zero threshold is intentionally not calibrated.

It is not selected to maximize trading performance, predictive correlation, or
separation between benchmark regimes.

Its purpose is to provide a simple and interpretable binary representation of
the momentum belief without introducing an additional optimized parameter.

Signal_t must be calculated using only information available at time t.

It must not depend on:

- future returns;
- future prices;
- hidden regime;
- the latent momentum driver;
- downstream AI benchmark performance.

---

## 6. Stable Momentum Driver

Observable momentum is not fed directly into the return equation.

Earlier generator designs showed that direct cumulative momentum-return feedback
could create unstable self-reinforcing price dynamics.

The benchmark therefore separates the observable economic feature from the
internal market-generating driver.

The latent driver is:

Driver_t = tanh(Momentum_t / 0.10)

The transformation:

- preserves the sign of momentum;
- bounds the internal driver;
- reduces unstable recursive feedback;
- preserves the observable classical momentum definition.

Driver_t is internal simulation state.

It must not be exposed to the AI system as a benchmark input.

---

## 7. Return-Generation Mechanism

The subsequent return is generated according to:

Return_(t+1) = beta_t * Driver_t + epsilon_t

where:

Driver_t = tanh(Momentum_t / 0.10)

and:

epsilon_t ~ N(0, 0.01)

The structural coefficient beta_t depends on the hidden regime.

### VALID

beta_t = 0.005

### TRANSITION

beta_t decreases linearly from 0.005 to 0.

### INVALID

beta_t = 0

The resulting lifecycle is therefore:

VALID:

Momentum contains detectable positive predictive information.

TRANSITION:

Momentum predictive strength progressively deteriorates.

INVALID:

Momentum no longer contributes to subsequent return generation.

---

## 8. Temporal Structure

The benchmark uses strict temporal alignment.

Each observation represents:

observable information at time t

        ↓

subsequent realized return from t to t+1

The causal sequence is:

Price history through time t

        ↓

Momentum_t

        ↓

Signal_t

        ↓

Internal Driver_t

        ↓

Return_(t+1)

        ↓

Price_(t+1)

The price update is:

Price_(t+1) = Price_t * (1 + Return_(t+1))

Momentum_t and Signal_t must therefore be calculated before Return_(t+1) is
realized.

No future information may be used in their construction.

The benchmark does not define a fixed multi-period trading holding rule as part
of the synthetic market generator.

The primary evidence relationship is:

Information at time t -> Return from t to t+1

Any later strategy-level or multi-period evaluation must be defined separately
from the market-generation mechanism.

---

## 9. Observable and Hidden Information

The benchmark distinguishes observable evidence from experimental ground truth.

### AI-Visible Market Information

Potential AI-visible variables include:

- date;
- price;
- historical returns;
- volume;
- momentum_20d;
- signal.

### Hidden Ground Truth

The following variable must remain hidden during AI evaluation:

- regime.

### Internal Simulation State

The following variable is used internally by the generator but must not be
provided as an AI-visible feature:

- Driver_t.

experiment_id is simulation metadata rather than an AI-visible market variable.

This separation ensures that the AI must infer structural deterioration from
evidence rather than receiving the answer directly.

---

## 10. Ground Truth

The synthetic environment contains a predefined structural ground truth.

### VALID

Day 0-999

Momentum contributes positively to subsequent return generation.

### TRANSITION

Day 1000-1299

The contribution of momentum progressively decreases.

### INVALID

Day 1300-1999

Momentum contributes nothing to subsequent return generation.

These labels are used for evaluation.

They are not shown to the AI system while it is making belief-revision
decisions.

The ground truth allows the researcher to measure when and how the AI updates
relative to the actual structural deterioration.

---

## 11. Expected AI Challenge

The central challenge is distinguishing temporary failure from structural
invalidation.

The benchmark creates two symmetric failure modes.

### 11.1 Over-Persistence

An AI system may continue believing in a previously successful relationship
after the underlying mechanism has disappeared.

This represents insufficient belief revision.

### 11.2 Over-Reaction

An AI system may abandon a genuinely valid relationship after a small amount of
negative evidence caused by noise.

This represents excessive sensitivity to temporary failure.

A strong adaptive system should avoid both extremes.

It should retain a belief while the evidence continues to justify it, while
also revising that belief when accumulated evidence indicates structural
deterioration.

---

## 12. Experimental Interpretation

The benchmark is fundamentally a belief-revision experiment rather than a
trading-strategy optimization experiment.

The momentum relationship provides the controlled belief.

The three regimes provide the structural lifecycle.

Noise creates ambiguous evidence.

The AI system's task is to determine whether observed failures represent:

- temporary stochastic variation;
- gradual weakening of the original relationship; or
- permanent structural invalidation.

The key object of measurement is therefore not simply realized profit.

It is the AI system's updating behavior under changing evidence.

---

## 13. Frozen Market Design

The current market design is frozen as:

Total simulation length:

2000 periods

Momentum:

Momentum_t = Price_t / Price_(t-20) - 1

Signal:

Signal_t = 1 if Momentum_t > 0, otherwise 0

Latent driver:

Driver_t = tanh(Momentum_t / 0.10)

Return:

Return_(t+1) = beta_t * Driver_t + epsilon_t

Noise:

epsilon_t ~ N(0, 0.01)

VALID:

Day 0-999

beta = 0.005

TRANSITION:

Day 1000-1299

beta decreases linearly from 0.005 to 0

INVALID:

Day 1300-1999

beta = 0

Temporal target:

Information at time t -> Return from t to t+1

The signal threshold is fixed at zero and is not a calibrated parameter.

The benchmark generator contains no fixed five-period holding rule.

Any earlier specification using:

- a 5% signal threshold;
- a fixed five-period holding period;
- direct alpha-based cumulative momentum feedback; or
- clipped cumulative momentum as the return-generation driver

is superseded by the current frozen design.

Any future change to these frozen market-design assumptions must be treated as
an explicit experimental design revision rather than an implementation
adjustment.