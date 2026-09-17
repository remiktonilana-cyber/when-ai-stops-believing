"""Engineering tests for non-canonical calibration; no threshold selection."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from src import lai_calibration as calibration
from src.lai_environment import generate_environment


class CalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world = generate_environment(n_timesteps=2000, seed=1000)
        cls.row = calibration.analyze_world(cls.world, 1000)

    def test_exact_seed_set(self):
        self.assertEqual(calibration.CALIBRATION_SEEDS, tuple(range(1000, 1200)))
        self.assertEqual(len(calibration.CALIBRATION_SEEDS), 200)

    def test_canonical_seed_absent_and_rejected_before_generation(self):
        self.assertNotIn(42, calibration.CALIBRATION_SEEDS)
        with patch.object(calibration, "generate_environment") as generate:
            with self.assertRaises(ValueError):
                calibration.run_calibration((1000, 42))
            generate.assert_not_called()

    def test_default_requests_exactly_200_worlds(self):
        with patch.object(calibration, "generate_environment", return_value=self.world) as generate, \
                patch.object(calibration, "analyze_world", side_effect=lambda data, seed: {"seed": seed}):
            table = calibration.run_calibration()
        self.assertEqual(tuple(table.seed), tuple(range(1000, 1200)))
        self.assertEqual(generate.call_count, 200)
        for seed, call in zip(range(1000, 1200), generate.call_args_list):
            self.assertEqual(call.kwargs, {"n_timesteps": 2000, "seed": seed})

    def test_valid_row_required_fields(self):
        required = {
            "seed", "smd_abs_shock", "mean_abs_shock_resilient", "mean_abs_shock_amplifying",
            "raw_abs_shock_difference", "beta_0", "beta_1", "beta_2", "beta_3",
            "beta_3_se", "beta_3_ci_lower", "beta_3_ci_upper", "alpha_hat_resilient",
            "alpha_hat_amplifying", "auc_fcl", "auc_n", "auc_gap", "split_valid",
        }
        self.assertTrue(required.issubset(self.row))
        self.assertTrue(self.row["split_valid"])
        self.assertTrue(all(np.isfinite(self.row[key]) for key in required))
        self.assertAlmostEqual(self.row["auc_gap"], self.row["auc_fcl"] - self.row["auc_n"])

    def test_temporal_split_features_and_state_encoding(self):
        with patch.object(calibration, "_classifier_auc", return_value=0.5) as auc:
            calibration.analyze_world(self.world, 1000)
        self.assertEqual(auc.call_count, 2)
        for call, features in zip(auc.call_args_list, (calibration.FCL_FEATURES, calibration.NUISANCE_FEATURES)):
            data, state, train, test, actual_features = call.args
            np.testing.assert_array_equal(data.loc[train, "t"], np.arange(1400))
            np.testing.assert_array_equal(data.loc[test, "t"], np.arange(1400, 2000))
            np.testing.assert_array_equal(state, (self.world.latent_state == "AMPLIFYING").astype(int))
            self.assertEqual(actual_features, features)
        self.assertEqual(calibration.STATE_ENCODING, {"RESILIENT": 0, "AMPLIFYING": 1})

    def test_actual_classifier_inputs_and_train_only_scaling(self):
        original = calibration.make_pipeline
        pipelines = []

        def record_pipeline(*steps):
            model = original(*steps)
            pipelines.append(model)
            return model

        with patch.object(calibration, "make_pipeline", side_effect=record_pipeline):
            calibration.analyze_world(self.world, 1000)
        for model, features in zip(pipelines, (("fragility", "crowding", "liquidity_stress"), ("nuisance",))):
            scaler = model.steps[0][1]
            self.assertEqual(tuple(scaler.feature_names_in_), features)
            self.assertEqual(scaler.n_samples_seen_, 1400)
            np.testing.assert_allclose(scaler.mean_, self.world.loc[:1399, list(features)].mean())
            params = model.steps[1][1].get_params()
            for name, value in {"penalty": "l2", "C": 1.0, "solver": "lbfgs", "tol": 1e-4,
                                "max_iter": 1000, "fit_intercept": True,
                                "class_weight": None, "random_state": 0}.items():
                self.assertEqual(params[name], value)

    def test_hidden_and_postshock_values_cannot_change_auc(self):
        changed = self.world.copy()
        changed["latent_stress"] = 99999.0
        changed["next_response"] = -changed.next_response + 50
        changed["shock"] = -changed.shock
        row = calibration.analyze_world(changed, 1000)
        for name in ("auc_fcl", "auc_n", "auc_gap"):
            self.assertEqual(row[name], self.row[name])

    def test_smd_known_values(self):
        shock = np.array([-1., 3., -2., 4.])
        state = np.array([0, 0, 1, 1])
        result = calibration.shock_balance(shock, state)
        self.assertEqual(result, calibration.shock_balance(shock, state))
        self.assertEqual(result["raw_abs_shock_difference"], 1)
        self.assertAlmostEqual(result["smd_abs_shock"], 1 / np.sqrt(2))
        self.assertEqual(result["mean_shock_resilient"], 1)
        self.assertAlmostEqual(result["sd_shock_resilient"], np.sqrt(8))
        self.assertAlmostEqual(result["sd_abs_shock_amplifying"], np.sqrt(2))

    def test_regression_matches_independent_linear_algebra(self):
        state = (self.world.latent_state == "AMPLIFYING").to_numpy().astype(int)
        shock = self.world.shock.to_numpy()
        response = self.world.next_response.to_numpy()
        design = np.column_stack((np.ones(2000), shock, state, shock * state))
        beta = np.linalg.lstsq(design, response, rcond=None)[0]
        variance = np.sum((response - design @ beta) ** 2) / 1996
        se = np.sqrt((variance * np.linalg.inv(design.T @ design))[3, 3])
        from scipy.stats import t
        margin = t.ppf(.975, 1996) * se
        np.testing.assert_allclose([self.row[f"beta_{i}"] for i in range(4)], beta)
        self.assertAlmostEqual(self.row["beta_3_se"], se)
        self.assertAlmostEqual(self.row["beta_3_ci_lower"], beta[3] - margin)
        self.assertAlmostEqual(self.row["beta_3_ci_upper"], beta[3] + margin)
        self.assertAlmostEqual(self.row["alpha_hat_resilient"], beta[1])
        self.assertAlmostEqual(self.row["alpha_hat_amplifying"], beta[1] + beta[3])

    def test_small_subset_determinism(self):
        first = calibration.run_calibration((1000, 1001))
        second = calibration.run_calibration((1000, 1001))
        pd.testing.assert_frame_equal(first, second, check_exact=True)

    def test_split_failures_retained_without_fitting(self):
        for split, indices in (("train", slice(0, 1399)), ("test", slice(1400, 1999))):
            world = self.world.copy()
            world.loc[indices, "latent_state"] = "RESILIENT"
            with patch.object(calibration, "generate_environment", return_value=world), \
                    patch.object(calibration, "_classifier_auc") as classifier:
                table = calibration.run_calibration((1000,))
            classifier.assert_not_called()
            self.assertEqual(len(table), 1)
            self.assertFalse(table.iloc[0].split_valid)
            self.assertEqual(table.iloc[0].split_failure, f"{split}_single_class")
            self.assertTrue(table[["auc_fcl", "auc_n", "auc_gap"]].isna().all().all())
            self.assertTrue(np.isfinite(table.iloc[0].beta_3))

    def test_summary_filters_invalid_and_nonfinite_auc(self):
        table = pd.DataFrame([self.row] * 4)
        table.loc[0, "auc_fcl"] = .8
        table.loc[1, "auc_fcl"] = np.inf
        table.loc[2, "auc_fcl"] = np.nan
        table.loc[3, ["split_valid", "auc_fcl"]] = [False, .1]
        summary = calibration.summarize(table)
        self.assertEqual(summary.loc["auc_fcl", "count"], 1)
        self.assertEqual(summary.loc["auc_fcl", "mean"], .8)
        self.assertEqual(summary.loc["beta_3", "count"], 4)

    def test_summary_quantiles_and_sample_sd(self):
        table = pd.DataFrame([self.row] * 4)
        table["beta_3"] = [1, 2, 3, 4]
        row = calibration.summarize(table).loc["beta_3"]
        self.assertEqual(row["mean"], 2.5)
        self.assertAlmostEqual(row["std"], np.std([1, 2, 3, 4], ddof=1))
        np.testing.assert_allclose(row[["min", "2.5%", "25%", "median", "75%", "97.5%", "max"]],
                                   [1, 1.075, 1.75, 2.5, 3.25, 3.925, 4])

    def test_artifacts_require_complete_seed_set(self):
        with tempfile.TemporaryDirectory() as directory:
            csv = Path(directory) / "data.csv"
            report = Path(directory) / "report.md"
            with self.assertRaises(ValueError):
                calibration.write_artifacts(pd.DataFrame([self.row]), csv, report)
            self.assertFalse(csv.exists())
            table = pd.DataFrame([dict(self.row, seed=seed) for seed in calibration.CALIBRATION_SEEDS])
            calibration.write_artifacts(table, csv, report)
            saved = pd.read_csv(csv)
            self.assertEqual(tuple(saved.seed), calibration.CALIBRATION_SEEDS)
            self.assertNotIn(42, saved.seed.tolist())
            self.assertIn("These results do not constitute the canonical Experiment A and do not validate LAI.", report.read_text())

    def test_invalid_seed_requests(self):
        for seeds in ((), (1000, 1000), (999,), (1200,), (1000.0,)):
            with self.subTest(seeds=seeds), self.assertRaises(ValueError):
                calibration.run_calibration(seeds)

    def test_bad_time_order_rejected(self):
        with self.assertRaises(ValueError):
            calibration.analyze_world(self.world.iloc[::-1], 1000)


if __name__ == "__main__":
    unittest.main()
