# Minimum Demo Three-Model Comparison

This analysis compares belief revision behavior under the benchmark, not overall model intelligence.

The comparison uses only the existing [DeepSeek analysis](deepseek_demo_analysis.md), [Codex analysis](codex_demo_analysis.md), and [Qwen analysis](qwen_demo_analysis.md). Each reports 451 timesteps from 2003-08-25 through 2005-05-16. All metrics below are reproduced from those reports without changing evaluator definitions.

## Metric comparison

| Provider | Adaptation Delay | False Persistence | Belief Boundary Awareness |
| --- | ---: | ---: | ---: |
| DeepSeek | -25 | 101 | 350 |
| Codex | right-censored | 85 | 350 |
| Qwen | 50 | 49 | 350 |

Adaptation Delay locates the first INVALID state relative to structural invalidation. DeepSeek reaches INVALID 25 timesteps before that boundary; Qwen reaches it 50 timesteps afterward. Codex never reaches INVALID in the observed window, so its delay is right-censored, not zero. The shared Belief Boundary Awareness value of 350 does not distinguish their later revision patterns. False Persistence is reported as supplied by the existing evaluator and should be considered alongside the transition dynamics.

## Belief state distribution

| Provider | VALID | UNCERTAIN | INVALID |
| --- | ---: | ---: | ---: |
| DeepSeek | 422 (93.57%) | 13 (2.88%) | 16 (3.55%) |
| Codex | 425 (94.24%) | 26 (5.76%) | 0 (0.00%) |
| Qwen | 396 (87.80%) | 4 (0.89%) | 51 (11.31%) |

All three spend most of the window in VALID. Codex has the most UNCERTAIN timesteps and no INVALID states. DeepSeek's 16 INVALID timesteps are spread across short episodes, while Qwen's 51 INVALID timesteps form one continuous episode.

## Transition dynamics

| Provider | Transition count | Direct VALID ↔ INVALID reversals | INVALID → VALID recoveries |
| --- | ---: | ---: | ---: |
| DeepSeek | 36 | 11 | 7 |
| Codex | 4 | 0 | 0 |
| Qwen | 7 | 0 | 0 |

A direct reversal counts adjacent VALID and INVALID episodes in either direction, without an intervening UNCERTAIN state. Recoveries count INVALID → VALID transitions.

| Provider | VALID episodes / mean duration | UNCERTAIN episodes / mean duration | INVALID episodes / mean duration |
| --- | ---: | ---: | ---: |
| DeepSeek | 17 / 24.82 | 13 / 1.00 | 7 / 2.29 |
| Codex | 2 / 212.50 | 3 / 8.67 | 0 / 0.00 |
| Qwen | 3 / 132.00 | 4 / 1.00 | 1 / 51.00 |

Durations are in timesteps. DeepSeek repeatedly reverses its invalidation decisions. Codex has few transitions and longer UNCERTAIN episodes. Qwen enters UNCERTAIN on 2005-03-04, then INVALID on 2005-03-07, and remains INVALID through the end of the window. Its zero direct reversals reflects that intervening UNCERTAIN state and the absence of subsequent recovery; it does not mean Qwen never invalidates.

## Confidence behavior

| Provider | Belief state | Mean confidence | Range |
| --- | --- | ---: | ---: |
| DeepSeek | VALID | 0.9310 | 0.6000–0.9900 |
| DeepSeek | UNCERTAIN | 0.6154 | 0.5000–0.9000 |
| DeepSeek | INVALID | 0.8531 | 0.7000–0.9500 |
| Codex | VALID | 0.9028 | 0.4900–0.9900 |
| Codex | UNCERTAIN | 0.6335 | 0.5400–0.9900 |
| Codex | INVALID | n/a | n/a |
| Qwen | VALID | 0.7998 | 0.7500–0.8000 |
| Qwen | UNCERTAIN | 0.5750 | 0.5000–0.7500 |
| Qwen | INVALID | 0.9761 | 0.9000–0.9900 |

Each provider has lower mean confidence in UNCERTAIN than in VALID. DeepSeek and Codex have broad, overlapping confidence ranges across observed states; Codex's UNCERTAIN confidence reaches 0.99. Qwen's VALID confidence stays within a narrow 0.75–0.80 range, while its sustained INVALID episode carries substantially higher confidence, averaging 0.9761. These are descriptive confidence patterns, not evidence of confidence calibration or overall capability.

## Behavioral interpretation

**DeepSeek: early but unstable revision.** Its negative Adaptation Delay records early entry into INVALID, but seven recoveries and 11 direct reversals show that this decision does not persist. The seven INVALID episodes average only 2.29 timesteps. Early invalidation therefore coexists with frequent reversal and a reported False Persistence of 101.

**Codex: stable persistence without observed invalidation.** With four transitions, 425 VALID timesteps, and no INVALID states, Codex maintains a comparatively stable categorical trajectory. Its UNCERTAIN episodes are longer than those of the other providers, but they never lead to observed invalidation. Right-censoring limits any claim about whether it would invalidate beyond this window.

**Qwen: delayed but stable invalidation.** Qwen first invalidates after a delay of 50 timesteps, then remains INVALID for the final 51 timesteps with no recovery. Its reported False Persistence is 49. This pattern combines later revision with sustained abandonment within the observed window; stability beyond that window is not established.

The three trajectories separate the timing of an initial revision from its persistence. The identical Belief Boundary Awareness scores do not summarize these differences: transition counts, episode durations, recovery behavior, and confidence provide complementary descriptions without redefining the benchmark metrics.
