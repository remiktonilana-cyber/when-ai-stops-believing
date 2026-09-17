"""E3 diagnostic logic tests without selecting research parameters."""
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from scipy.stats import t
from src import lai_transition_calibration as cal
from src.lai_transition_environment import generate_transition, alpha_schedule


class TransitionCalibrationTests(unittest.TestCase):
    def test_fixed_grid_and_seed_partition(self):
        self.assertEqual(cal.SEEDS, tuple(range(1000,1200)))
        self.assertNotIn(42, cal.SEEDS)
        self.assertEqual(cal.TRAIN_SEEDS, tuple(range(1000,1140)))
        self.assertEqual(cal.TEST_SEEDS, tuple(range(1140,1200)))
        self.assertEqual(cal.D_PLUS, (.01,.02,.03,.04))
        self.assertEqual(cal.DELTAS, (.25,.50,.75))
        self.assertEqual(cal.KS, (1,3,5))
        self.assertEqual(cal.W, 50)

    def test_hand_checked_slope_uncertainty(self):
        e = np.ones(50)
        r = 2 + np.tile([-1.,1.],25)
        row = cal.rolling_evidence(e,r).iloc[0]
        self.assertEqual(row.evaluation_t,50)
        self.assertEqual(row.slope,2)
        self.assertAlmostEqual(row.residual_variance,50/49)
        self.assertAlmostEqual(row.se,1/7)
        self.assertAlmostEqual(row.lower,2-t.ppf(.975,49)/7)
        self.assertAlmostEqual(row.upper,2+t.ppf(.975,49)/7)

    def test_resolved_pairs_only_and_future_invariance(self):
        e = np.ones(60)
        r = np.ones(60)
        before = cal.rolling_evidence(e,r)
        r[50:] = 100
        after = cal.rolling_evidence(e,r)
        pd.testing.assert_series_equal(before.iloc[0],after.iloc[0])
        self.assertEqual(after.iloc[1].evaluation_t,51)
        self.assertNotEqual(before.iloc[1].slope,after.iloc[1].slope)
        self.assertEqual(before.evaluation_t.tolist(), list(range(50,61)))
        import inspect
        self.assertEqual(tuple(inspect.signature(cal.rolling_evidence).parameters), ('shock','response'))

    def test_persistence_not_backdated(self):
        table = pd.DataFrame({'evaluation_t':range(50,60),'lower':[1.25,1.3,1.3,1.3,1.3,1.3,0,0,0,0]})
        for k, expected in [(1,51),(3,53),(5,55)]:
            self.assertEqual(cal.evidence_time(table,.25,k),expected)
        self.assertIsNone(cal.evidence_time(table,.5,1))
        table.loc[3,'lower'] = np.nan
        self.assertIsNone(cal.evidence_time(table,.25,3))

    def test_gap_breaks_persistence(self):
        table = pd.DataFrame(dict(evaluation_t=[50,51,53],lower=[2,2,2]))
        self.assertIsNone(cal.evidence_time(table,.25,3))

    def test_theoretical_times(self):
        for delta, expected in [(.25,638),(.5,675),(.75,713)]:
            time = cal.theoretical_time(delta)
            self.assertEqual(time,expected)
            self.assertGreaterEqual(alpha_schedule()[time],1+delta)
            self.assertLess(alpha_schedule()[time-1],1+delta)

    def test_zero_energy_no_detection(self):
        rolling = cal.rolling_evidence(np.zeros(50),np.ones(50))
        self.assertTrue(rolling.lower.isna().all())
        self.assertIsNone(cal.evidence_time(rolling,.25,1))

    def test_diagnostics_keep_no_detection_and_world_types(self):
        table = pd.DataFrame([dict(d_plus=.01,delta=.25,k=1,world=kind,T_evidence=value)
                              for kind,values in [('control',[None,100]),('transition',[None,637])]
                              for value in values])
        row = cal.summarize_evidence(table).iloc[0]
        self.assertEqual(row.control_detections,1)
        self.assertEqual(row.control_no_detection,1)
        self.assertEqual(row.control_rate,.5)
        self.assertEqual(row.false_time_mean,100)
        self.assertEqual(row.transition_rate,.5)
        self.assertEqual(row.early_crossing_rate,.5)
        self.assertEqual(row.latency_count,1)
        self.assertEqual(row.latency_mean,-1)

    def test_distribution_filters_missing(self):
        summary = cal.distribution([1,2,3,np.nan])
        self.assertEqual(summary['count'],3)
        self.assertEqual(summary['sd'],1)
        self.assertEqual(summary['median'],2)
        self.assertEqual(cal.distribution([])['count'],0)

    def test_warning_rows_features_and_labels(self):
        world = generate_transition(1000,.01)
        x,y = cal.warning_rows(world)
        self.assertEqual(tuple(x.columns),('fragility','crowding','liquidity_stress'))
        self.assertEqual(len(x),600)
        np.testing.assert_array_equal(y,np.r_[np.zeros(400),np.ones(200)])
        self.assertTrue((world.alpha.iloc[:600]==1).all())

    def test_warning_partition_fixed_model_and_pooled_auc(self):
        # Distinct feature marker per seed proves no held-out row enters fit.
        worlds = {seed:pd.DataFrame(dict(t=np.arange(600),fragility=np.full(600,seed),
                   crowding=np.arange(600),liquidity_stress=np.zeros(600))) for seed in cal.SEEDS}
        class RecordingModel:
            def fit(self,x,y):
                self.x,self.y=x.copy(),y.copy()
            def predict_proba(self,x):
                self.test_seeds.append(int(x.fragility.iloc[0]))
                probability = np.where(x.crowding>=400,.8,.2)
                return np.column_stack((1-probability,probability))
        model = RecordingModel()
        model.test_seeds=[]
        with patch.object(cal,'make_pipeline',return_value=model) as pipeline:
            rows,summary=cal.warning_diagnostic(worlds)
        pipeline.assert_called_once()
        self.assertEqual(len(model.x),84000)
        self.assertEqual(set(model.x.fragility),set(cal.TRAIN_SEEDS))
        self.assertEqual(model.test_seeds,list(cal.TEST_SEEDS))
        self.assertEqual(tuple(model.x.columns),cal.FEATURES)
        self.assertEqual(int(model.y.sum()),28000)
        self.assertEqual(summary['auc_warning_pooled'],1)
        self.assertEqual(summary['valid_worlds'],60)
        self.assertEqual(len(rows),60)
        self.assertTrue((rows.auc_warning_seed==1).all())
        scaler,classifier=pipeline.call_args.args
        self.assertTrue(scaler.with_mean and scaler.with_std)
        for name,value in dict(C=1.,solver='lbfgs',penalty='l2',max_iter=1000,tol=1e-4,
                               fit_intercept=True,class_weight=None,random_state=0).items():
            self.assertEqual(classifier.get_params()[name],value)

    def test_warning_invalid_world_explicit(self):
        world=generate_transition(1000,.01)
        worlds={seed:world for seed in cal.SEEDS}
        worlds[1140]=world.iloc[:400]
        rows,summary=cal.warning_diagnostic(worlds)
        invalid=rows[rows.seed==1140].iloc[0]
        self.assertFalse(invalid.valid)
        self.assertTrue(np.isnan(invalid.auc_warning_seed))
        self.assertEqual(summary['invalid_worlds'],1)
        self.assertEqual(summary['invalid_seeds'],'1140')

    def test_warning_rejects_noncalibration_seed(self):
        with self.assertRaises(ValueError):
            cal.warning_diagnostic({42:None})
