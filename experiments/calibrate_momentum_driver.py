"""Compare stable-momentum-driver parameters without selecting a winner."""

import numpy as np
import pandas as pd


SIMULATION_DAYS = 2000
INITIAL_PRICE = 100.0
MOMENTUM_WINDOW = 20
VALID_END = 999
TRANSITION_START = 1000
TRANSITION_END = 1299
NOISE_STD = 0.01
RANDOM_SEED = 42
ROBUSTNESS_SEEDS = (42, 123, 456, 789, 2026)
STRESS_TEST_SEEDS = tuple(range(1, 21))

SCALES = (0.05, 0.10, 0.20)
VALID_BETAS = (0.001, 0.0025, 0.005, 0.01)
REGIMES = ("VALID", "TRANSITION", "INVALID")
ROBUSTNESS_CANDIDATES = {
    "A": {"scale": 0.10, "beta_valid": 0.005},
    "B": {"scale": 0.20, "beta_valid": 0.010},
    "C": {"scale": 0.10, "beta_valid": 0.0025},
}


def get_regime(day):
    """Return the documented regime for a zero-based simulation day."""
    if day <= VALID_END:
        return "VALID"
    if day <= TRANSITION_END:
        return "TRANSITION"
    return "INVALID"


def calculate_beta(day, regime, beta_valid):
    """Keep beta stable in VALID, decay it in TRANSITION, then set it to zero."""
    if regime == "VALID":
        return beta_valid
    if regime == "INVALID":
        return 0.0

    transition_length = TRANSITION_END - TRANSITION_START
    progress = (day - TRANSITION_START) / transition_length
    return beta_valid * (1.0 - progress)


def simulate(scale, beta_valid, noise):
    """Simulate one parameter pair using a shared, pre-generated noise path."""
    prices = [INITIAL_PRICE]
    records = []

    for day in range(SIMULATION_DAYS):
        current_price = prices[-1]
        if len(prices) <= MOMENTUM_WINDOW:
            momentum = np.nan
            driver = 0.0
        else:
            momentum = current_price / prices[-(MOMENTUM_WINDOW + 1)] - 1.0
            driver = float(np.tanh(momentum / scale))

        regime = get_regime(day)
        beta = calculate_beta(day, regime, beta_valid)
        next_return = float(beta * driver + noise[day])
        next_price = float(current_price * (1.0 + next_return))

        records.append(
            {
                "regime": regime,
                "momentum": momentum,
                "driver": driver,
                "return": next_return,
                "price": current_price,
                "next_price": next_price,
            }
        )
        prices.append(next_price)

    return pd.DataFrame.from_records(records)


def correlation(frame):
    """Calculate feature-target correlation after removing the warm-up rows."""
    aligned = frame[["momentum", "return"]].dropna()
    if len(aligned) < 2:
        return np.nan
    return float(aligned["momentum"].corr(aligned["return"]))


def summarize(frame, scale, beta_valid):
    """Calculate stability and regime diagnostics for one simulation."""
    result = {"scale": scale, "beta_valid": beta_valid}

    for regime in REGIMES:
        regime_frame = frame.loc[frame["regime"] == regime]
        prefix = regime.lower()
        result[f"{prefix}_corr"] = correlation(regime_frame)
        result[f"{prefix}_mean_ret"] = float(regime_frame["return"].mean())
        result[f"{prefix}_std_ret"] = float(
            regime_frame["return"].std(ddof=0)
        )

    valid_observations = frame.loc[
        (frame["regime"] == "VALID") & frame["momentum"].notna()
    ]
    result["valid_pos_mom_rate"] = float(
        (valid_observations["momentum"] > 0.0).mean()
    )
    result["valid_saturation_rate"] = float(
        (valid_observations["driver"].abs() > 0.95).mean()
    )
    result["min_price"] = float(
        min(frame["price"].min(), frame["next_price"].min())
    )
    result["max_price"] = float(
        max(frame["price"].max(), frame["next_price"].max())
    )

    expected_warmup_nan = bool(frame["momentum"].iloc[:MOMENTUM_WINDOW].isna().all())
    post_warmup = frame.iloc[MOMENTUM_WINDOW:]
    stability_values = post_warmup[
        ["momentum", "driver", "return", "price", "next_price"]
    ].to_numpy()
    result["expected_warmup_nan"] = expected_warmup_nan
    result["unexpected_nan_inf"] = bool((~np.isfinite(stability_values)).any())
    return result


def run_parameter_grid():
    """Return diagnostics for the original single-seed parameter grid."""
    noise = np.random.default_rng(RANDOM_SEED).normal(
        0.0, NOISE_STD, size=SIMULATION_DAYS
    )
    results = []

    for scale in SCALES:
        for beta_valid in VALID_BETAS:
            frame = simulate(scale, beta_valid, noise)
            results.append(summarize(frame, scale, beta_valid))

    return pd.DataFrame(results).sort_values(
        ["scale", "beta_valid"], ignore_index=True
    )


def run_robustness_test():
    """Return candidate diagnostics for every requested random seed."""
    results = []

    for seed in ROBUSTNESS_SEEDS:
        noise = np.random.default_rng(seed).normal(
            0.0, NOISE_STD, size=SIMULATION_DAYS
        )
        for candidate, parameters in ROBUSTNESS_CANDIDATES.items():
            frame = simulate(parameters["scale"], parameters["beta_valid"], noise)
            summary = summarize(
                frame, parameters["scale"], parameters["beta_valid"]
            )
            results.append(
                {
                    "candidate": candidate,
                    "seed": seed,
                    "scale": parameters["scale"],
                    "beta_valid": parameters["beta_valid"],
                    "valid_corr": summary["valid_corr"],
                    "transition_corr": summary["transition_corr"],
                    "invalid_corr": summary["invalid_corr"],
                    "valid_pos_mom_rate": summary["valid_pos_mom_rate"],
                    "valid_saturation_rate": summary["valid_saturation_rate"],
                    "min_price": summary["min_price"],
                    "max_price": summary["max_price"],
                    "nan_inf": summary["unexpected_nan_inf"],
                }
            )

    return pd.DataFrame(results).sort_values(
        ["candidate", "seed"], ignore_index=True
    )


