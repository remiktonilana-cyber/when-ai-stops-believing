# E3.3 controlled-transition calibration

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

| d_plus | auc_warning_pooled | valid_worlds | invalid_worlds | invalid_seeds | count | mean | sd | min | p025 | p25 | median | p75 | p975 | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.010000 | 0.601722 | 60 | 0 | NA | 60 | 0.596637 | 0.171992 | 0.227625 | 0.294108 | 0.462134 | 0.627656 | 0.726072 | 0.885965 | 0.908713 |
| 0.020000 | 0.705994 | 60 | 0 | NA | 60 | 0.701966 | 0.148602 | 0.356438 | 0.426228 | 0.606528 | 0.725156 | 0.825188 | 0.932778 | 0.954800 |
| 0.030000 | 0.793212 | 60 | 0 | NA | 60 | 0.791011 | 0.119489 | 0.495300 | 0.541019 | 0.730841 | 0.810437 | 0.883975 | 0.966427 | 0.979163 |
| 0.040000 | 0.859780 | 60 | 0 | NA | 60 | 0.859063 | 0.091164 | 0.624200 | 0.637045 | 0.818844 | 0.881144 | 0.923906 | 0.982958 | 0.991112 |

## Detection diagnostics

control_rate is the false-evidence rate. All rates use 200 worlds per cell.

| d_plus | delta | k | T_delta | control_detections | control_no_detection | control_rate | transition_detections | transition_no_detection | transition_rate | early_crossing_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.010000 | 0.250000 | 1 | 638 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.010000 | 0.250000 | 3 | 638 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.010000 | 0.250000 | 5 | 638 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.010000 | 0.500000 | 1 | 675 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.010000 | 0.500000 | 3 | 675 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.010000 | 0.500000 | 5 | 675 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.010000 | 0.750000 | 1 | 713 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.010000 | 0.750000 | 3 | 713 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.010000 | 0.750000 | 5 | 713 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.020000 | 0.250000 | 1 | 638 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.020000 | 0.250000 | 3 | 638 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.020000 | 0.250000 | 5 | 638 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.020000 | 0.500000 | 1 | 675 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.020000 | 0.500000 | 3 | 675 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.020000 | 0.500000 | 5 | 675 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.020000 | 0.750000 | 1 | 713 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.020000 | 0.750000 | 3 | 713 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.020000 | 0.750000 | 5 | 713 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.030000 | 0.250000 | 1 | 638 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.030000 | 0.250000 | 3 | 638 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.030000 | 0.250000 | 5 | 638 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.030000 | 0.500000 | 1 | 675 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.030000 | 0.500000 | 3 | 675 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.030000 | 0.500000 | 5 | 675 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.030000 | 0.750000 | 1 | 713 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.030000 | 0.750000 | 3 | 713 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.030000 | 0.750000 | 5 | 713 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.040000 | 0.250000 | 1 | 638 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.040000 | 0.250000 | 3 | 638 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.040000 | 0.250000 | 5 | 638 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.040000 | 0.500000 | 1 | 675 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.040000 | 0.500000 | 3 | 675 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.040000 | 0.500000 | 5 | 675 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.040000 | 0.750000 | 1 | 713 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.040000 | 0.750000 | 3 | 713 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |
| 0.040000 | 0.750000 | 5 | 713 | 0 | 200 | 0.000000 | 200 | 0 | 1.000000 | 0.000000 |

## False-evidence times, conditional on detection

| d_plus | delta | k | false_time_count | false_time_mean | false_time_sd | false_time_min | false_time_p025 | false_time_p25 | false_time_median | false_time_p75 | false_time_p975 | false_time_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.010000 | 0.250000 | 1 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.010000 | 0.250000 | 3 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.010000 | 0.250000 | 5 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.010000 | 0.500000 | 1 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.010000 | 0.500000 | 3 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.010000 | 0.500000 | 5 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.010000 | 0.750000 | 1 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.010000 | 0.750000 | 3 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.010000 | 0.750000 | 5 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.020000 | 0.250000 | 1 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.020000 | 0.250000 | 3 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.020000 | 0.250000 | 5 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.020000 | 0.500000 | 1 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.020000 | 0.500000 | 3 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.020000 | 0.500000 | 5 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.020000 | 0.750000 | 1 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.020000 | 0.750000 | 3 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.020000 | 0.750000 | 5 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.030000 | 0.250000 | 1 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.030000 | 0.250000 | 3 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.030000 | 0.250000 | 5 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.030000 | 0.500000 | 1 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.030000 | 0.500000 | 3 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.030000 | 0.500000 | 5 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.030000 | 0.750000 | 1 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.030000 | 0.750000 | 3 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.030000 | 0.750000 | 5 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.040000 | 0.250000 | 1 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.040000 | 0.250000 | 3 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.040000 | 0.250000 | 5 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.040000 | 0.500000 | 1 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.040000 | 0.500000 | 3 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.040000 | 0.500000 | 5 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.040000 | 0.750000 | 1 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.040000 | 0.750000 | 3 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 0.040000 | 0.750000 | 5 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA |

