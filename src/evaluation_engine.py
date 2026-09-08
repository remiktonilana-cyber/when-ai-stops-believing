"""Evaluation engine for adaptive intelligence benchmark."""

import pandas as pd



def load_environment_state(path):
    """
    Load hidden environment information for evaluation.

    Hidden variables are only available inside the evaluation layer.
    """

    return pd.read_csv(path)



def load_belief_history(path):
    """
    Load AI belief trajectory.
    """

    return pd.read_json(path)



def get_transition_reference(environment):
    """
    Identify structural transition timing from ground truth regime.

    The evaluation engine does not define invalidation.
    It reads predefined environment transitions.
    """

    regimes = environment["regime"]

    transition_points = []

    previous_regime = regimes.iloc[0]

    for index, regime in enumerate(regimes):

        if regime != previous_regime:

            transition_points.append(
                {
                    "day": index,
                    "from": previous_regime,
                    "to": regime,
                }
            )

            previous_regime = regime

    return transition_points



def get_belief_change_points(belief_history):
    """
    Identify when AI belief status changes.
    """

    changes = []

    previous_status = (
        belief_history.iloc[0]["belief_status"]
    )

    for index, status in enumerate(
        belief_history["belief_status"]
    ):

        if status != previous_status:

            changes.append(
                {
                    "day": index,
                    "from": previous_status,
                    "to": status,
                }
            )

            previous_status = status

    return changes



def compare_transition_and_belief(
    environment,
    belief_history,
):
    """
    Compare environment transitions with AI belief changes.
    """

    return {
        "environment_transitions":
            get_transition_reference(environment),

        "belief_changes":
            get_belief_change_points(
                belief_history
            ),
    }



def get_invalid_transition_day(environment):
    """
    Return the first day when environment becomes INVALID.
    """

    transitions = get_transition_reference(
        environment
    )

    for transition in transitions:

        if transition["to"] == "INVALID":

            return transition["day"]


    raise ValueError(
        "No INVALID transition found"
    )



def calculate_adaptation_delay(
    environment,
    belief_history,
):
    """
    Calculate time required for AI to recognize
    structural invalidation.
    """

    invalid_transition_day = (
        get_invalid_transition_day(
            environment
        )
    )


    invalid_days = belief_history[
        belief_history["belief_status"] == "INVALID"
    ]


    if invalid_days.empty:

        return None


    first_invalid_day = invalid_days.index[0]


    return (
        first_invalid_day
        -
        invalid_transition_day
    )



def calculate_false_persistence(
    environment,
    belief_history,
):
    """
    Measure how long AI maintains a VALID belief
    after the environment becomes INVALID.
    """

    invalid_transition_day = (
        get_invalid_transition_day(
            environment
        )
    )


    post_invalid = belief_history.iloc[
        invalid_transition_day:
    ]


    valid_days = post_invalid[
        post_invalid["belief_status"]
        == "VALID"
    ]


    if valid_days.empty:

        return 0


    return (
        valid_days.index[-1]
        -
        invalid_transition_day
        +
        1
    )



def calculate_false_abandonment(
    environment,
    belief_history,
):
    """
    Count INVALID beliefs while ground truth remains stably VALID.

    UNCERTAIN is a boundary state, not abandonment.
    """

    transitions = get_transition_reference(
        environment
    )

    valid_end_day = None

    for transition in transitions:

        if transition["from"] == "VALID":

            valid_end_day = transition["day"]

            break


    if valid_end_day is None:

        raise ValueError(
            "No VALID period found"
        )


    stable_valid_period = belief_history.iloc[
        :valid_end_day
    ]


    abandoned_days = stable_valid_period[
        stable_valid_period["belief_status"]
        == "INVALID"
    ]


    return len(abandoned_days)



def calculate_belief_boundary_awareness(
    environment,
    belief_history,
):
    """
    Measure whether AI enters uncertainty
    before complete structural invalidation.

    A larger value means earlier awareness
    of a changing knowledge boundary.
    """

    invalid_transition_day = (
        get_invalid_transition_day(
            environment
        )
    )


    before_invalid = belief_history.iloc[
        :invalid_transition_day
    ]


    uncertain_days = before_invalid[
        before_invalid["belief_status"]
        == "UNCERTAIN"
    ]


    if uncertain_days.empty:

        return None


    first_uncertain_day = (
        uncertain_days.index[0]
    )


    return (
        invalid_transition_day
        -
        first_uncertain_day
    )
