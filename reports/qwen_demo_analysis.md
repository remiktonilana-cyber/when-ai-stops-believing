# Qwen Minimum Demo Trajectory Analysis

## Basic information

| Field | Value |
| --- | --- |
| Provider | qwen |
| Trajectory length | 451 |
| First timestamp | 2003-08-25 |
| Last timestamp | 2005-05-16 |

## Belief state statistics

| Belief status | Count | Percentage |
| --- | ---: | ---: |
| VALID | 396 | 87.80% |
| UNCERTAIN | 4 | 0.89% |
| INVALID | 51 | 11.31% |

## Transition analysis

Transition count: **7**

| # | Timestamp | Transition |
| ---:| ---|---|
| 1 | 2003-08-26 | UNCERTAIN → VALID |
| 2 | 2004-08-17 | VALID → UNCERTAIN |
| 3 | 2004-08-18 | UNCERTAIN → VALID |
| 4 | 2005-02-18 | VALID → UNCERTAIN |
| 5 | 2005-02-21 | UNCERTAIN → VALID |
| 6 | 2005-03-04 | VALID → UNCERTAIN |
| 7 | 2005-03-07 | UNCERTAIN → INVALID |

## Belief oscillation analysis

A reversal is counted here only when VALID and INVALID are adjacent episodes, without an intervening UNCERTAIN state.

- Direct VALID ↔ INVALID reversals: **0**
- INVALID → VALID recoveries: **0**

| Belief status | Episode count | Average episode duration (timesteps) |
| --- | ---: | ---: |
| VALID | 3 | 132.00 |
| UNCERTAIN | 4 | 1.00 |
| INVALID | 1 | 51.00 |

## Confidence analysis

| Belief status | Mean confidence | Confidence range |
| --- | ---: | ---: |
| VALID | 0.7998 | 0.7500–0.8000 |
| UNCERTAIN | 0.5750 | 0.5000–0.7500 |
| INVALID | 0.9761 | 0.9000–0.9900 |

## Existing demo metrics

These values use the existing evaluation engine definitions without modification.

| Metric | Value |
| --- | ---: |
| Adaptation Delay | 50 |
| False Persistence | 49 |
| Belief Boundary Awareness | 350 |

## Interpretation

Invalidation detection and oscillatory belief revision describe different behavior dimensions. Adaptation Delay records when INVALID is first reached relative to structural invalidation, while repeated reversals and recoveries describe the stability of the trajectory around that decision. A trajectory may detect invalidation yet continue alternating between incompatible belief states, or remain stable without detecting invalidation. These observations compare belief-revision stability, not overall model intelligence.
