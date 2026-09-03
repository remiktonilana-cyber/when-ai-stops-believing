# Project Architecture


## 1. Research Objective

This project studies how intelligent systems update beliefs when previously valid patterns become invalid.

The central research question is:

> How should an intelligent system adapt when the relationship between observations and outcomes undergoes structural change?

The project does not focus on prediction accuracy alone.

Instead, it evaluates whether an intelligent system can:

- recognize when an existing belief remains valid;
- detect when environmental conditions are changing;
- revise beliefs when previous assumptions become unreliable.


---


## 2. Core Concept: Belief Lifecycle

The project is built around the concept of belief lifecycle.

A belief may experience the following stages:
Stable Pattern
    ↓
Structural Change
    ↓
Pattern Invalidity
    ↓
Belief Revision

A successful intelligent system should not only exploit existing patterns, but also recognize when those patterns lose validity.


---


## 3. System Overview

The project consists of three major layers:
            When AI Stops Believing


                     |

          Synthetic Environment Layer


                     |

    -------------------------------------

    |                                   |
    Benchmark Track LAI Track

Belief Revision Transition Intelligence Benchmark Track LAI Track

Belief Revision Transition Intelligence

The Synthetic Environment Layer provides controlled changing environments.

The Benchmark Track evaluates whether AI systems can revise beliefs after structural changes.

The LAI Track investigates whether systems can detect emerging transitions before complete failure occurs.


---


# 4. Shared Synthetic Environment Layer


## 4.1 Purpose

The Synthetic Environment Layer creates reproducible environments where structural changes can be explicitly controlled.

The environment is responsible for generating:

- observable information;
- hidden ground-truth states;
- temporal evolution of the system.


The environment does not make decisions and does not contain AI reasoning mechanisms.


## 4.2 Current Implementation

The first implementation uses a synthetic market environment:

src/market_generator.py


The market environment contains:

Observable variables:

- price;
- return;
- volume;
- momentum;
- signal.


Hidden variables:

- regime;
- structural validity state;
- internal transition parameters.


The hidden variables are used only for evaluation and are not exposed to AI systems.


## 4.3 Design Principle

The synthetic market is not intended to model financial markets.

It is a measurable experimental environment for studying adaptive intelligence under changing conditions.

The same architecture can later be extended to other complex systems, including:

- economic systems;
- scientific discovery processes;
- organizational systems;
- other environments with changing underlying rules.


---


# 5. Benchmark Track


## 5.1 Research Question

The Benchmark Track asks:

> Can an AI system recognize when a previously successful belief becomes invalid?


The focus is belief revision.

The system is evaluated on whether it can:

- maintain useful beliefs when evidence supports them;
- avoid abandoning valid patterns too early;
- update beliefs when structural change occurs.


## 5.2 Architecture

The Benchmark Track follows:

Synthetic Environment
    ↓
Observation Builder
    ↓
AI System
    ↓
Belief Output
    ↓
Evaluation Engine



## 5.3 Principle

The Benchmark Track evaluates intelligence after observing evidence.

It measures:

- adaptation speed;
- persistence of outdated beliefs;
- sensitivity to structural change.


---


# 6. LAI Track


## 6.1 Research Question

The LAI Track asks:

> Can an intelligent system detect that the environment itself is changing?


Unlike the Benchmark Track, LAI focuses on transition awareness.


## 6.2 Architecture

The LAI Track follows:

Synthetic Environment
    ↓
State Representation
    ↓
Transition Detection
    ↓
Adaptation Signal



## 6.3 Principle

LAI does not attempt to replace the Benchmark Track.

Instead, it investigates whether systems can identify structural transitions before a complete belief failure occurs.


---


# 7. Relationship Between Benchmark and LAI


The two tracks study different aspects of adaptive intelligence.

Benchmark:

Environment changes
    ↓
AI receives evidence
    ↓
Can AI revise its belief?

LAI:

Environment changes
    ↓
Can AI detect the transition itself?

The relationship between the two tracks is:

          Synthetic Environment


                  |

          Structural Transition


          /                    \


 Benchmark Track          LAI Track


 Belief Revision       Transition Detection



The Benchmark evaluates adaptation.

The LAI investigates early recognition of environmental change.


---


# 8. Development Roadmap


## Phase 1: Synthetic Environment

Completed:

- controlled environment generation;
- regime transition design;
- temporal alignment;
- reproducible simulation.


## Phase 2: Benchmark Protocol

Next:

- define AI observation interface;
- define belief output format;
- design evaluation metrics;
- benchmark different AI systems.


## Phase 3: LAI Development

Future:

- define system state representation;
- design transition detection mechanisms;
- evaluate early-warning capability.


## Phase 4: Generalization

Extend the framework beyond synthetic markets into broader complex systems.


---


# 9. Architectural Principle


The project separates:

World Generation

    from

Intelligence Evaluation

    from

Transition Detection



This separation ensures that:

- experiments remain reproducible;
- AI evaluation remains fair;
- future intelligent systems can be compared within the same environment.