## Transition evidence latency, conditional on detection

| d_plus | delta | k | latency_count | latency_mean | latency_sd | latency_min | latency_p025 | latency_p25 | latency_median | latency_p75 | latency_p975 | latency_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.010000 | 0.250000 | 1 | 200 | 44.880000 | 11.020110 | 13.000000 | 23.950000 | 37.750000 | 45.000000 | 51.000000 | 66.025000 | 80.000000 |
| 0.010000 | 0.250000 | 3 | 200 | 47.810000 | 11.040533 | 15.000000 | 26.000000 | 41.000000 | 48.000000 | 54.000000 | 69.025000 | 82.000000 |
| 0.010000 | 0.250000 | 5 | 200 | 50.255000 | 10.991087 | 17.000000 | 28.000000 | 44.000000 | 50.500000 | 56.000000 | 71.025000 | 84.000000 |
| 0.010000 | 0.500000 | 1 | 200 | 45.920000 | 11.208109 | 14.000000 | 25.000000 | 38.750000 | 46.000000 | 54.000000 | 65.025000 | 79.000000 |
| 0.010000 | 0.500000 | 3 | 200 | 49.085000 | 11.316274 | 16.000000 | 27.000000 | 42.000000 | 49.000000 | 57.000000 | 70.000000 | 81.000000 |
| 0.010000 | 0.500000 | 5 | 200 | 51.540000 | 11.390219 | 18.000000 | 29.000000 | 44.000000 | 51.000000 | 60.000000 | 72.000000 | 83.000000 |
| 0.010000 | 0.750000 | 1 | 200 | 45.545000 | 10.779096 | 20.000000 | 23.000000 | 39.000000 | 45.500000 | 53.000000 | 68.000000 | 74.000000 |
| 0.010000 | 0.750000 | 3 | 200 | 48.510000 | 10.548281 | 22.000000 | 27.000000 | 41.000000 | 49.000000 | 55.250000 | 70.000000 | 76.000000 |
| 0.010000 | 0.750000 | 5 | 200 | 50.980000 | 10.546361 | 24.000000 | 29.975000 | 43.750000 | 51.500000 | 58.000000 | 72.000000 | 78.000000 |
| 0.020000 | 0.250000 | 1 | 200 | 44.880000 | 11.020110 | 13.000000 | 23.950000 | 37.750000 | 45.000000 | 51.000000 | 66.025000 | 80.000000 |
| 0.020000 | 0.250000 | 3 | 200 | 47.810000 | 11.040533 | 15.000000 | 26.000000 | 41.000000 | 48.000000 | 54.000000 | 69.025000 | 82.000000 |
| 0.020000 | 0.250000 | 5 | 200 | 50.255000 | 10.991087 | 17.000000 | 28.000000 | 44.000000 | 50.500000 | 56.000000 | 71.025000 | 84.000000 |
| 0.020000 | 0.500000 | 1 | 200 | 45.920000 | 11.208109 | 14.000000 | 25.000000 | 38.750000 | 46.000000 | 54.000000 | 65.025000 | 79.000000 |
| 0.020000 | 0.500000 | 3 | 200 | 49.085000 | 11.316274 | 16.000000 | 27.000000 | 42.000000 | 49.000000 | 57.000000 | 70.000000 | 81.000000 |
| 0.020000 | 0.500000 | 5 | 200 | 51.540000 | 11.390219 | 18.000000 | 29.000000 | 44.000000 | 51.000000 | 60.000000 | 72.000000 | 83.000000 |
| 0.020000 | 0.750000 | 1 | 200 | 45.545000 | 10.779096 | 20.000000 | 23.000000 | 39.000000 | 45.500000 | 53.000000 | 68.000000 | 74.000000 |
| 0.020000 | 0.750000 | 3 | 200 | 48.510000 | 10.548281 | 22.000000 | 27.000000 | 41.000000 | 49.000000 | 55.250000 | 70.000000 | 76.000000 |
| 0.020000 | 0.750000 | 5 | 200 | 50.980000 | 10.546361 | 24.000000 | 29.975000 | 43.750000 | 51.500000 | 58.000000 | 72.000000 | 78.000000 |
| 0.030000 | 0.250000 | 1 | 200 | 44.880000 | 11.020110 | 13.000000 | 23.950000 | 37.750000 | 45.000000 | 51.000000 | 66.025000 | 80.000000 |
| 0.030000 | 0.250000 | 3 | 200 | 47.810000 | 11.040533 | 15.000000 | 26.000000 | 41.000000 | 48.000000 | 54.000000 | 69.025000 | 82.000000 |
| 0.030000 | 0.250000 | 5 | 200 | 50.255000 | 10.991087 | 17.000000 | 28.000000 | 44.000000 | 50.500000 | 56.000000 | 71.025000 | 84.000000 |
| 0.030000 | 0.500000 | 1 | 200 | 45.920000 | 11.208109 | 14.000000 | 25.000000 | 38.750000 | 46.000000 | 54.000000 | 65.025000 | 79.000000 |
| 0.030000 | 0.500000 | 3 | 200 | 49.085000 | 11.316274 | 16.000000 | 27.000000 | 42.000000 | 49.000000 | 57.000000 | 70.000000 | 81.000000 |
| 0.030000 | 0.500000 | 5 | 200 | 51.540000 | 11.390219 | 18.000000 | 29.000000 | 44.000000 | 51.000000 | 60.000000 | 72.000000 | 83.000000 |
| 0.030000 | 0.750000 | 1 | 200 | 45.545000 | 10.779096 | 20.000000 | 23.000000 | 39.000000 | 45.500000 | 53.000000 | 68.000000 | 74.000000 |
| 0.030000 | 0.750000 | 3 | 200 | 48.510000 | 10.548281 | 22.000000 | 27.000000 | 41.000000 | 49.000000 | 55.250000 | 70.000000 | 76.000000 |
| 0.030000 | 0.750000 | 5 | 200 | 50.980000 | 10.546361 | 24.000000 | 29.975000 | 43.750000 | 51.500000 | 58.000000 | 72.000000 | 78.000000 |
| 0.040000 | 0.250000 | 1 | 200 | 44.880000 | 11.020110 | 13.000000 | 23.950000 | 37.750000 | 45.000000 | 51.000000 | 66.025000 | 80.000000 |
| 0.040000 | 0.250000 | 3 | 200 | 47.810000 | 11.040533 | 15.000000 | 26.000000 | 41.000000 | 48.000000 | 54.000000 | 69.025000 | 82.000000 |
| 0.040000 | 0.250000 | 5 | 200 | 50.255000 | 10.991087 | 17.000000 | 28.000000 | 44.000000 | 50.500000 | 56.000000 | 71.025000 | 84.000000 |
| 0.040000 | 0.500000 | 1 | 200 | 45.920000 | 11.208109 | 14.000000 | 25.000000 | 38.750000 | 46.000000 | 54.000000 | 65.025000 | 79.000000 |
| 0.040000 | 0.500000 | 3 | 200 | 49.085000 | 11.316274 | 16.000000 | 27.000000 | 42.000000 | 49.000000 | 57.000000 | 70.000000 | 81.000000 |
| 0.040000 | 0.500000 | 5 | 200 | 51.540000 | 11.390219 | 18.000000 | 29.000000 | 44.000000 | 51.000000 | 60.000000 | 72.000000 | 83.000000 |
| 0.040000 | 0.750000 | 1 | 200 | 45.545000 | 10.779096 | 20.000000 | 23.000000 | 39.000000 | 45.500000 | 53.000000 | 68.000000 | 74.000000 |
| 0.040000 | 0.750000 | 3 | 200 | 48.510000 | 10.548281 | 22.000000 | 27.000000 | 41.000000 | 49.000000 | 55.250000 | 70.000000 | 76.000000 |
| 0.040000 | 0.750000 | 5 | 200 | 50.980000 | 10.546361 | 24.000000 | 29.975000 | 43.750000 | 51.500000 | 58.000000 | 72.000000 | 78.000000 |

## Observed calibration diagnostics

Pooled warning AUC spans 0.601722 to 0.859780; all 240 held-out-world evaluations have both classes. The tables show substantial between-world variability.

Across the 36 cells, control false-evidence counts range from 0 to 0 per 200 worlds; transition detections range from 200 to 200 per 200 worlds. Early-crossing rates range from 0.000000 to 0.000000. Observed zero event counts do not establish zero population event probabilities.


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
