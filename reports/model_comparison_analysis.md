# Minimum Demo Model Comparison Analysis

## Experimental setup

Both trajectories use the frozen Minimum Demo window, Day 950 through Day 1400 inclusive. Each contains the same 451 benchmark timestamps from 2003-08-25 through 2005-05-16, in the same order, and is based on the same benchmark observations. Both are evaluated with the existing evaluation engine and its unchanged metric definitions.

This comparison describes differences in observed belief-revision behavior. It does not rank either model or make claims about overall model intelligence.

## Metric comparison

| Provider | Adaptation Delay | False Persistence | Belief Boundary Awareness |
| --- | ---: | ---: | ---: |
| DeepSeek | -25 | 101 | 350 |
| Codex | right-censored | 85 | 350 |

Under the existing evaluator, DeepSeek's first INVALID state occurred 25 timesteps before the ground-truth INVALID boundary, producing an Adaptation Delay of -25. Codex did not enter INVALID within the demo window, so its Adaptation Delay is right-censored rather than numerical. False Persistence follows the existing definition based on the last post-invalidation VALID state. Both trajectories receive Belief Boundary Awareness of 350 because each begins the selected window in UNCERTAIN, 350 timesteps before the ground-truth INVALID boundary.

## Belief state distribution

| Provider | VALID | UNCERTAIN | INVALID |
| --- | ---: | ---: | ---: |
| DeepSeek | 93.57% (422) | 2.88% (13) | 3.55% (16) |
| Codex | 94.24% (425) | 5.76% (26) | 0.00% (0) |

Both trajectories spend more than 93% of the window in VALID. DeepSeek allocates a small portion to INVALID and less time to UNCERTAIN. Codex never enters INVALID and spends twice the percentage of the window in UNCERTAIN, although those UNCERTAIN states are concentrated into a few longer episodes.

## Transition dynamics

| Provider | Total transitions | VALID → UNCERTAIN | UNCERTAIN → INVALID | INVALID → VALID recovery | Direct VALID ↔ INVALID oscillations |
| --- | ---: | ---: | ---: | ---: | ---: |
| DeepSeek | 36 | 12 | 3 | 7 | 11 |
| Codex | 4 | 2 | 0 | 0 | 0 |

The oscillation count uses the same descriptive convention as the individual analyses: every direct transition between VALID and INVALID is counted, in either direction. DeepSeek has 11 such direct reversals: four VALID → INVALID transitions and seven INVALID → VALID recoveries. Its INVALID states occur in seven short episodes averaging 2.29 timesteps, while its VALID episodes average 24.82 timesteps and its UNCERTAIN episodes each last one timestep.

Codex has no INVALID episode and therefore no VALID ↔ INVALID reversal or recovery. Its two VALID episodes average 212.50 timesteps. Its three UNCERTAIN episodes average 8.67 timesteps, reflecting less frequent but more sustained use of the boundary state.

## Confidence behavior

| Provider | Belief state | Mean confidence | Range |
| --- | --- | ---: | ---: |
| DeepSeek | VALID | 0.9310 | 0.6000–0.9900 |
| DeepSeek | UNCERTAIN | 0.6154 | 0.5000–0.9000 |
| DeepSeek | INVALID | 0.8531 | 0.7000–0.9500 |
| Codex | VALID | 0.9028 | 0.4900–0.9900 |
| Codex | UNCERTAIN | 0.6335 | 0.5400–0.9900 |
| Codex | INVALID | n/a | n/a |

For both providers, mean confidence is lower in UNCERTAIN than in VALID, so aggregate confidence broadly distinguishes those states. The ranges overlap substantially, however. DeepSeek's INVALID confidence is relatively high and overlaps both VALID and UNCERTAIN, meaning movement into INVALID does not consistently correspond to the lowest confidence. Codex also has overlapping VALID and UNCERTAIN ranges, including UNCERTAIN confidence as high as 0.99, so individual state changes are not uniformly accompanied by lower confidence.

## Behavioral interpretation

### Early invalidation and stable persistence

DeepSeek enters INVALID before the environment's ground-truth INVALID phase, as reflected by its negative Adaptation Delay, but it does not remain there. Codex maintains VALID or UNCERTAIN throughout the window and never records INVALID, producing a right-censored Adaptation Delay. These are different revision patterns: early invalidation followed by reversal versus stable persistence without observed invalidation.

### Belief oscillation

DeepSeek changes state 36 times and repeatedly moves between VALID and INVALID, directly or through UNCERTAIN. Its seven INVALID → VALID recoveries show that reaching INVALID is not a stable terminal revision in this trajectory. Codex changes state four times and uses no INVALID state, yielding a substantially steadier categorical trajectory without demonstrating invalidation detection during the observed window.

### Uncertainty management

DeepSeek generally uses UNCERTAIN as a one-timestep bridge around other state changes. Codex uses UNCERTAIN less frequently as an episode but remains there longer when it does. The shared Belief Boundary Awareness value does not capture this difference because the existing metric is determined by the first pre-invalidation UNCERTAIN state, which occurs at the beginning of both trajectories. Episode duration and transition structure therefore add descriptive context about uncertainty management without redefining the benchmark metrics.
