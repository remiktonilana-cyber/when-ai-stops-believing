"""Build causally valid AI-visible observations from synthetic market data."""

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


def _json_safe(value):
    """
    Convert pandas / NumPy scalar values into JSON-safe Python values.

    Missing observable values are represented as None rather than NaN.
    """
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if hasattr(value, "item"):
        return value.item()

    return value


def _validate_no_forbidden_keys(value):
    """
    Recursively ensure hidden environment variables do not appear
    anywhere inside an AI-visible observation.
    """
    forbidden = set(FORBIDDEN_COLUMNS)

    if isinstance(value, dict):
        hidden_keys = forbidden.intersection(value.keys())

        if hidden_keys:
            raise ValueError(
                "Observation contains forbidden hidden variables: "
                + ", ".join(sorted(hidden_keys))
            )

        for nested_value in value.values():
            _validate_no_forbidden_keys(nested_value)

    elif isinstance(value, list):
        for nested_value in value:
            _validate_no_forbidden_keys(nested_value)


def validate_observation_boundary(observation):
    """
    Ensure hidden variables are not included anywhere
    in AI-visible observations.
    """
    _validate_no_forbidden_keys(observation)
    return True


def build_observation(
    row,
    previous_belief_state=None,
    historical_return=None,
):
    """
    Convert one environment state into a causally valid AI observation.

    The synthetic-market CSV stores Return_(t+1) on row t.
    Therefore row["return"] must not be exposed in observation t.

    historical_return must instead contain the return that became
    realized before the current timestep, i.e. Return_t.
    """
    observation = {
        "timestamp": _json_safe(row["date"]),
        "market_history": [],
        "current_features": {
            "price": _json_safe(row["price"]),
            "historical_return": _json_safe(historical_return),
            "volume": _json_safe(row["volume"]),
            "momentum_20d": _json_safe(row["momentum_20d"]),
            "signal": _json_safe(row["signal"]),
        },
        "previous_belief_state": previous_belief_state,
    }

    validate_observation_boundary(observation)

    return observation


def build_observation_sequence(dataframe):
    """
    Convert the full market dataset into causally ordered AI observations.

    For observation t:

        price               = Price_t
        momentum_20d        = Momentum_t
        signal              = Signal_t
        historical_return   = Return_t

    Because the source CSV stores Return_(t+1) on row t,
    observation t receives the return stored on row t-1.

    The first observation has no historically realized return.
    """
    observations = []

    historical_return = None
    previous_belief_state = None

    for _, row in dataframe.iterrows():
        observation = build_observation(
            row=row,
            previous_belief_state=previous_belief_state,
            historical_return=historical_return,
        )

        observations.append(observation)

        # row["return"] is Return_(t+1), which becomes historical
        # only for the next observation.
        historical_return = _json_safe(row["return"])

    return observations


def save_observations(
    observations,
    output_path,
):
    """
    Save observation sequence as standards-compliant JSON.
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
            allow_nan=False,
        )

    return output_path