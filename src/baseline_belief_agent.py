"""Baseline belief agent with historical reliability memory."""

import pandas as pd

from src.belief_interface import create_belief_state
from src.belief_memory import BeliefMemory



def extract_prediction(observation):
    """
    Extract the hypothesis implied by current observable information.

    The agent assumes:
    positive momentum signal should be followed by
    positive future return.

    This is a belief hypothesis,
    not a trading action.
    """

    signal = observation["current_features"]["signal"]

    if pd.isna(signal):
        return None

    if signal == 1:
        return "positive"

    return "negative"



def evaluate_belief(
    observation,
    memory,
    previous_status="VALID",
    confidence=0.8,
):
    """
    Update belief status using current evidence
    and historical reliability.

    Only AI-visible information and memory are used.
    """

    momentum = observation["current_features"]["momentum_20d"]


    # Warm-up period.
    # Lack of evidence is not evidence of failure.
    if pd.isna(momentum):

        return create_belief_state(
            timestamp=observation["timestamp"],
            belief_status=previous_status,
            confidence=confidence,
            explanation=(
                "Insufficient historical information "
                "during warm-up period"
            ),
        )


    reliability = memory.success_rate()

    evidence_count = memory.evidence_count()


    # Once a belief is considered INVALID,
    # it remains invalid until a future
    # revalidation mechanism is introduced.
    #
    # This prevents short-term evidence
    # from immediately restoring a failed belief.

    if previous_status == "INVALID":

        return create_belief_state(
            timestamp=observation["timestamp"],
            belief_status="INVALID",
            confidence=confidence,
            explanation=(
                "Belief remains invalid "
                "until revalidation"
            ),
        )


    # Not enough historical evidence yet.
    if reliability is None or evidence_count < 10:

        return create_belief_state(
            timestamp=observation["timestamp"],
            belief_status=previous_status,
            confidence=confidence,
            explanation=(
                "Belief maintained due to insufficient "
                "historical evidence"
            ),
        )


    # Strong historical support.
    if reliability >= 0.7:

        confidence = min(
            confidence + 0.02,
            1.0
        )

        status = "VALID"


    # Possible structural change.
    elif reliability < 0.5:

        confidence = max(
            confidence - 0.05,
            0.0
        )

        if confidence < 0.2:

            status = "INVALID"

        else:

            status = "UNCERTAIN"


    # Intermediate uncertainty.
    else:

        confidence = max(
            confidence - 0.02,
            0.0
        )

        if confidence < 0.4:

            status = "UNCERTAIN"

        else:

            status = previous_status



    return create_belief_state(
        timestamp=observation["timestamp"],
        belief_status=status,
        confidence=confidence,
        explanation=(
            "Baseline belief update using "
            "historical reliability"
        ),
    )



def update_memory_from_previous_prediction(
    memory,
    previous_prediction,
    current_observation,
):
    """
    Update memory after the next observation arrives.

    This preserves temporal causality.

    Prediction from t is evaluated using
    information available at t+1.
    """

    if previous_prediction is None:
        return


    current_return = (
        current_observation["current_features"]
        ["historical_return"]
    )


    if pd.isna(current_return):
        return


    if current_return > 0:

        outcome = "positive"

    else:

        outcome = "negative"


    memory.update(
        previous_prediction,
        outcome
    )



def run_baseline_agent(
    observations,
):
    """
    Generate a complete belief trajectory.

    The agent:
    1. receives Observation(t)
    2. updates belief
    3. stores prediction
    4. evaluates previous prediction
       when next observation arrives
    """

    history = []

    memory = BeliefMemory(
        window_size=50
    )


    status = "VALID"

    confidence = 0.8


    previous_prediction = None


    for observation in observations:


        # Evaluate previous belief prediction
        # using newly available outcome.
        update_memory_from_previous_prediction(
            memory,
            previous_prediction,
            observation,
        )


        belief = evaluate_belief(
            observation,
            memory,
            status,
            confidence,
        )


        status = belief["belief_status"]

        confidence = belief["confidence"]


        history.append(
            belief
        )


        # Store current hypothesis.
        previous_prediction = extract_prediction(
            observation
        )


    return history