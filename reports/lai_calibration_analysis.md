# LAI E1.5 sampling calibration

These are non-canonical calibration results from seeds 1000–1199. Seed 42 was not evaluated. These results do not constitute the canonical Experiment A and do not validate LAI.

Frozen generator: `d347531`, `src/lai_environment.py`, unchanged. Exactly 200 worlds,
2,000 timesteps each, default zero drift; no DGP parameters changed.
Reproduce with `python -m src.lai_calibration`. Per-world data: `lai_calibration_seed_1000_1199.csv`
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
- Versions: NumPy 1.21.5, pandas 1.4.4, scikit-learn 1.0.2,
  SciPy 1.9.1, statsmodels 0.13.2.

## Split validity

Worlds: 200; valid: 200; invalid: 0.
Affected seeds: none.

## Calibration distributions

| statistic | count | mean | std | min | 2.5% | 25% | median | 75% | 97.5% | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| smd_abs_shock | 200 | 0.007110 | 0.047099 | -0.090714 | -0.084464 | -0.025688 | 0.004833 | 0.039300 | 0.098316 | 0.112140 |
| beta_3 | 200 | 1.998426 | 0.024534 | 1.921571 | 1.953740 | 1.981818 | 1.998655 | 2.013576 | 2.052302 | 2.063002 |
| beta_3_ci_lower | 200 | 1.950538 | 0.024491 | 1.875428 | 1.906144 | 1.933797 | 1.950412 | 1.966309 | 2.002405 | 2.016557 |
| beta_3_ci_upper | 200 | 2.046315 | 0.024634 | 1.967713 | 2.002175 | 2.029863 | 2.046499 | 2.062148 | 2.102199 | 2.109447 |
| alpha_hat_resilient | 200 | 1.000112 | 0.012972 | 0.966858 | 0.975770 | 0.991471 | 1.000644 | 1.009033 | 1.024600 | 1.032370 |
| alpha_hat_amplifying | 200 | 2.998539 | 0.019431 | 2.946159 | 2.963629 | 2.984097 | 2.997845 | 3.010629 | 3.037720 | 3.047872 |
| auc_fcl | 200 | 0.937912 | 0.022903 | 0.860463 | 0.894618 | 0.922889 | 0.942054 | 0.955274 | 0.974550 | 0.981507 |
| auc_n | 200 | 0.497171 | 0.025405 | 0.443529 | 0.453831 | 0.477658 | 0.497702 | 0.515759 | 0.543009 | 0.602566 |
| auc_gap | 200 | 0.440740 | 0.032709 | 0.319401 | 0.368416 | 0.421132 | 0.444609 | 0.463225 | 0.494589 | 0.522613 |

## Interpretation boundary

These distributions describe finite-sample variation under the frozen synthetic DGP.
Shock-balance diagnostics do not prove mathematical independence. Held-out AUCs
describe these temporal splits, not a production estimator. No final acceptance
thresholds are selected and no canonical Experiment A conclusion is drawn.
