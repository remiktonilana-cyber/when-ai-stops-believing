# Baseline Experiment Report


## 1. Experiment Objective


This experiment evaluates whether an AI system can recognize when a previously useful belief becomes unreliable after structural changes in the environment.


The experiment does not primarily measure prediction accuracy.

Instead, it studies adaptive intelligence through the ability to:

- maintain useful knowledge when evidence remains consistent;

- recognize when previous assumptions become unreliable;

- revise beliefs under changing environments.


The central research question:


> Can an AI system manage the validity boundary of its own knowledge?



---


## 2. Experimental Architecture


The experiment follows a separated architecture:


Synthetic Environment

    |

    ↓

Observation Builder

    |

    ↓

Belief Agent

    |

    ↓

Evaluation Engine



Each component has an independent responsibility.



### 2.1 Synthetic Environment


Creates a reproducible environment where structural changes can be explicitly controlled.



### 2.2 Observation Builder


Defines the information boundary between the environment and the AI system.



### 2.3 Belief Agent


Maintains an internal belief state and updates confidence according to observed evidence.



### 2.4 Evaluation Engine


Measures whether belief evolution matches environmental structural changes.



This separation prevents information leakage and allows adaptive intelligence to be evaluated independently from prediction performance.


---


## 3. Synthetic Environment Design


The experiment uses a controlled synthetic market environment.


The environment contains three structural phases:


| Phase | Time Range | Description |
|---|---|---|
| VALID | Day 0-999 | Historical relationship remains useful |
| TRANSITION | Day 1000-1299 | Relationship reliability gradually changes |
| INVALID | Day 1300-1999 | Previous relationship is no longer reliable |


The true environment state is hidden from the AI system.


The AI system cannot directly access:

- regime labels;

- transition timing;

- hidden simulation parameters.


Instead, the AI must infer changes from observable evidence.



---


## 4. Observation Constraint


The AI system receives only information available at the current timestep.


Allowed information includes:

- historical price information;

- historical return information;

- volume information;

- momentum features;

- observable signal variables;

- previous belief states.


Forbidden information includes:

- hidden regime labels;

- future observations;

- future returns;

- future prices;

- internal simulation variables;

- evaluation results.


The purpose of this constraint is to ensure that belief revision is based on evidence rather than privileged information.



---


## 5. Baseline Belief Agent


The baseline agent represents a simple adaptive intelligence system.


Instead of directly predicting future outcomes, the agent maintains a belief state describing whether a previously useful relationship remains reliable.


The belief state contains:


```json
{
    "belief_status": "VALID | UNCERTAIN | INVALID",
    "confidence": 0-1
}
```

The agent also maintains historical reliability memory.

The update process follows:

Current observation

+

Historical reliability

↓

Belief state update

The agent does not access the hidden environment state.

All belief updates are generated from AI-visible observations only.



## 6. Evaluation Metrics

The experiment evaluates four dimensions of adaptive intelligence.

### 6.1 Adaptation Delay

Adaptation Delay measures the time required for the AI system to recognize that a previous relationship has become invalid.

Result:

5 days

The environment becomes invalid at Day 1300.

The baseline agent changes to INVALID belief state at Day 1305.

### 6.2 False Persistence

False Persistence measures whether an AI system continues maintaining an outdated belief after the underlying relationship becomes invalid.

Result:

0 days

The baseline agent does not continue maintaining a VALID belief after structural invalidation.

### 6.3 False Abandonment

False Abandonment measures whether an AI system abandons a valid belief before structural failure occurs.

Result:

0 days

During the stable VALID phase, the baseline agent maintains the original belief.

### 6.4 Belief Boundary Awareness

Belief Boundary Awareness measures whether an AI system recognizes increasing uncertainty before complete structural failure.

Result:

7 days

The baseline agent enters UNCERTAIN state 7 days before complete invalidation.

## 7. Experimental Result

The baseline experiment demonstrates the following behaviors:

Capability	Result
Maintain valid beliefs	Passed
Detect structural invalidation	Passed
Avoid premature abandonment	Passed
Recognize uncertainty before failure	Passed

The result shows that adaptive intelligence can be evaluated not only by whether a system learns useful patterns, but also by whether it recognizes when those patterns should no longer be trusted.

## 8. Research Implication

Traditional AI evaluation often focuses on:

Can a system find a useful pattern?

This benchmark focuses on a different question:

Can a system recognize when a useful pattern stops being reliable?

The experiment treats intelligence as a process of managing knowledge validity boundaries.

A capable adaptive system should not only accumulate knowledge.

It should also understand the conditions under which that knowledge remains valid.

## 9. Future Extensions

The current experiment provides a minimal benchmark environment.

Future extensions may include:

stronger AI reasoning agents;
large language model based belief agents;
multiple structural transition types;
different observation spaces;
cross-domain environments;
integration with the LAI Track for early transition detection.

The fundamental principle remains:

Intelligence requires not only learning from the world, but also recognizing when the world has changed.