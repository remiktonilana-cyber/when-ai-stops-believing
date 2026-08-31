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

The first 20 observations are treated as an initialization period required to
construct a valid 20-period momentum feature.

This warm-up period is part of the VALID regime but does not yet contain an
active momentum contribution because the momentum feature is not computable.

---

## 2. Market Belief

The benchmark studies a momentum-based market belief.

The tested belief is:

> Assets that have performed strongly in the recent past are more likely to
> continue performing well in the near future.

This belief is intentionally valid during the first part of the synthetic
environment once sufficient price history exists to evaluate it.

Its predictive strength then gradually decreases and ultimately disappears.

The benchmark therefore creates a controlled belief lifecycle:

Warm-up

        ↓

Valid observable momentum belief

        ↓

Increasing contradictory evidence

        ↓

Structural deterioration

        ↓

Invalid belief

The warm-up period is not itself a fourth structural regime.

It is an initialization condition inside VALID.

The AI system must infer structural deterioration from observable evidence.

It is not told directly when the underlying market mechanism changes.

---

## 3. Regime Structure

The synthetic market contains 2000 simulated periods divided into three hidden
ground-truth regimes.

### 3.1 VALID

Period:

Day 0-999

The structural momentum coefficient is:

beta = 0.005

Day 0-19 are the warm-up portion of VALID.

During these observations, a complete 20-period price history is not yet
available.

Therefore:

Momentum_t = missing

Signal_t = missing

Driver_t = 0

Return_(t+1) = epsilon_t

where:

epsilon_t ~ N(0, 0.01)

From Day 20 onward, VALID contains stable positive predictive information about
the subsequent return.

The warm-up period does not change the regime label or beta value.

Instead, the momentum contribution is temporarily inactive because the internal
driver is set to zero until observable momentum becomes computable.

This regime establishes a belief that becomes empirically observable and
initially justified by evidence from Day 20 onward.

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

A complete 20-period price history is required.

Therefore:

For Day 0-19:

Momentum_t = missing

For Day 20 onward:

Momentum_t = Price_t / Price_(t-20) - 1

The first fully defined momentum observation is:

Momentum_20 = Price_20 / Price_0 - 1

Warm-up momentum must not be set to zero.

It must not be estimated using future observations.

The missing value represents insufficient information rather than a market
state.

Momentum_t is AI-visible once it becomes available.

It preserves the economic interpretation of the belief being tested while
remaining separate from the internal mechanism used to generate returns.

---

## 5. Signal Definition

The benchmark also provides a simple binary representation of the observable
momentum belief.

During Day 0-19:

Signal_t = missing

because Momentum_t itself is unavailable.

From Day 20 onward, the frozen signal rule is:

Signal_t = 1 if Momentum_t > 0

Signal_t = 0 otherwise

The signal threshold is therefore fixed at zero.

The interpretation after warm-up is:

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

A missing warm-up signal must not be interpreted as:

Signal_t = 0

The distinction is structural:

missing signal

means the belief cannot yet be evaluated;

Signal_t = 0

means observable momentum exists and is zero or negative.

---

## 6. Stable Momentum Driver

Observable momentum is not fed directly into the return equation.

Earlier generator designs showed that direct cumulative momentum-return feedback
could create unstable self-reinforcing price dynamics.

The benchmark therefore separates the observable economic feature from the
internal market-generating driver.

After warm-up, the latent driver is:

Driver_t = tanh(Momentum_t / 0.10)

The transformation:

- preserves the sign of momentum;
- bounds the internal driver;
- reduces unstable recursive feedback;
- preserves the observable classical momentum definition.

During Day 0-19:

Driver_t = 0

This zero value is an internal initialization convention.

It does not imply:

Momentum_t = 0

and must not be exposed to the AI as an observable momentum state.

Driver_t is internal simulation state.

It must not be exposed to the AI system as a benchmark input.

---

## 7. Return-Generation Mechanism

The subsequent return is generated according to:

Return_(t+1) = beta_t * Driver_t + epsilon_t

where:

epsilon_t ~ N(0, 0.01)

The structural coefficient beta_t depends on the hidden regime.

### Warm-Up

For Day 0-19:

beta_t = 0.005

Driver_t = 0

therefore:

Return_(t+1) = epsilon_t

