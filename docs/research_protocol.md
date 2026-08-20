# Research Protocol

## 1. Research Question
# Research Protocol
Can AI distinguish a temporary drawdown from the death of a profitable market belief?

When a previously profitable market pattern stops working, can AI determine whether the failure is temporary noise or evidence that the underlying belief has permanently lost its validity?

The goal of this research is not to predict financial markets, but to evaluate how AI systems update beliefs when facing changing evidence in complex environments.

## 2. Research Motivation

Complex environments require intelligent systems that can adapt when previous knowledge becomes unreliable.

Modern AI systems have demonstrated strong capabilities in pattern recognition and prediction. However, a more fundamental challenge remains: when a previously successful belief fails, how should an intelligent system decide whether to maintain, adjust, or abandon that belief?

This research uses financial markets as a measurable testing environment to study belief revision under uncertainty. Financial markets provide historical patterns, continuous feedback, and observable outcomes, allowing us to evaluate how different AI systems update their judgments when confronted with changing evidence.

The goal is not to build a stock prediction model, but to investigate a broader question: how can intelligent systems adapt their understanding when the world no longer behaves according to previous assumptions?

## 3. Hypothesis

This research investigates the following hypotheses:

### H1: Different AI systems exhibit different belief revision behaviors.

When exposed to identical evidence, different AI systems may update their beliefs at different speeds and in different directions.

### H2: Faster belief updates do not necessarily indicate superior intelligence.

An intelligent system should balance adaptation and stability. Overreacting to temporary noise may be as problematic as failing to recognize structural change.

### H3: AI systems may struggle to distinguish temporary noise from permanent changes.

A key challenge for intelligent systems is determining whether a failed pattern represents short-term uncertainty or the disappearance of the underlying relationship.

## 4. Experimental Design

This research follows a two-stage experimental framework.

### Phase 1: Synthetic Market Environment

A controlled synthetic environment will be created where the underlying market relationship is predefined. This allows us to know whether a previously profitable belief is truly maintained or has structurally disappeared.

The purpose of this phase is to evaluate whether AI systems can distinguish temporary fluctuations from permanent changes under controlled conditions.

### Phase 2: Real Market Validation

After evaluating AI behavior in controlled environments, the framework will be applied to real market data.

The purpose of this phase is to examine whether the observed belief revision patterns remain meaningful in complex real-world environments.

### Experimental Principle

The first version of this benchmark focuses on belief revision rather than pattern discovery.

Market patterns will be predefined before evaluation. This separation allows us to measure how AI systems update beliefs when evidence contradicts previous assumptions.

## 5. AI Models

This benchmark evaluates multiple AI systems under identical experimental conditions.

The selected models include:

- DeepSeek
- GPT
- Grok
- Qwen

The purpose of this benchmark is not to rank which AI system is universally superior. Instead, it investigates whether different AI systems exhibit different belief revision behaviors when facing changing evidence.

Each AI system will receive identical information, identical tasks, and identical evaluation criteria.

The evaluation focuses on how AI systems update their beliefs under uncertainty, including:

- whether the system recognizes when previous assumptions become invalid;
- how quickly the system adjusts its confidence after receiving new evidence;
- whether the adjustment direction is consistent with the actual underlying environment;
- whether confidence levels are appropriately calibrated with observed outcomes.

The benchmark evaluates adaptive decision behavior rather than prediction accuracy alone.

A stronger system is not defined as the one that changes its belief fastest, but as the one that achieves a better balance between stability and adaptation.

## 6. Input Format

To ensure fair comparison across AI systems, all models will receive identical structured inputs.

The input design consists of four components:

### 1. Historical Belief

The model receives information describing a previously successful pattern, including historical performance, consistency, and reliability indicators.

### 2. New Evidence

The model receives new observations showing changes in performance. These signals are designed to represent either temporary fluctuations or structural changes.

### 3. Context Variables

Additional environmental information is provided, including relevant market conditions and external factors that may influence the interpretation of new evidence.

### 4. Decision Task

Each AI system must answer standardized questions:

- Is the original belief still valid?
- What is the confidence level of this judgment?
- Should the belief be maintained, monitored, or abandoned?
- What evidence contributed most to the updated judgment?

The benchmark evaluates how AI systems update their judgments under identical information conditions.

## 7. Output Format

To enable quantitative comparison, all AI systems must provide structured outputs under the same format.

Each response should include the following components:

### 1. Belief Probability

The estimated probability that the original market belief remains valid (0-100%).

### 2. Decision

The AI system must select one of three standardized decisions:

- MAINTAIN: Continue believing the original pattern remains valid.
- MONITOR: Reduce confidence and continue observing additional evidence.
- ABANDON: Consider the original pattern no longer valid.

### 3. Confidence Level

The confidence level of the AI system's judgment (0-100%).

### 4. Key Evidence

The AI system identifies the most influential evidence that contributed to its judgment update.

### 5. Brief Explanation

A concise explanation of the decision.

The benchmark does not evaluate hidden reasoning processes. Instead, it evaluates observable belief revision behavior through structured outputs.

## 8. Evaluation Metrics

The benchmark evaluates AI belief revision behavior through multiple complementary metrics.

A stronger AI system is not defined as the one that changes its belief fastest, but as the one that achieves an appropriate balance between stability and adaptation.

### 1. Belief Update Magnitude

Measures whether an AI system adjusts its belief after receiving new evidence.

The metric captures the magnitude of belief change between initial and updated confidence levels.

### 2. Regime Recognition Accuracy

Measures whether the AI system correctly identifies whether the original pattern remains valid or has structurally disappeared.

This metric evaluates the direction of belief adjustment rather than the magnitude alone.

### 3. Detection Lag

Measures the delay between the actual change of the underlying environment and the AI system's recognition of that change.

The objective is not minimum delay, but appropriate adaptation timing.

### 4. False Abandonment Rate

Measures how frequently an AI system incorrectly abandons a valid pattern due to temporary fluctuations.

### 5. Confidence Calibration

Measures whether the confidence level expressed by an AI system corresponds to its actual performance.

The benchmark combines these metrics to evaluate adaptive intelligence under changing environments.

## 9. Experimental Constraints

To ensure scientific validity and fair comparison, the benchmark follows several experimental constraints.

### 1. Same Information

All AI systems receive identical information, including historical beliefs, new evidence, and contextual variables.

### 2. Same Prompt Structure

All models are evaluated using the same standardized prompt format to minimize differences caused by task interpretation.

### 3. No Future Leakage

AI systems are not provided with future outcomes during evaluation. Decisions must be based only on information available at the evaluation point.

### 4. Predefined Evaluation Rules

Evaluation metrics and scoring procedures are defined before experiments are conducted and are not modified based on model performance.

### 5. No Manual Intervention

AI responses are recorded without subjective modification. Human evaluation focuses only on predefined metrics.

### 6. Reproducibility

All experiments will record model versions, prompts, inputs, and outputs to enable independent reproduction.

## 10. Future Extensions

This benchmark provides a foundation for studying adaptive intelligence under changing environments.

Future extensions may include:

### 1. More Complex Environments

The framework can be extended beyond financial markets to other complex domains, including economic systems, organizational decisions, and scientific discovery.

### 2. Multi-Agent Evaluation

Future versions may evaluate how multiple AI agents with different roles and information sources coordinate and update their beliefs collectively.

### 3. Human-AI Comparison

The benchmark can be extended to compare human and AI belief revision behaviors under similar uncertainty conditions.

### 4. Adaptive Decision Systems

The framework may contribute to the development of intelligent decision systems that can continuously update their understanding when facing changing environments.