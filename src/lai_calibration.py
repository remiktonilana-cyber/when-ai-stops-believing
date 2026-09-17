"""Non-canonical sampling calibration of the frozen LAI E1 generator.

Run from the repository root with: python -m src.lai_calibration
No acceptance gates, parameter tuning, or canonical Experiment A evaluation.
"""

from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import scipy
import sklearn
import statsmodels
import statsmodels.api as sm
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.lai_environment import generate_environment


CALIBRATION_SEEDS = tuple(range(1000, 1200))
assert 42 not in CALIBRATION_SEEDS
N_TIMESTEPS = 2000
TRAIN_END = 1400
FCL_FEATURES = ("fragility", "crowding", "liquidity_stress")
NUISANCE_FEATURES = ("nuisance",)
STATE_ENCODING = {"RESILIENT": 0, "AMPLIFYING": 1}
CORE_STATISTICS = (
    "smd_abs_shock", "beta_3", "beta_3_ci_lower", "beta_3_ci_upper",
    "alpha_hat_resilient", "alpha_hat_amplifying", "auc_fcl", "auc_n", "auc_gap",
)
ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "results" / "lai_calibration_seed_1000_1199.csv"
REPORT_PATH = ROOT / "reports" / "lai_calibration_analysis.md"


def _check_seed(seed):
    if isinstance(seed, (bool, np.bool_)) or not isinstance(seed, (int, np.integer)) or seed not in CALIBRATION_SEEDS:
        raise ValueError("Calibration seeds must be integers in 1000–1199")


def shock_balance(shock, state):
    """Sample SDs use ddof=1; SMD uses the conventional pooled sample SD.

    pooled_sd = sqrt(((n_A-1)*s_A^2 + (n_R-1)*s_R^2)/(n_A+n_R-2)),
    where s_A and s_R are sample SDs of absolute shock magnitudes.
    SMD sign and raw difference are AMPLIFYING minus RESILIENT.
    Finite-sample balance is not proof of mathematical independence.
    """
    groups = [np.asarray(shock)[state == value] for value in (0, 1)]
    result = {}
    for name, values in zip(("resilient", "amplifying"), groups):
        result.update({
            f"mean_shock_{name}": values.mean(),
            f"mean_abs_shock_{name}": np.abs(values).mean(),
            f"sd_shock_{name}": values.std(ddof=1),
            f"sd_abs_shock_{name}": np.abs(values).std(ddof=1),
        })
    pooled = np.sqrt(sum((len(g) - 1) * np.abs(g).var(ddof=1) for g in groups)
                     / (sum(map(len, groups)) - 2))
    difference = result["mean_abs_shock_amplifying"] - result["mean_abs_shock_resilient"]
    result["raw_abs_shock_difference"] = difference
    result["smd_abs_shock"] = difference / pooled if pooled > 0 else np.nan
    return result


def amplification(shock, state, response):
    """OLS with intercept, nonrobust homoskedastic SE and two-sided 95% t CI.

    Design columns: 1, E, S, E*S. Residual degrees of freedom: n-4.
    Separate empirical slopes also use OLS with an intercept in each state.
    """
    design = np.column_stack((np.ones(len(shock)), shock, state, shock * state))
    fitted = sm.OLS(response, design).fit(cov_type="nonrobust", use_t=True)
    result = {f"beta_{i}": value for i, value in enumerate(fitted.params)}
    result.update(beta_3_se=fitted.bse[3],
                  beta_3_ci_lower=fitted.conf_int(alpha=0.05)[3, 0],
                  beta_3_ci_upper=fitted.conf_int(alpha=0.05)[3, 1])
    for value, name in ((0, "resilient"), (1, "amplifying")):
        mask = state == value
        group_design = np.column_stack((np.ones(mask.sum()), shock[mask]))
        result[f"alpha_hat_{name}"] = sm.OLS(response[mask], group_design).fit().params[1]
    return result


def _classifier_auc(data, state, train, test, features):
    """Training-only scaling, fixed L2 logistic regression, held-out ROC-AUC."""
    model = make_pipeline(
        StandardScaler(with_mean=True, with_std=True),
        LogisticRegression(penalty="l2", C=1.0, solver="lbfgs", tol=1e-4,
                           max_iter=1000, fit_intercept=True, class_weight=None,
                           random_state=0),
    )
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        model.fit(data.loc[train, list(features)], state[train])
    probability = model.predict_proba(data.loc[test, list(features)])[:, 1]
    return float(roc_auc_score(state[test], probability))


def analyze_world(data, seed):
    """Calculate one allowed world's statistics; preserve invalid splits as NaN.

    The caller supplies the world generated with the stated seed. Public entry
    run_calibration enforces this provenance by generating each world itself.
    """
    _check_seed(seed)
    if len(data) != N_TIMESTEPS or not np.array_equal(data.t, np.arange(N_TIMESTEPS)):
        raise ValueError("Expected ordered t=0 through 1999")
    if not data.latent_state.isin(STATE_ENCODING).all():
        raise ValueError("Unknown latent state")
    state = data.latent_state.map(STATE_ENCODING).to_numpy()
    if any((state == value).sum() < 2 for value in (0, 1)):
        raise ValueError("Both states need at least two observations for regressions")
    shock = data.shock.to_numpy()
    result = {"seed": int(seed)}
    result.update(shock_balance(shock, state))
    result.update(amplification(shock, state, data.next_response.to_numpy()))
    train = (data.t < TRAIN_END).to_numpy()
    test = ~train
    valid_train = len(np.unique(state[train])) == 2
    valid_test = len(np.unique(state[test])) == 2
    result.update(split_valid=valid_train and valid_test,
                  split_failure=";".join(name for name, valid in
                                         (("train_single_class", valid_train),
                                          ("test_single_class", valid_test)) if not valid),
                  auc_fcl=np.nan, auc_n=np.nan, auc_gap=np.nan)
    if result["split_valid"]:
        result["auc_fcl"] = _classifier_auc(data, state, train, test, FCL_FEATURES)
        result["auc_n"] = _classifier_auc(data, state, train, test, NUISANCE_FEATURES)
        result["auc_gap"] = result["auc_fcl"] - result["auc_n"]
    return result


