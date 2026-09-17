"""E3.3 diagnostics only. Run: python -m src.lai_transition_calibration.

Fixed candidate order, no ranking or selection. Evaluation time j uses rows
j-50,...,j-1, whose responses have resolved by j. Eligible times: 50..1200,
including terminal resolution of row 1199. Persistence is dated when known.
"""
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
from scipy.stats import t as student_t
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.exceptions import ConvergenceWarning
from src.lai_transition_environment import generate_transition, alpha_schedule

SEEDS = tuple(range(1000, 1200))
TRAIN_SEEDS = tuple(range(1000, 1140))
TEST_SEEDS = tuple(range(1140, 1200))
D_PLUS = (.01, .02, .03, .04)
DELTAS = (.25, .50, .75)
KS = (1, 3, 5)
W = 50
FEATURES = ('fragility', 'crowding', 'liquidity_stress')
assert 42 not in SEEDS
ROOT = Path(__file__).resolve().parents[1]


def rolling_evidence(shock, response):
    """Only resolved pairs enter no-intercept OLS. s²=SSE/(50-1),
    SE=sqrt(s²/sum(E²)); local two-sided 95% Student-t interval, df=49.
    This is not an anytime-valid confidence sequence. Under changing alpha,
    the local interval is a working constant-slope diagnostic only.
    """
    shock, response = np.asarray(shock, float), np.asarray(response, float)
    if shock.ndim != 1 or shock.shape != response.shape or len(shock) < W:
        raise ValueError('Need matching one-dimensional arrays with at least 50 pairs')
    if not np.isfinite(shock).all() or not np.isfinite(response).all():
        raise ValueError('Pairs must be finite')
    rows = []
    critical = student_t.ppf(.975, W - 1)
    for j in range(W, len(shock) + 1):
        e, r = shock[j-W:j], response[j-W:j]
        denominator = e @ e
        if denominator == 0:
            rows.append((j, np.nan, np.nan, np.nan, np.nan, np.nan))
            continue
        slope = (e @ r) / denominator
        residual = r - slope * e
        variance = residual @ residual / (W - 1)
        se = np.sqrt(variance / denominator)
        rows.append((j, slope, variance, se, slope-critical*se, slope+critical*se))
    return pd.DataFrame(rows, columns=['evaluation_t', 'slope', 'residual_variance', 'se', 'lower', 'upper'])


def evidence_time(rolling, delta, k):
    """Return detection time (end of qualifying run), or None; never backdate."""
    run = 0
    previous = None
    for time, lower in zip(rolling.evaluation_t, rolling.lower):
        run = run if previous is not None and time == previous + 1 else 0
        run = run + 1 if np.isfinite(lower) and lower > 1 + delta else 0
        if run >= k:
            return int(time)
        previous = time
    return None


def theoretical_time(delta):
    times = np.flatnonzero(alpha_schedule() >= 1 + delta)
    return int(times[0]) if len(times) else None


def distribution(values):
    values = pd.Series(values, dtype=float)
    values = values[np.isfinite(values)]
    result = dict(count=len(values), mean=values.mean(), sd=values.std(ddof=1), min=values.min())
    for name, q in [('p025', .025), ('p25', .25), ('median', .5), ('p75', .75), ('p975', .975)]:
        result[name] = values.quantile(q)
    result['max'] = values.max()
    return result


def warning_rows(world):
    selected = world.loc[world.t.between(0, 599)]
    return selected.loc[:, list(FEATURES)], (selected.t >= 400).astype(int).to_numpy()


def warning_diagnostic(worlds):
    """One classifier, 140 training worlds, 60 wholly held-out worlds.
    No row shuffling/downsampling. Features exclude seed/time/hidden outcomes.
    """
    if set(worlds) != set(SEEDS):
        raise ValueError('Exactly seeds 1000..1199 required')
    training = [warning_rows(worlds[seed]) for seed in TRAIN_SEEDS]
    x = pd.concat([pair[0] for pair in training], ignore_index=True)
    y = np.concatenate([pair[1] for pair in training])
    if len(np.unique(y)) != 2:
        raise ValueError('Training labels lack both classes')
    model = make_pipeline(StandardScaler(), LogisticRegression(
        penalty='l2', C=1., solver='lbfgs', tol=1e-4, max_iter=1000,
        fit_intercept=True, class_weight=None, random_state=0))
    with warnings.catch_warnings():
        warnings.simplefilter('error', ConvergenceWarning)
        model.fit(x, y)
    rows, labels, predictions = [], [], []
    for seed in TEST_SEEDS:
        x_test, y_test = warning_rows(worlds[seed])
        valid = len(np.unique(y_test)) == 2
        probability = model.predict_proba(x_test)[:, 1] if len(x_test) else np.array([])
        rows.append(dict(seed=seed, valid=valid, auc_warning_seed=
                         roc_auc_score(y_test, probability) if valid else np.nan))
        labels.extend(y_test)
        predictions.extend(probability)
    pooled = roc_auc_score(labels, predictions) if len(np.unique(labels)) == 2 else np.nan
    table = pd.DataFrame(rows)
    summary = dict(auc_warning_pooled=pooled, valid_worlds=int(table.valid.sum()),
                   invalid_worlds=int((~table.valid).sum()),
                   invalid_seeds=','.join(map(str, table.loc[~table.valid, 'seed'])))
    summary.update(distribution(table.loc[table.valid, 'auc_warning_seed']))
    return table, summary