The warm-up price path is therefore generated from Gaussian noise only.

### VALID after Warm-Up

From Day 20 to Day 999:

beta_t = 0.005

Driver_t = tanh(Momentum_t / 0.10)

Momentum contains detectable positive predictive information.

### TRANSITION

From Day 1000 to Day 1299:

beta_t decreases linearly from 0.005 to 0.

Momentum predictive strength progressively deteriorates.

### INVALID

From Day 1300 to Day 1999:

beta_t = 0

Momentum no longer contributes to subsequent return generation.

The resulting lifecycle is therefore:

Warm-up inside VALID:

No observable momentum contribution yet exists.

VALID after warm-up:

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

For Day 20 onward, the causal sequence is:

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

During Day 0-19, the causal sequence is:

Price_t

        ↓

Momentum_t unavailable

        ↓

Signal_t unavailable

        ↓

Driver_t = 0

        ↓

Return_(t+1) = epsilon_t

        ↓

Price_(t+1)

The price update is:

Price_(t+1) = Price_t * (1 + Return_(t+1))

Momentum_t and Signal_t must therefore be calculated, or explicitly recognized
as unavailable during warm-up, before Return_(t+1) is realized.

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

During Day 0-19:

- momentum_20d is missing;
- signal is missing.

This missingness is part of the truthful observable information state.

From Day 20 onward, both variables are fully defined.

### Hidden Ground Truth

The following variable must remain hidden during AI evaluation:

- regime.

### Internal Simulation State

The following variable is used internally by the generator but must not be
provided as an AI-visible feature:

- Driver_t.

During warm-up:

Driver_t = 0

This internal zero must not be substituted for missing observable momentum.

experiment_id is simulation metadata rather than an AI-visible market variable.

This separation ensures that the AI must infer structural deterioration from
evidence rather than receiving the answer directly.

---

## 10. Ground Truth

The synthetic environment contains a predefined structural ground truth.

### VALID

Day 0-999

beta = 0.005

Day 0-19:

the regime is VALID, but the momentum mechanism is inactive because a valid
20-period momentum observation does not yet exist.

Day 20-999:

momentum contributes positively to subsequent expected return generation.

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

Warm-up is a feature-availability condition, not a hidden ground-truth regime.

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

The warm-up period should not be interpreted as evidence for or against the
momentum belief because the relevant observable feature is not yet defined.

---

## 12. Experimental Interpretation

The benchmark is fundamentally a belief-revision experiment rather than a
trading-strategy optimization experiment.

The momentum relationship provides the controlled belief.

The three regimes provide the structural lifecycle.

Noise creates ambiguous evidence.

The warm-up period provides the minimum historical state needed to construct the
observable belief variable.

It is not itself part of the belief-revision challenge.

The AI system's task is to determine whether observed failures after the belief
becomes measurable represent:

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

Warm-up:

Day 0-19

Momentum during warm-up:

missing

Signal during warm-up:

missing

Internal driver during warm-up:

Driver_t = 0

Warm-up return:

Return_(t+1) = epsilon_t

Momentum after warm-up:

Momentum_t = Price_t / Price_(t-20) - 1

First valid momentum observation:

Momentum_20 = Price_20 / Price_0 - 1

Signal after warm-up:

Signal_t = 1 if Momentum_t > 0, otherwise 0

Latent driver after warm-up:

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

The signal threshold is fixed at zero from Day 20 onward and is not a calibrated
parameter.

The warm-up convention is a structural initialization rule and is not a
calibrated parameter.

The benchmark generator contains no fixed five-period holding rule.

Any earlier specification using:

- a 5% signal threshold;
- a fixed five-period holding period;
- direct alpha-based cumulative momentum feedback; or
- clipped cumulative momentum as the return-generation driver

is superseded by the current frozen design.

The only intentional missing values in the exported dataset are:

- momentum_20d during Day 0-19;
- signal during Day 0-19.

Any future change to:

- warm-up length;
- warm-up missing-value semantics;
- warm-up driver behavior;
- momentum definition;
- signal definition;
- signal threshold;
- latent driver transformation;
- beta schedule;
- noise process;
- regime boundaries;
- temporal alignment

must be treated as an explicit experimental design revision rather than an
implementation adjustment.