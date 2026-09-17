# Canonical LAI System-Layer Experiment A

## Frozen design and execution

Starting HEAD: `4c5e62d Calibrate LAI synthetic system statistics`, with a clean
working tree. Generator checkpoint: `d347531 Add LAI synthetic system environment`.
Both scientific implementations remain unchanged. Canonical seed 42 was generated
once for this analysis: 2,000 timesteps, default zero drift. No recalibration,
parameter tuning, alternative specifications, or new thresholds were used.
Engineering regression tests may separately instantiate their existing worlds.

This reveal directly reused `shock_balance`, `amplification`, and `_classifier_auc`
from frozen `src/lai_calibration.py`, with its state encoding, feature constants,
and temporal boundary. The calibration-only runner and its seed restrictions were
left unchanged; canonical data were not relabeled as a calibration world.

Frozen references below are the human-specified empirical 95% calibration
envelopes from seeds 1000–1199, fixed before reveal. They are **not confidence
intervals**. Comparisons use unrounded canonical values against the specified
reference endpoints. Displayed canonical values are rounded to six decimals.

## Canonical context

| Portion | Timesteps | RESILIENT | AMPLIFYING | Both classes present |
| --- | --- | ---: | ---: | --- |
| Full world | 0–1999 | 1400 | 600 | Yes |
| Training | 0–1399 | 954 | 446 | Yes |
| Testing | 1400–1999 | 446 | 154 | Yes |

AMPLIFYING share: **30%**. No shuffled split.

## A1 — Shock balance

| Statistic | RESILIENT | AMPLIFYING |
| --- | ---: | ---: |
| Mean shock | 0.020889 | -0.000582 |
| Mean absolute shock | 0.799548 | 0.796182 |
| SD shock | 1.001093 | 0.995072 |
| SD absolute shock | 0.602403 | 0.595990 |

Sample SDs use ddof=1. Raw absolute-shock mean difference (AMPLIFYING minus
RESILIENT): **-0.003366**. SMD: **-0.005606**, using the conventional pooled SD
sqrt(((n_A−1)s_A²+(n_R−1)s_R²)/(n_A+n_R−2)) of absolute shocks.

Frozen SMD envelope: **[-0.08446, 0.09832]**.

**A1: WITHIN CALIBRATION.** The generator's `_rng_streams` spawns distinct local
child streams for latent innovations, measurement noise, nuisance, shocks, and
response noise. Shocks are drawn from the shock child stream as N(0,1), without
reading latent stress or state. This structural separation is the primary
causal-design evidence. The observed SMD is only a finite-sample diagnostic;
it does not prove mathematical independence.

## A2 — Amplification

Frozen OLS specification:
`next_response = beta_0 + beta_1*shock + beta_2*state + beta_3*shock*state + error`,
with RESILIENT=0 and AMPLIFYING=1. Conventional homoskedastic residual-variance
standard errors; residual df=1996; two-sided Student-t 95% confidence interval.
Separate state slopes use OLS with an intercept.

| Statistic | Canonical value |
| --- | ---: |
| beta_0 | -0.002650 |
| beta_1 | 0.986172 |
| beta_2 | -0.005155 |
| beta_3 | 2.007487 |
| beta_3 SE | 0.024169 |
| beta_3 95% CI lower | 1.960087 |
| beta_3 95% CI upper | 2.054886 |
| alpha_hat_resilient | 0.986172 |
| alpha_hat_amplifying | 2.993659 |

Frozen beta_3 calibration envelope: **[1.95374, 2.05230]**.
Theoretical DGP slopes remain 1 and 3, with interaction 2; table values are fitted.

**A2: WITHIN CALIBRATION.** The interaction is positive, its 95% CI excludes zero
on the positive side, and the AMPLIFYING slope exceeds the RESILIENT slope.
The calibration comparison concerns the beta_3 point estimate, not whether its
confidence interval fits inside the calibration envelope. The frozen response
mechanism amplifies positive and negative shocks symmetrically.

## A3 — Pre-shock footprints

Both classifiers reuse the frozen training-only StandardScaler (mean centering,
unit variance), then LogisticRegression with L2 penalty, C=1.0, solver=lbfgs,
tol=0.0001, max_iter=1000, fit_intercept=True, class_weight=None, random_state=0.
ROC-AUC uses held-out class-1 probabilities. No hyperparameters were tuned.

The FCL model uses only `fragility`, `crowding`, and `liquidity_stress` to predict
latent state. It excludes latent stress, shock, next response, and nuisance.
The generator constructs these noisy footprints before shocks and responses;
no response information enters them. The full-trajectory stress quantile remains
offline synthetic ground truth, not an online estimator or a classifier feature.

**AUC_FCL: 0.962145**. Frozen envelope: **[0.89462, 0.97455]**.

**A3: WITHIN CALIBRATION.** The synthetic state has strong observable pre-shock
footprints under this temporal split. These results do not support describing
the state as difficult to observe. Neither over-separation nor weak-footprint
outlier labeling is triggered.

## A4 — Nuisance control

The separate nuisance classifier uses only `nuisance`, with the identical frozen
split, preprocessing, logistic configuration, target encoding, and AUC method.

**AUC_N: 0.505023**. Frozen envelope: **[0.45383, 0.54301]**.

**AUC_gap = AUC_FCL − AUC_N: 0.457122**, above the frozen lower calibration
reference **0.36842**.

**A4: WITHIN CALIBRATION.** Nuisance discrimination is near chance and does not
carry information comparable to FCL in this world and split. The nuisance has its
own generator stream and is not constructed from stress. A single finite-sample
AUC does not establish exact population independence.

## Overall interpretation

**SYSTEM-LAYER MECHANISM STATUS: SUPPORTED IN FROZEN SYNTHETIC DGP.**

All four substantive properties are present: structurally independent shocks,
state-dependent shock sensitivity, informative pre-shock footprints, and a
nuisance control without comparable discrimination.

**CANONICAL CALIBRATION STATUS: TYPICAL RELATIVE TO CALIBRATION.**

All four envelope comparisons are within calibration, and the AUC gap exceeds
its lower reference. No calibration-outlier or substantive-failure classification
is triggered. No numerical criterion was added after observing the results.

### Synthetic mechanism evidence

Experiment A establishes only that the frozen synthetic environment successfully
operationalizes the intended latent-amplification mechanism under the specified
canonical design and analysis. Its state definition and sensitivity differences
are synthetic construction choices, not discoveries about a real population.

### Real-world claims

This does not establish that the same mechanism exists in real financial markets
or other real systems, validate a real-world LAI measure, or establish an Agent
reliability effect. No LLM Agent or provider was evaluated and no external API
was called.