def summarize_evidence(table):
    rows = []
    for (d, delta, k), group in table.groupby(['d_plus', 'delta', 'k'], sort=True):
        row = dict(d_plus=d, delta=delta, k=k, T_delta=theoretical_time(delta))
        for kind in ('control', 'transition'):
            worlds = group[group.world == kind]
            detected = worlds.T_evidence.notna()
            row[f'{kind}_worlds'] = len(worlds)
            row[f'{kind}_detections'] = int(detected.sum())
            row[f'{kind}_no_detection'] = int((~detected).sum())
            row[f'{kind}_rate'] = detected.mean()
            if kind == 'control':
                row.update({f'false_time_{key}': value for key, value in distribution(worlds.loc[detected, 'T_evidence']).items()})
            else:
                row['early_crossing_rate'] = (worlds.loc[detected, 'T_evidence'] < row['T_delta']).sum() / len(worlds)
                latency = worlds.loc[detected, 'T_evidence'] - row['T_delta']
                row.update({f'latency_{key}': value for key, value in distribution(latency).items()})
        rows.append(row)
    return pd.DataFrame(rows)


def run_calibration():
    warning_tables, warning_summaries, evidence = [], [], []
    for d in D_PLUS:
        worlds = {}
        for seed in SEEDS:
            transition = generate_transition(seed, d)
            control = generate_transition(seed, d, control=True)
            worlds[seed] = transition
            for kind, world in [('transition', transition), ('control', control)]:
                rolling = rolling_evidence(world.shock, world.next_response)
                for delta in DELTAS:
                    for k in KS:
                        detection = evidence_time(rolling, delta, k)
                        evidence.append(dict(d_plus=d, delta=delta, k=k, seed=seed,
                                             world=kind, T_delta=theoretical_time(delta),
                                             detected=detection is not None, T_evidence=detection))
        warning, summary = warning_diagnostic(worlds)
        warning.insert(0, 'd_plus', d)
        warning_tables.append(warning)
        warning_summaries.append(dict(d_plus=d, **summary))
        print(f'Completed d_plus={d:.2f}', flush=True)
    evidence = pd.DataFrame(evidence)
    evidence['T_evidence'] = evidence.T_evidence.astype('Int64')
    return pd.concat(warning_tables, ignore_index=True), pd.DataFrame(warning_summaries), evidence, summarize_evidence(evidence)


def markdown(table):
    def fmt(v):
        if pd.isna(v):
            return 'NA'
        return f'{v:.6f}' if isinstance(v, (float, np.floating)) else str(v)
    rows = ['| ' + ' | '.join(table.columns) + ' |', '| ' + ' | '.join(['---'] * len(table.columns)) + ' |']
    rows.extend('| ' + ' | '.join(fmt(v) for v in row) + ' |' for row in table.itertuples(index=False, name=None))
    return '\n'.join(rows)


