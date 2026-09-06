# when-ai-stops-believing

An open benchmark studying whether AI systems can recognize when previously useful beliefs become unreliable under changing environments.


# When Should AI Stop Believing?


## Can AI recognize when a previously useful belief no longer describes reality?


An open benchmark studying how AI systems revise beliefs when previously successful assumptions encounter structural changes.


## Research Question


When reality repeatedly contradicts a previously useful belief, how should an AI system determine whether to maintain, reduce confidence in, or revise that belief?


The benchmark studies whether intelligence requires not only learning patterns, but also understanding the conditions under which those patterns remain valid.


## Benchmark Framework


The benchmark is model-independent.


It evaluates AI systems through a standardized belief interface rather than a specific model architecture.


Current components include:


- Synthetic Environment for controlled structural changes;

- Observation Builder for information boundary control;

- Belief Agent for belief maintenance and revision;

- Evaluation Engine for measuring adaptive behavior.


Future experiments can integrate:


- large language models;

- reasoning agents;

- reinforcement learning systems;

- other adaptive intelligence systems.


## Status


Research prototype with a complete benchmark pipeline.


Implemented:

- synthetic environment generation;

- AI observation boundary control;

- structured belief state interface;

- baseline adaptive belief agent;

- evaluation metrics for belief revision.


Current results demonstrate that the benchmark can measure:

- adaptation delay;

- false persistence;

- false abandonment;

- belief boundary awareness.


Future work will extend the benchmark to stronger reasoning agents and the LAI Track.

---


## Repository Structure

when-ai-stops-believing/

├── docs/

│ ├── project_architecture.md

│ ├── benchmark_protocol.md

│ ├── observation_builder_design.md

│ ├── belief_state_design.md

│ ├── evaluation_engine_design.md

│ └── baseline_experiment_report.md

├── src/

│ ├── market_generator.py

│ ├── observation_builder.py

│ ├── belief_interface.py

│ ├── belief_memory.py

│ ├── baseline_belief_agent.py

│ └── evaluation_engine.py

└── data/

    └── synthetic_market.csv



Each module represents an independent layer of the benchmark pipeline.