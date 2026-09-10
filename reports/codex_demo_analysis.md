# Codex Minimum Demo Trajectory Analysis

## Basic information

| Field | Value |
| --- | --- |
| Provider | codex |
| Trajectory length | 451 |
| First timestamp | 2003-08-25 |
| Last timestamp | 2005-05-16 |

## Belief state statistics

| Belief status | Count | Percentage |
| --- | ---: | ---: |
| VALID | 425 | 94.24% |
| UNCERTAIN | 26 | 5.76% |
| INVALID | 0 | 0.00% |

## Transition analysis

Transition count: **4**

| # | Timestamp | Transition |
| ---:| ---|---|
| 1 | 2003-08-26 | UNCERTAIN → VALID |
| 2 | 2004-12-16 | VALID → UNCERTAIN |
| 3 | 2004-12-29 | UNCERTAIN → VALID |
| 4 | 2005-04-25 | VALID → UNCERTAIN |

## Belief oscillation analysis

A reversal is counted here only when VALID and INVALID are adjacent episodes, without an intervening UNCERTAIN state.

- Direct VALID ↔ INVALID reversals: **0**
- INVALID → VALID recoveries: **0**

| Belief status | Episode count | Average episode duration (timesteps) |
| --- | ---: | ---: |
| VALID | 2 | 212.50 |
| UNCERTAIN | 3 | 8.67 |
| INVALID | 0 | 0.00 |

## Confidence analysis

| Belief status | Mean confidence | Confidence range |
| --- | ---: | ---: |
| VALID | 0.9028 | 0.4900–0.9900 |
| UNCERTAIN | 0.6335 | 0.5400–0.9900 |
| INVALID | n/a | n/a |

## Existing demo metrics

These values use the existing evaluation engine definitions without modification.

| Metric | Value |
| --- | ---: |
| Adaptation Delay | right-censored |
| False Persistence | 85 |
| Belief Boundary Awareness | 350 |

## Interpretation

Invalidation detection and oscillatory belief revision describe different behavior dimensions. Adaptation Delay records when INVALID is first reached relative to structural invalidation, while repeated reversals and recoveries describe the stability of the trajectory around that decision. A trajectory may detect invalidation yet continue alternating between incompatible belief states, or remain stable without detecting invalidation. These observations compare belief-revision stability, not overall model intelligence.
