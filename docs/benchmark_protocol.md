# Benchmark Protocol

## 1. Objective


The Benchmark Track evaluates whether an AI system can revise beliefs when a previously valid pattern becomes invalid.

...

The central question is:

Can an AI system recognize when evidence indicates that a previously successful belief should be updated?


## Intelligence Boundary Principle


The benchmark is designed around the principle that intelligence requires not only learning useful patterns, but also recognizing when previously useful patterns lose validity.


A system that only preserves successful historical beliefs may achieve short-term performance while failing to adapt to environmental change.


Therefore, the benchmark evaluates whether an AI system can:

- maintain useful beliefs when evidence remains consistent;

- reduce confidence when evidence becomes contradictory;

- revise beliefs when previous assumptions no longer explain observations.


The benchmark does not evaluate whether an AI system discovers absolute truth.

It evaluates whether an AI system can manage the validity boundary of its own beliefs.


---


# 2. Benchmark Philosophy


The benchmark evaluates belief adaptation rather than prediction accuracy.

A strong system should balance two competing behaviors.


## 2.1 Over-Persistence

Over-persistence occurs when an AI system continues to rely on an outdated belief after the underlying relationship has changed.

Example:

A pattern is valid.

    ↓

The environment changes.

    ↓

The AI continues to believe the old pattern remains valid.


This represents failure to adapt.


---


## 2.2 Over-Reaction

Over-reaction occurs when an AI system abandons a valid belief too quickly because of temporary noise.

Example:
A pattern remains valid.

    ↓

Short-term negative evidence appears.

    ↓

The AI immediately discards the belief.



This represents excessive sensitivity to short-term fluctuations.


---


# 3. Observation Boundary


The benchmark follows strict temporal causality.

At each timestep t:
Information available at t

    ↓

AI belief update

    ↓

Future outcome revealed at t+1


The AI system may only access information available at the current timestep.


## 3.1 Allowed Information

The AI system may receive:

- historical price information;
- historical return information;
- observable market variables;
- current momentum information;
- current signal information;
- previous AI belief states (if memory is enabled).


## 3.2 Forbidden Information

The AI system must not receive:

- future observations;
- future returns;
- future prices;
- hidden regime labels;
- internal simulation variables;
- benchmark evaluation results.


The purpose of this restriction is to ensure that AI decisions are based on evidence available at the time of decision.


---


# 4. AI Input Interface


The benchmark uses a model-independent observation interface.

The observation format should separate:

- environment information;
- AI reasoning;
- evaluation.


A generic observation contains:

Observation(t)

{

timestamp,

historical_observations,

current_features,

previous_belief_state

}


The interface should remain independent from specific AI models.

The same observation structure should support:

- large language models;
- reasoning agents;
- other adaptive intelligence systems.


---


# 5. Temporal Interaction Loop


The benchmark follows an online interaction process.

For each timestep t:

1. Environment state is generated.

2. Observation Builder constructs Observation(t)
   using only AI-visible information.

3. AI receives Observation(t).

4. AI produces belief state.

5. Environment reveals Outcome(t+1).

6. Evaluation records:
   - AI belief
   - confidence
   - adaptation behavior
   - correctness relative to hidden state

7. Continue to timestep t+1.



This design evaluates belief evolution rather than isolated predictions.


---


# 6. Belief Output Format


The AI system should output a structured belief state.


The minimum required output contains:

{

belief_status,

confidence,

explanation

}


## 6.1 Belief Status

The AI belief status is not equivalent to the hidden environmental regime.

The hidden regime is available only to the evaluation system.

The AI belief status represents the AI system's inferred understanding based on observed evidence.

The benchmark defines three conceptual states:

VALID

The previous relationship remains useful.

UNCERTAIN

Evidence suggests possible structural change.

INVALID

The previous relationship no longer provides reliable guidance.


The AI system is not given the true regime label.

It must infer belief status from observations.


## 6.2 Confidence


Confidence represents the AI system's certainty about its current belief.

Confidence is evaluated separately from correctness.


A calibrated system should:

- have higher confidence when evidence is strong;
- reduce confidence during uncertain transitions;
- avoid excessive certainty after structural change.


---


# 7. Evaluation Metrics


The benchmark evaluates multiple dimensions of adaptive intelligence.


## 7.1 Adaptation Delay


Measures the time required for an AI system to update its belief after structural change occurs.


A shorter delay indicates faster adaptation.


---


## 7.2 False Persistence


Measures how long an AI system continues to maintain an invalid belief after the environment changes.


This captures failure caused by excessive attachment to historical patterns.


---


## 7.3 False Abandonment


Measures premature transition to `belief_status == INVALID` while the
underlying belief remains in the stable ground-truth VALID period.


This captures excessive sensitivity to noise.

`UNCERTAIN` is an explicit boundary state and does not count as abandonment.


---


## 7.4 Belief Calibration


Measures whether confidence corresponds to actual reliability.


A well-calibrated system should reduce confidence when evidence becomes inconsistent with previous assumptions.


---


# 8. Benchmark Design Principle


The benchmark separates:
Environment Generation

    from

AI Belief Formation

    from

Evaluation

This separation ensures that:

- the environment remains reproducible;
- AI systems are compared under identical conditions;
- adaptation behavior can be measured independently from prediction accuracy.


---


# 9. Future Extensions


The Benchmark Track can later support:

- different AI model families;
- different observation windows;
- different memory mechanisms;
- different synthetic environments.


The core experimental principle remains unchanged:

> Evaluate whether intelligence can recognize when the world has changed.