def aggregate_robustness(seed_results):
    """Aggregate robustness diagnostics by candidate without ranking them."""
    rows = []

    for candidate, group in seed_results.groupby("candidate", sort=True):
        rows.append(
            {
                "candidate": candidate,
                "scale": float(group["scale"].iloc[0]),
                "beta_valid": float(group["beta_valid"].iloc[0]),
                "mean_valid_corr": float(group["valid_corr"].mean()),
                "std_valid_corr": float(group["valid_corr"].std(ddof=0)),
                "mean_transition_corr": float(group["transition_corr"].mean()),
                "mean_invalid_corr": float(group["invalid_corr"].mean()),
                "min_valid_pos_mom_rate": float(group["valid_pos_mom_rate"].min()),
                "max_valid_pos_mom_rate": float(group["valid_pos_mom_rate"].max()),
                "max_valid_saturation_rate": float(
                    group["valid_saturation_rate"].max()
                ),
                "ordered_corr_seed_count": int(
                    (
                        (group["valid_corr"] > group["transition_corr"])
                        & (group["transition_corr"] > group["invalid_corr"])
                    ).sum()
                ),
            }
        )

    return pd.DataFrame(rows)


def run_candidate_a_stress_test():
    """Run the fixed Candidate A specification over 20 deterministic seeds."""
    parameters = ROBUSTNESS_CANDIDATES["A"]
    results = []

    for seed in STRESS_TEST_SEEDS:
        noise = np.random.default_rng(seed).normal(
            0.0, NOISE_STD, size=SIMULATION_DAYS
        )
        frame = simulate(parameters["scale"], parameters["beta_valid"], noise)
        summary = summarize(frame, parameters["scale"], parameters["beta_valid"])
        results.append(
            {
                "seed": seed,
                "valid_corr": summary["valid_corr"],
                "transition_corr": summary["transition_corr"],
                "invalid_corr": summary["invalid_corr"],
                "valid_pos_mom_rate": summary["valid_pos_mom_rate"],
                "valid_saturation_rate": summary["valid_saturation_rate"],
                "min_price": summary["min_price"],
                "max_price": summary["max_price"],
                "nan_inf": summary["unexpected_nan_inf"],
            }
        )

    return pd.DataFrame(results).sort_values("seed", ignore_index=True)


def aggregate_candidate_a_stress(seed_results):
    """Aggregate Candidate A stress outcomes without changing its parameters."""
    result = {
        "seed_count": len(seed_results),
        "min_valid_pos_mom_rate": float(seed_results["valid_pos_mom_rate"].min()),
        "max_valid_pos_mom_rate": float(seed_results["valid_pos_mom_rate"].max()),
        "max_valid_saturation_rate": float(
            seed_results["valid_saturation_rate"].max()
        ),
        "min_price_all_runs": float(seed_results["min_price"].min()),
        "max_price_all_runs": float(seed_results["max_price"].max()),
    }

    for regime in ("valid", "transition", "invalid"):
        correlations = seed_results[f"{regime}_corr"]
        result[f"mean_{regime}_corr"] = float(correlations.mean())
        result[f"std_{regime}_corr"] = float(correlations.std(ddof=0))
        result[f"min_{regime}_corr"] = float(correlations.min())
        result[f"max_{regime}_corr"] = float(correlations.max())

    ordered = (
        (seed_results["valid_corr"] > seed_results["transition_corr"])
        & (seed_results["transition_corr"] > seed_results["invalid_corr"])
    )
    result["ordered_corr_seed_count"] = int(ordered.sum())
    result["ordered_corr_seed_pct"] = float(100.0 * ordered.mean())
    result["positive_valid_corr_seed_count"] = int(
        (seed_results["valid_corr"] > 0.0).sum()
    )
    result["neutral_invalid_corr_seed_count"] = int(
        (seed_results["invalid_corr"].abs() < 0.10).sum()
    )
    result["finite_seed_count"] = int((~seed_results["nan_inf"]).sum())
    return pd.DataFrame([result])


def print_table(frame):
    """Print a DataFrame with compact, consistent floating-point formatting."""
    float_columns = frame.select_dtypes(include=["floating"]).columns
    formatters = {column: "{:.6f}".format for column in float_columns}
    print(frame.to_string(index=False, formatters=formatters))


def main():
    """Print calibration and robustness diagnostics without selecting a winner."""
    print("Single-seed parameter grid (seed 42)")
    print_table(run_parameter_grid())

    seed_results = run_robustness_test()
    print("\nMulti-seed candidate results")
    print_table(seed_results)

    print("\nMulti-seed aggregate summary (VALID correlation std uses ddof=0)")
    print_table(aggregate_robustness(seed_results))

    stress_results = run_candidate_a_stress_test()
    print(
        "\nCandidate A falsification stress test "
        "(scale=0.10, beta_valid=0.005, noise_std=0.01)"
    )
    print_table(stress_results)

    print("\nCandidate A stress aggregate (correlation std uses ddof=0)")
    print_table(aggregate_candidate_a_stress(stress_results))


if __name__ == "__main__":
    main()