def run_calibration(seeds=CALIBRATION_SEEDS):
    """Default: exactly 200 frozen, zero-drift worlds; subsets support tests."""
    seeds = tuple(seeds)
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("Seeds must be nonempty and unique")
    for seed in seeds:
        _check_seed(seed)
    assert 42 not in seeds
    return pd.DataFrame([
        analyze_world(generate_environment(n_timesteps=N_TIMESTEPS, seed=int(seed)), seed)
        for seed in seeds
    ])


def summarize(table):
    """Finite numeric values only; AUC summaries additionally require valid splits.

    Across-world SD uses ddof=1; percentiles use linear interpolation. Count is
    included so missing values cannot silently change the summary denominator.
    """
    rows = []
    for statistic in CORE_STATISTICS:
        values = table.loc[table.split_valid, statistic] if statistic.startswith("auc_") else table[statistic]
        values = pd.to_numeric(values, errors="coerce")
        values = values[np.isfinite(values)]
        row = {"statistic": statistic, "count": len(values), "mean": values.mean(),
               "std": values.std(ddof=1), "min": values.min()}
        for label, q in (("2.5%", .025), ("25%", .25), ("median", .5), ("75%", .75), ("97.5%", .975)):
            row[label] = values.quantile(q, interpolation="linear")
        row["max"] = values.max()
        rows.append(row)
    return pd.DataFrame(rows).set_index("statistic")


def write_artifacts(table, csv_path=CSV_PATH, report_path=REPORT_PATH):
    """Write the complete prescribed calibration and its descriptive report."""
    if tuple(table.seed) != CALIBRATION_SEEDS:
        raise ValueError("Artifacts require exactly the ordered 200 calibration seeds")
    summary = summarize(table)
    invalid = table.loc[~table.split_valid, "seed"].tolist()
    header = ["statistic"] + list(summary.columns)
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * len(header)) + " |"]
    for name, row in summary.iterrows():
        cells = [name, str(int(row["count"]))] + [f"{row[column]:.6f}" for column in summary.columns[1:]]
        lines.append("| " + " | ".join(cells) + " |")
    report = f"""# LAI E1.5 sampling calibration

These are non-canonical calibration results from seeds 1000–1199. Seed 42 was not evaluated. These results do not constitute the canonical Experiment A and do not validate LAI.

Frozen generator: `d347531`, `src/lai_environment.py`, unchanged. Exactly 200 worlds,
2,000 timesteps each, default zero drift; no DGP parameters changed.
Reproduce with `python -m src.lai_calibration`. Per-world data: `{Path(csv_path).name}`
(default location `results/`, intentionally gitignored).

## Methods

- Shock group means and sample SDs (ddof=1) are recorded for signed and absolute shocks.
  Raw difference is mean absolute shock in AMPLIFYING minus RESILIENT.
  SMD divides this by sqrt(((n_A-1)*s_A²+(n_R-1)*s_R²)/(n_A+n_R-2)),
  where s_A and s_R are sample SDs of absolute shocks.
- OLS: response = beta_0 + beta_1*shock + beta_2*state + beta_3*shock*state + error;
  RESILIENT=0, AMPLIFYING=1. Conventional homoskedastic residual-variance SEs,
  residual df=1996, two-sided Student-t 95% intervals. Separate state slopes use
  OLS with an intercept; they are fitted, not assigned theoretical values.
- Temporal training t=0–1399; testing t=1400–1999; no shuffling.
  FCL uses only fragility, crowding, liquidity_stress. The separate nuisance model
  uses only nuisance. Neither uses latent_stress, shock, or next_response.
- Both classifiers: StandardScaler (mean centering and unit variance, training fit only),
  LogisticRegression(penalty='l2', C=1.0, solver='lbfgs', tol=0.0001,
  max_iter=1000, fit_intercept=True, class_weight=None, random_state=0).
  No hyperparameter tuning. AUC uses held-out class-1 probabilities.
  Convergence warnings halt execution rather than silently accepting a fit.
- Both classes must occur in both splits. Invalid worlds retain shock/regression
  statistics, a failure reason, and missing AUCs. AUC summaries use only split-valid,
  finite values; other summaries use finite values. Across-world SD uses ddof=1;
  percentiles use linear interpolation. Counts disclose summary denominators.
- Versions: NumPy {np.__version__}, pandas {pd.__version__}, scikit-learn {sklearn.__version__},
  SciPy {scipy.__version__}, statsmodels {statsmodels.__version__}.

## Split validity

Worlds: {len(table)}; valid: {int(table.split_valid.sum())}; invalid: {len(invalid)}.
Affected seeds: {invalid if invalid else 'none'}.

## Calibration distributions

{chr(10).join(lines)}

## Interpretation boundary

These distributions describe finite-sample variation under the frozen synthetic DGP.
Shock-balance diagnostics do not prove mathematical independence. Held-out AUCs
describe these temporal splits, not a production estimator. No final acceptance
thresholds are selected and no canonical Experiment A conclusion is drawn.
"""
    csv_path, report_path = Path(csv_path), Path(report_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(csv_path, index=False)
    report_path.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    calibration = run_calibration()
    write_artifacts(calibration)
    print(f"Wrote {len(calibration)} non-canonical worlds to {CSV_PATH}")
    print(f"Report: {REPORT_PATH}")
