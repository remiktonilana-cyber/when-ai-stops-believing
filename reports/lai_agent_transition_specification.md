# Frozen LAI Agent-transition specification — E3.4

## Research purpose and freeze provenance

Starting checkpoint: `c71910f Document canonical LAI system experiment`.
This specification freezes the subsequent human research decision following the
noncanonical E3.3 diagnostic calibration. It closes parameter-selection freedom
before the canonical E3 reveal and before any LLM Agent experiment.

The purpose is to test belief revision under one transparent, precalibrated,
causally controlled nonstationary synthetic environment: an initially correct
shock-response belief, prospective warning footprints, gradual structural change,
and resolved contradictory evidence. The human selected d_plus=0.03, delta=0.50,
and k=3 from the preregistered grid; W=50 was already frozen. These choices were
not selected by optimizing LLM behavior. No E3 LLM experiment has been run.

The importable reference is `src/lai_transition_reference.py`. It reuses the
existing environment's trajectory constants and calibration detector's W rather
than duplicating those values. T_DELTA is computed by `theoretical_time(DELTA)`
from `alpha_schedule()`. Importing the reference does not generate a trajectory.
Historical E3.3 candidate grids and results remain unchanged; the calibration
report's statement that no parameters were selected describes that earlier task.
This document records the later human decision without rewriting that history.

## Frozen parameters and timeline

| Parameter | Value | Role |
| --- | ---: | --- |
| N | 1200 | Trajectory rows t=0..1199 |
| T_warning | 400 | Stress accumulation begins |
| T_structural | 600 | Structural-transition phase begins |
| d_plus | 0.03 | Warning-channel drift |
| delta | 0.50 | Minimum practical sensitivity increase |
| alpha_boundary | 1.50 | 1+delta |
| W | 50 | Maximum resolved-pair reference horizon |
| k | 3 | Consecutive evidence conditions |
| T_delta | 675 | Derived first t with alpha_t >= 1.50 |

| Phase | Rows | Hidden response coefficient |
| --- | --- | --- |
| Established old world | 0..399 | alpha_t=1 |
| Warning/stress accumulation | 400..599 | alpha_t=1 |
| Structural transition | 600..899 | alpha_t=1+2*(t-600)/299 |
| Established new world | 900..1199 | alpha_t=3 |

Exactly alpha_600=1 and alpha_899=3. T_structural=600 denotes the transition's
onset boundary; under the frozen discrete schedule the first strict increase
above 1 occurs at row 601. This distinction does not change the frozen timeline.
T_delta=675 is derived from the schedule and delta, not independently hardcoded.

Latent stress remains Z_-1=0 and Z_t=0.97*Z_(t-1)+d_t+eta_t, with independent
eta_t~Normal(0,0.15²). Drift d_t=0.03 for 400<=t<750, zero otherwise.
F/C/L=sigmoid((1,0.8,1.1)*Z+independent Normal(0,0.5²) measurement noise).
Nuisance and shocks are independent standard normals. R_(t+1)=alpha_t*E_t+
Normal(0,0.5²) response noise. Separate deterministic child RNG streams govern
innovations, measurement noise, nuisance, shocks, and response noise.

The warning-only/no-change control uses alpha=1 at all rows and shares every
stochastic realization with its matched transition world at the same seed and
d_plus. Only the alpha schedule differs. Hidden alpha, stress, and benchmark
times are research ground truth, not future Agent inputs.

## Human parameter-selection rationale

**d_plus=0.03:** The held-out cross-world diagnostic showed an observable but
imperfect and noisy stress footprint: pooled AUC=0.79321; seed-level mean=0.79101,
SD=0.11949, 2.5%=0.54102, median=0.81044, 97.5%=0.96643. Warning information is
substantially variable across worlds and is not a deterministic regime label.
The selection expresses the desired benchmark design, not an AUC maximization.

**delta=0.50:** A substantive 50% increase in shock-response sensitivity defines
the practical boundary alpha=1.50. It is the middle candidate among 25%, 50%, and
75% increases. Evidence must support exceeding that boundary, rather than merely
a statistically detectable departure from alpha=1. This is a scientific and
operational benchmark definition, not a discovered natural constant.

**k=3:** The human chose persistence against isolated local-window crossings while
limiting added delay. At delta=0.50, the calibration observed:

| k | Control detections | Transition detections | Median evidence latency |
| --- | --- | --- | ---: |
| 1 | 0/200 | 200/200 | 46 |
| 3 | 0/200 | 200/200 | 49 |
| 5 | 0/200 | 200/200 | 51 |

Zero false evidence events were observed in these 200 calibration control worlds
for each candidate. This does not establish a population false-positive rate of
zero or demonstrate statistical superiority of k=3.

**W=50:** This horizon was frozen before calibration. It matches the maximum
resolved evidence horizon intended for the future Agent, preventing the reference
from using a longer raw resolved-pair history than the Agent receives.

## Frozen evidence reference

Row i pairs current E_i with next_response R_(i+1). The latter resolves at time
i+1, not at time i. At evaluation time j, the reference uses only rows j-50..j-1.
Eligible evaluation times are 50..1200, including resolution of the last row.
The unresolved current response and all future observations are excluded.

