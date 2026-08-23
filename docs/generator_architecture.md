# Generator Architecture

## 1. Objective

The purpose of the market generator is to create a reproducible synthetic environment for evaluating AI belief revision capabilities.

The generator should simulate a market where a previously profitable relationship can emerge, weaken, and eventually disappear.

The system is not designed to predict financial returns. Instead, it creates a controlled environment where the true timing of structural change is known and AI adaptation can be measured.

## 2. System Architecture Overview

The generator is designed as a modular synthetic environment engine.

The system consists of five major components:

Configuration Layer
        ↓
Regime Controller
        ↓
Market Simulator
        ↓
Feature Calculator
        ↓
Data Exporter

Each component has a clearly defined responsibility to ensure reproducibility, interpretability, and future extensibility.

### Configuration Layer

Manages experiment parameters, including initial conditions, simulation length, and signal parameters.

### Regime Controller

Determines the current market state and controls the transition between VALID, TRANSITION, and INVALID regimes.

### Market Simulator

Generates market returns according to the current regime and the relationship between momentum signals and future returns.

### Feature Calculator

Transforms raw market observations into features visible to AI systems, such as momentum indicators and trading signals.

### Data Exporter

Stores generated observations into a structured dataset for downstream AI evaluation.