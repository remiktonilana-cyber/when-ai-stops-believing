"""Reproducible synthetic market data generator."""

from pathlib import Path

import numpy as np
import pandas as pd


CONFIG = None
RETURN_RNG = None
VOLUME_RNG = None


def load_config():
    """Return the default simulation configuration."""
    return {
        "experiment_id": "momentum_decay_seed_42",
        "random_seed": 42,
        "simulation_days": 2000,
        "start_date": "2000-01-03",
        "initial_price": 100.0,
        "momentum_window": 20,
        "warmup_days": 20,
        "momentum_scale": 0.10,
        "signal_threshold": 0.0,
        "valid_end": 999,
        "transition_start": 1000,
        "transition_end": 1299,
        "invalid_start": 1300,
        "valid_beta": 0.005,
        "invalid_beta": 0.0,
        "noise_std": 0.01,
        "volume_log_mean": np.log(1_000_000),
        "volume_log_std": 0.25,
        "output_path": Path(__file__).resolve().parents[1]
        / "data"
        / "synthetic_market.csv",
    }


def _config():
    """Return the active configuration, loading defaults when necessary."""
    global CONFIG
    if CONFIG is None:
        CONFIG = load_config()
    return CONFIG


def _initialize_rngs():
    """Initialize independent return-noise and volume random streams."""
    global RETURN_RNG, VOLUME_RNG
    child_seeds = np.random.SeedSequence(_config()["random_seed"]).spawn(2)
    RETURN_RNG = np.random.default_rng(child_seeds[0])
    VOLUME_RNG = np.random.default_rng(child_seeds[1])


def _return_rng():
    """Return the active return-noise random number generator."""
    if RETURN_RNG is None:
        _initialize_rngs()
    return RETURN_RNG


def _volume_rng():
    """Return the active volume random number generator."""
    if VOLUME_RNG is None:
        _initialize_rngs()
    return VOLUME_RNG


def get_regime(day):
    """Return the hidden market regime for a zero-based trading day."""
    config = _config()
    if day < 0 or day >= config["simulation_days"]:
        raise ValueError("day is outside the configured simulation range")
    if day <= config["valid_end"]:
        return "VALID"
    if day <= config["transition_end"]:
        return "TRANSITION"
    return "INVALID"


def calculate_beta(day, regime):
    """Return the Stable Momentum Driver coefficient for a day and regime."""
    config = _config()
    expected_regime = get_regime(day)
    if regime != expected_regime:
        raise ValueError(f"day {day} belongs to {expected_regime}, not {regime}")

    if regime == "VALID":
        return config["valid_beta"]
    if regime == "INVALID":
        return config["invalid_beta"]

    transition_length = config["transition_end"] - config["transition_start"]
    progress = (day - config["transition_start"]) / transition_length
    beta_range = config["invalid_beta"] - config["valid_beta"]
    return config["valid_beta"] + progress * beta_range


def generate_return(momentum, beta):
    """Generate the next return using the latent Stable Momentum Driver."""
    driver = (
        0.0
        if pd.isna(momentum)
        else float(np.tanh(float(momentum) / _config()["momentum_scale"]))
    )
    noise = _return_rng().normal(0.0, _config()["noise_std"])
    return_value = float(beta * driver + noise)
    if not np.isfinite(return_value):
        raise ValueError("generated return must be finite")
    return return_value


def update_price(previous_price, return_value):
    """Apply a simple daily return to the previous price."""
    if not np.isfinite(previous_price) or previous_price <= 0:
        raise ValueError("previous_price must be finite and positive")
    if not np.isfinite(return_value) or return_value <= -1:
        raise ValueError("return_value must be finite and greater than -1")
    updated_price = float(previous_price * (1.0 + return_value))
    if not np.isfinite(updated_price) or updated_price <= 0:
        raise ValueError("updated price must be finite and positive")
    return updated_price


def calculate_features(price_history):
    """Calculate causal 20-day momentum and its binary trading signal."""
    config = _config()
    if len(price_history) <= config["warmup_days"]:
        return np.nan, np.nan

    window = config["momentum_window"]
    momentum = float(price_history[-1] / price_history[-(window + 1)] - 1.0)
    signal = int(momentum > config["signal_threshold"])
    return momentum, signal


def save_dataset(data):
    """Save simulation records, including hidden ground truth, as CSV."""
    config = _config()
    columns = [
        "experiment_id",
        "date",
        "price",
        "return",
        "volume",
        "momentum_20d",
        "signal",
        "regime",
    ]
    dataset = pd.DataFrame(data, columns=columns)
    dataset["signal"] = dataset["signal"].astype("Int64")
    output_path = config["output_path"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(output_path, index=False)
    return output_path


def main():
    """Export rows of time-t information paired with the next-period return."""
    global CONFIG, RETURN_RNG, VOLUME_RNG
    CONFIG = load_config()
    RETURN_RNG = None
    VOLUME_RNG = None
    _initialize_rngs()

    dates = pd.bdate_range(CONFIG["start_date"], periods=CONFIG["simulation_days"])
    price_history = [CONFIG["initial_price"]]
    records = []

    for day, date in enumerate(dates):
        regime = get_regime(day)
        beta = calculate_beta(day, regime)

        # The row's observable information is fixed before its return is drawn.
        current_price = price_history[-1]
        momentum, signal = calculate_features(price_history)
        volume = float(
            _volume_rng().lognormal(
                CONFIG["volume_log_mean"], CONFIG["volume_log_std"]
            )
        )

        # The hidden regime governs the return realized after that state.
        next_return = generate_return(momentum, beta)

        records.append(
            {
                "experiment_id": CONFIG["experiment_id"],
                "date": date.strftime("%Y-%m-%d"),
                "price": current_price,
                "return": next_return,
                "volume": volume,
                "momentum_20d": momentum,
                "signal": signal,
                "regime": regime,
            }
        )
        next_price = update_price(current_price, next_return)
        price_history.append(next_price)

    output_path = save_dataset(records)
    print(f"Generated {len(records)} rows at {output_path}")


if __name__ == "__main__":
    main()