For those 50 resolved pairs:

- alpha_hat = sum(E_i * R_(i+1)) / sum(E_i²).
- s² = sum((R_(i+1) - alpha_hat*E_i)²) / 49.
- SE = sqrt(s² / sum(E_i²)).
- Local conventional 95% interval = alpha_hat ± t_(0.975,49)*SE.
- Single-window substantive evidence condition: lower_bound > 1.50 (strict).

The uncertainty estimate uses only observed residuals, never the hidden noise
sigma. No Z, F/C/L, nuisance, hidden alpha, T_warning, T_structural, or T_delta
enters the estimator. Zero shock energy produces an undefined interval and no
qualifying evidence condition.

T_evidence is the first evaluation time at which the condition has held for three
consecutive eligible evaluation times. It is the detection time when persistence
becomes known, never the first member of the run. No detection is represented by
a missing time, not by a numerical replacement.

This is a local rolling-window diagnostic reference, not an anytime-valid
confidence sequence. It supplies no repeated-window or simultaneous coverage
guarantee. A changing coefficient also limits the interpretation of a working
constant-slope interval inside transition windows.

## Distinct time semantics and two evidence channels

- T_warning=400: controlled stress accumulation begins; observable footprints may
  change while the old response relationship remains valid.
- T_structural=600: onset of the frozen transition phase, with the endpoint detail
  at rows 600/601 stated above.
- T_delta=675: hidden sensitivity first reaches the practical boundary alpha>=1.50.
- T_evidence: resolved Agent-accessible pairs first satisfy the frozen reference
  rule. This is trajectory-dependent; its value remains unset until a later reveal.
- Future T_U: first causally observed entry into UNCERTAIN under future frozen
  Agent evaluation semantics.
- Future T_I: first causally observed entry into INVALID under those semantics.

T_U and T_I, an Agent runner, and final Agent scoring rules are not implemented.

The **prospective warning channel** consists of F/C/L. It can indicate rising
stress before failure of the old shock-response relationship; it does not itself
constitute realized contradiction. The **retrospective contradiction channel**
consists of resolved (E,R) pairs, which reveal whether the old response model
continues to describe observations. These channels remain separate. E3.3 evidence
diagnostics were identical across d_plus precisely because the detector excludes
F/C/L. Warning != contradiction, as illustrated by the matched no-change controls.

## Calibration support and limits of transfer

Calibration used exactly seeds 1000..1199, with 200 worlds per relevant
configuration. Warning classifiers trained on seeds 1000..1139 (140 worlds) and
evaluated seeds 1140..1199 (60 entirely held-out worlds). Baseline rows 0..399 have
label 0; warning rows 400..599 have label 1, with alpha=1 in both periods.

For each d_plus, one fixed logistic classifier used pooled training rows and
training-only StandardScaler. Features were exactly fragility, crowding,
liquidity_stress. L2, C=1, LBFGS, tol=0.0001, max_iter=1000, intercept enabled,
class_weight=None, random_state=0. No row-level random splitting or downsampling.
The same fitted classifier produced pooled and per-seed held-out AUCs. This is
cross-world stress-footprint discrimination, not prediction of structural change.

At selected d_plus=0.03, all 60 held-out worlds were valid; pooled warning
AUC=0.79321. At delta=0.50 and k=3, transition detection was 200/200, control
detection was 0/200, and evidence before T_delta was observed in 0/200 worlds.
Latency D_E=T_evidence-T_delta among the 200 detected transition worlds was:

| Mean | SD | Min | 2.5% | 25% | Median | 75% | 97.5% | Max |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 49.085 | 11.316 | 16 | 27 | 42 | 49 | 57 | 70 | 81 |

The calibration median latency was 49 timesteps after T_delta. This distribution
is not a canonical prediction or an assigned evidence time. Raw calibration
results remain unchanged under gitignored results/lai_transition_*.csv; the
complete historical diagnostics are in lai_transition_calibration_analysis.md.

## Failure-taxonomy interpretation boundary

T_U < T_evidence is not automatically a failure. An Agent may rationally lower
confidence or enter UNCERTAIN in response to causally available warning signals.
Likewise, T_I < T_evidence must not mechanically be labeled Premature Revision
without considering the information available at that time.

Future evaluation should distinguish anticipatory uncertainty, unsupported or
premature abandonment, evidence-supported invalidation, and persistent outdated
belief. T_evidence is a model-independent reference boundary, not a theorem that
every rational Agent must revise at exactly that time. Final scoring is deferred.

## Canonical blindness and scientific boundary

At this freeze, no seed-42 E3 scientific trajectory or statistic has been generated
or inspected, and no seed-42 E3 evidence time is assigned. No LLM provider or
external API has been called. Frozen E1 regression tests may independently use
seed 42 for their previously established engineering checks; these are not E3.

The reference defines one controlled synthetic Agent experiment. It establishes
neither real-world LAI, a universal amplification threshold, a real-market critical
point, a zero population false-positive rate, statistically superior parameter
values, general Agent reliability, nor an LLM-provider ranking. No Agent results
exist for this design. The freeze enables a later causally controlled experiment;
it does not supply its outcome.
