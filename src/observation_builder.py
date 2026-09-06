"""Build AI-visible observations from synthetic market data."""

from pathlib import Path

import json

import pandas as pd


OBSERVATION_COLUMNS = [
    "price",
    "historical_return",
    "volume",
    "momentum_20d",
    "signal",
]


FORBIDDEN_COLUMNS = [
    "regime",
    "beta",
    "driver",
]


def load_market_data(path):
    """
    Load synthetic market dataset.

    The dataset may contain hidden evaluation variables.
    These variables must be removed before AI access.
    """
    return pd.read_csv(path)


def validate_observation_boundary(observation):
    """
    Ensure hidden variables are not included in AI observations.
    """

    forbidden = set(FORBIDDEN_COLUMNS)

    if forbidden.intersection(observation.keys()):
        raise ValueError(
            "Observation contains forbidden hidden variables"
        )

    return True


def build_observation(row, previous_belief_state=None):
    """
    Convert one environment state into an AI observation.
    """

    observation = {
        "timestamp": row["date"],

        "market_history": [],

        "current_features": {
            "price": row["price"],
            "historical_return": row["return"],
            "volume": row["volume"],
            "momentum_20d": row["momentum_20d"],
            "signal": row["signal"],
        },

        "previous_belief_state": previous_belief_state,
    }

    validate_observation_boundary(
        observation
    )

    return observation


def build_observation_sequence(
    dataframe,
):
    """
    Convert full market dataset into AI observations.
    """

    observations = []

    previous_belief_state = None

    for _, row in dataframe.iterrows():

        observation = build_observation(
            row,
            previous_belief_state,
        )

        observations.append(
            observation
        )

    return observations


def save_observations(
    observations,
    output_path,
):
    """
    Save observation sequence as JSON.
    """

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            observations,
            f,
            indent=4,
            ensure_ascii=False,
        )

    return output_path