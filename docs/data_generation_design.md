# Data Generation Design

## 1. Objective

The purpose of the synthetic data generation process is to create a controlled market environment for evaluating AI belief revision.

Each variable is designed to support the research question: whether AI systems can distinguish temporary underperformance from permanent structural change.

## 2. Data Schema

The synthetic market dataset consists of three layers:

### 1. Observable Market Variables

Variables provided to AI systems during evaluation.

### 2. Hidden Ground Truth Variables

Variables used only for evaluation and not exposed to AI systems.

### 3. Experiment Metadata

Variables used to ensure reproducibility.

## 3. Dataset Fields

| Variable | Description | AI Visible |
|----------|-------------|------------|
| date | Trading day identifier | Yes |
| price | Synthetic asset price | Yes |
| return | Daily return | Yes |
| volume | Trading activity indicator | Yes |
| momentum_20d | 20-day momentum signal | Yes |
| signal | Trading rule indicator | Yes |
| regime | True market state label | No |