def write_artifacts(warning, summary, evidence, diagnostics):
    result_dir = ROOT / 'results'
    result_dir.mkdir(exist_ok=True)
    for name, table in [('warning_seeds', warning), ('warning_summary', summary),
                        ('evidence', evidence), ('diagnostics', diagnostics)]:
        table.to_csv(result_dir / f'lai_transition_{name}.csv', index=False)
    report = '''# E3.3 controlled-transition calibration

Starting checkpoint: c71910f. Frozen E1/E1.5/E2/V1 code and reports are unchanged.
Seeds 1000–1199 only; seed 42 is absent from E3 scientific calibration.
No external API or LLM provider was used. No parameters are selected or ranked.

## Environment and matched controls

N=1200. Alpha=1 for t=0..599; alpha=1+2*(t-600)/299 for t=600..899;
alpha=3 for t=900..1199. Hidden benchmark times: warning=400, structural=600.
Control alpha=1 throughout. Z_-1=0; Z_t=.97*Z_(t-1)+d_t+eta_t,
eta~N(0,.15²). d_t=d_plus for 400<=t<750 and zero otherwise.
F/C/L=sigmoid((1,.8,1.1)*Z+independent N(0,.5²) measurement noise).
Nuisance and shocks are independent standard normals. Response=alpha*shock+
N(0,.5²). Five SeedSequence child RNG streams separate latent innovations,
measurement noise, nuisance, shocks, and response noise. Matched transition/control
calls share all random realizations and differ only in alpha. Streams are also
shared across d_plus at each seed; diagnostics across d_plus are not independent.
Hidden stress/alpha columns and warning/structural metadata are research truth,
not an Agent interface. Same-row next_response at row t resolves at time t+1.

## Warning evaluation

One fixed classifier per d_plus pools all 84,000 baseline/warning rows from
training seeds 1000–1139 (140 worlds). Test seeds 1140–1199 (60 worlds) are
entirely held out: 36,000 test rows. Labels: t=0..399 -> 0; t=400..599 -> 1.
No downsampling or random row split. Features exactly fragility, crowding,
liquidity_stress. Seed and time are partition/label metadata only. Training-only
StandardScaler; LogisticRegression L2, C=1, lbfgs, tol=.0001, max_iter=1000,
intercept=True, class_weight=None, random_state=0. No tuning. The same fitted
classifier evaluates all held-out worlds. Primary AUC pools held-out predictions;
robustness AUCs are per held-out world. Missing-class worlds are explicitly marked
invalid; seed AUC is missing. All held-out predictions enter pooled AUC if pooled
labels contain both classes. Convergence warnings stop execution.
Matched controls have identical F/C/L in these periods, so warning fitting is
performed once per d_plus rather than duplicated for the controls.

## Evidence reference

At evaluation time j=50..1200, use only resolved pairs in rows j-50..j-1.
The final evaluation at 1200 resolves the last trajectory row. W=50 exactly.
Slope=sum(E*R)/sum(E²); residual variance=sum((R-slope*E)²)/49;
SE=sqrt(residual_variance/sum(E²)). Interval=slope +/- t_(.975,49)*SE.
Zero shock energy gives an undefined interval, which cannot satisfy evidence.
No hidden noise sigma, alpha, stress, F/C/L, nuisance, or benchmark times enter
this estimator. This is a local working constant-slope 95% diagnostic interval,
not an anytime-valid confidence sequence; repeated/overlapping windows have no
claimed simultaneous coverage. Changing alpha also limits a constant-slope
interval's interpretation within transition windows.
Evidence requires lower bound > 1+delta for k consecutive eligible times.
T_evidence is the last time in that run, when persistence becomes known; it is
never backdated. T_delta is calculated from the hidden alpha schedule (shock-row
time), so latency includes observation resolution and persistence delay.
No-detection is explicit: detected=False and missing T_evidence, not an imputed time.
Early crossing uses all 200 transition worlds as denominator; no-detection worlds
contribute no early crossing. Latency and false-time summaries condition on detection,
with contributing counts. SD uses ddof=1; percentiles use linear interpolation.

## Calibration size

Four d_plus values (.01,.02,.03,.04), three deltas (.25,.50,.75), three k values
(1,3,5): 36 combinations, each evaluated on 200 transition/control pairs.
800 matched pairs = 1,600 generated worlds; 14,400 world/parameter detection
records. Four warning classifiers and 240 held-out-world AUCs. No optimization.
Machine-readable files are results/lai_transition_{warning_seeds,warning_summary,
evidence,diagnostics}.csv (results/ is intentionally gitignored).

## Warning distributions

'''
    report += markdown(summary) + '\n\n## Detection diagnostics\n\n'
    columns = ['d_plus', 'delta', 'k', 'T_delta', 'control_detections', 'control_no_detection', 'control_rate',
               'transition_detections', 'transition_no_detection', 'transition_rate', 'early_crossing_rate']
    report += 'control_rate is the false-evidence rate. All rates use 200 worlds per cell.\n\n' + markdown(diagnostics[columns])
    for prefix, title in [('false_time_', 'False-evidence times, conditional on detection'), ('latency_', 'Transition evidence latency, conditional on detection')]:
        report += '\n\n## ' + title + '\n\n' + markdown(diagnostics[['d_plus', 'delta', 'k'] + [c for c in diagnostics if c.startswith(prefix)]])
    report += '\n\n## Observed calibration diagnostics\n\n'
    report += (f'Pooled warning AUC spans {summary.auc_warning_pooled.min():.6f} to '
               f'{summary.auc_warning_pooled.max():.6f}; all {int(summary.valid_worlds.sum())} '
               'held-out-world evaluations have both classes. The tables show substantial '
               'between-world variability.\n\n')
    report += (f'Across the {len(diagnostics)} cells, control false-evidence counts range from '
               f'{diagnostics.control_detections.min()} to {diagnostics.control_detections.max()} '
               'per 200 worlds; transition detections range from '
               f'{diagnostics.transition_detections.min()} to {diagnostics.transition_detections.max()} '
               'per 200 worlds. Early-crossing rates range from '
               f'{diagnostics.early_crossing_rate.min():.6f} to '
               f'{diagnostics.early_crossing_rate.max():.6f}. '
               'Observed zero event counts do not establish zero population event probabilities.\n')
    report += '''

## Interpretation boundary

d_plus controls warning observability; delta defines practical deviation; k
requires persistence. Their scientific roles are distinct. Identical evidence
diagnostics across d_plus follow from the design: d_plus changes only stress and
footprints, whereas this detector uses only shock/response pairs. Warning AUC
measures cross-world stress-footprint discrimination, not prediction of future
structural change. Alpha is exactly 1 throughout baseline and warning in both
world types: warning != contradiction. These diagnostics neither establish
real-world LAI nor justify an Agent invalidating its belief. No final d_plus,
delta, or k is selected. The benchmark is not declared ready for Agent evaluation.
'''
    (ROOT / 'reports' / 'lai_transition_calibration_analysis.md').write_text(report)


if __name__ == '__main__':
    write_artifacts(*run_calibration())
