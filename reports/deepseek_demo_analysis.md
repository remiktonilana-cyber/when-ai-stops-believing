# DeepSeek Minimum Demo Trajectory Analysis

## Basic information

| Field | Value |
| --- | --- |
| Provider | deepseek |
| Trajectory length | 451 |
| First timestamp | 2003-08-25 |
| Last timestamp | 2005-05-16 |

## Belief state statistics

| Belief status | Count | Percentage |
| --- | ---: | ---: |
| VALID | 422 | 93.57% |
| UNCERTAIN | 13 | 2.88% |
| INVALID | 16 | 3.55% |

## Transition analysis

Transition count: **36**

| # | Timestamp | Transition |
| ---:| ---|---|
| 1 | 2003-08-26 | UNCERTAIN → VALID |
| 2 | 2004-08-17 | VALID → UNCERTAIN |
| 3 | 2004-08-18 | UNCERTAIN → VALID |
| 4 | 2004-11-19 | VALID → UNCERTAIN |
| 5 | 2004-11-22 | UNCERTAIN → INVALID |
| 6 | 2004-11-25 | INVALID → VALID |
| 7 | 2004-11-26 | VALID → INVALID |
| 8 | 2004-11-30 | INVALID → VALID |
| 9 | 2004-12-01 | VALID → INVALID |
| 10 | 2004-12-02 | INVALID → VALID |
| 11 | 2004-12-08 | VALID → INVALID |
| 12 | 2004-12-10 | INVALID → VALID |
| 13 | 2004-12-13 | VALID → INVALID |
| 14 | 2004-12-17 | INVALID → VALID |
| 15 | 2004-12-23 | VALID → UNCERTAIN |
| 16 | 2004-12-24 | UNCERTAIN → VALID |
| 17 | 2005-01-06 | VALID → UNCERTAIN |
| 18 | 2005-01-07 | UNCERTAIN → VALID |
| 19 | 2005-01-19 | VALID → UNCERTAIN |
| 20 | 2005-01-20 | UNCERTAIN → INVALID |
| 21 | 2005-01-25 | INVALID → VALID |
| 22 | 2005-02-10 | VALID → UNCERTAIN |
| 23 | 2005-02-11 | UNCERTAIN → VALID |
| 24 | 2005-03-18 | VALID → UNCERTAIN |
| 25 | 2005-03-21 | UNCERTAIN → VALID |
| 26 | 2005-04-18 | VALID → UNCERTAIN |
| 27 | 2005-04-19 | UNCERTAIN → VALID |
| 28 | 2005-04-20 | VALID → UNCERTAIN |
| 29 | 2005-04-21 | UNCERTAIN → VALID |
| 30 | 2005-04-26 | VALID → UNCERTAIN |
| 31 | 2005-04-27 | UNCERTAIN → VALID |
| 32 | 2005-04-29 | VALID → UNCERTAIN |
| 33 | 2005-05-02 | UNCERTAIN → INVALID |
| 34 | 2005-05-03 | INVALID → VALID |
| 35 | 2005-05-05 | VALID → UNCERTAIN |
| 36 | 2005-05-06 | UNCERTAIN → VALID |

## Belief oscillation analysis

A reversal is counted here only when VALID and INVALID are adjacent episodes, without an intervening UNCERTAIN state.

- Direct VALID ↔ INVALID reversals: **11**
- INVALID → VALID recoveries: **7**

| Belief status | Episode count | Average episode duration (timesteps) |
| --- | ---: | ---: |
| VALID | 17 | 24.82 |
| UNCERTAIN | 13 | 1.00 |
| INVALID | 7 | 2.29 |

## Confidence analysis

| Belief status | Mean confidence | Confidence range |
| --- | ---: | ---: |
| VALID | 0.9310 | 0.6000–0.9900 |
| UNCERTAIN | 0.6154 | 0.5000–0.9000 |
| INVALID | 0.8531 | 0.7000–0.9500 |

## Existing demo metrics

These values use the existing evaluation engine definitions without modification.

| Metric | Value |
| --- | ---: |
| Adaptation Delay | -25 |
| False Persistence | 101 |
| Belief Boundary Awareness | 350 |

## Interpretation

Eventual invalidation detection and oscillatory belief revision describe different behavior dimensions. Adaptation Delay records when INVALID is first reached relative to structural invalidation, while repeated reversals and recoveries describe the stability of the trajectory around that decision. A system can therefore detect invalidation yet continue alternating between incompatible belief states afterward.
