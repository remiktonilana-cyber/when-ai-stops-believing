"""Construction tests for E1, not Experiment A statistical validation."""

import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from src.lai_environment import _response, _rng_streams, generate_environment


class LAIEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.data = generate_environment()

    def test_canonical_rows_and_time(self):
        self.assertEqual(len(self.data), 2000)
        np.testing.assert_array_equal(self.data.t, np.arange(2000))

    def test_required_fields(self):
        self.assertEqual(set(self.data.columns), {
            "t", "latent_stress", "fragility", "crowding", "liquidity_stress",
            "nuisance", "latent_state", "shock", "next_response",
        })

    def test_repeatability(self):
        pd.testing.assert_frame_equal(self.data, generate_environment(), check_exact=True)
        self.assertEqual(self.data.attrs, generate_environment().attrs)

    def test_different_seeds(self):
        other = generate_environment(seed=43)
        for field in ("latent_stress", "fragility", "nuisance", "shock", "next_response"):
            self.assertFalse(np.array_equal(self.data[field], other[field]))

    def test_state_labels_and_threshold(self):
        self.assertEqual(set(self.data.latent_state), {"RESILIENT", "AMPLIFYING"})
        theta = np.quantile(self.data.latent_stress, 0.7)
        self.assertEqual(self.data.attrs["theta"], theta)
        np.testing.assert_array_equal(
            self.data.latent_state == "AMPLIFYING", self.data.latent_stress > theta,
        )

    def test_amplifying_share(self):
        self.assertAlmostEqual((self.data.latent_state == "AMPLIFYING").mean(), 0.30)

    def test_bounded_footprints(self):
        values = self.data[["fragility", "crowding", "liquidity_stress"]].to_numpy()
        self.assertTrue(((values >= 0) & (values <= 1)).all())

    def test_latent_recurrence(self):
        seed = np.random.SeedSequence(42).spawn(5)[0]
        innovations = np.random.default_rng(seed).normal(0, 0.15, 2000)
        previous = np.r_[0.0, self.data.latent_stress.to_numpy()[:-1]]
        np.testing.assert_allclose(self.data.latent_stress, 0.97 * previous + innovations)

    def test_noisy_footprint_equations(self):
        seed = np.random.SeedSequence(42).spawn(5)[1]
        noise = np.random.default_rng(seed).normal(0, 0.5, (2000, 3))
        logits = self.data.latent_stress.to_numpy()[:, None] * [1, 0.8, 1.1] + noise
        expected = 1 / (1 + np.exp(-logits))
        np.testing.assert_allclose(
            self.data[["fragility", "crowding", "liquidity_stress"]], expected,
        )

    def test_nuisance_independent_stream(self):
        seed = np.random.SeedSequence(42).spawn(5)[2]
        expected = np.random.default_rng(seed).normal(0, 1, 2000)
        np.testing.assert_array_equal(self.data.nuisance, expected)
        changed = generate_environment(drift=np.linspace(-0.2, 0.2, 2000))
        self.assertFalse(np.array_equal(self.data.latent_stress, changed.latent_stress))
        np.testing.assert_array_equal(self.data.nuisance, changed.nuisance)

    def test_shock_independent_of_stress_and_state(self):
        seed = np.random.SeedSequence(42).spawn(5)[3]
        expected = np.random.default_rng(seed).normal(0, 1, 2000)
        np.testing.assert_array_equal(self.data.shock, expected)
        changed = generate_environment(drift=np.linspace(-0.2, 0.2, 2000))
        self.assertFalse(np.array_equal(self.data.latent_state, changed.latent_state))
        np.testing.assert_array_equal(self.data.shock, changed.shock)

    def test_response_coefficients_and_noise(self):
        seed = np.random.SeedSequence(42).spawn(5)[4]
        noise = np.random.default_rng(seed).normal(0, 0.5, 2000)
        expected = np.where(self.data.latent_state == "AMPLIFYING", 3, 1) * self.data.shock + noise
        np.testing.assert_array_equal(self.data.next_response, expected)

    def test_signed_shock_symmetry(self):
        states = np.array(["RESILIENT", "AMPLIFYING"])
        positive = _response(np.ones(2), states, np.zeros(2))
        negative = _response(-np.ones(2), states, np.zeros(2))
        np.testing.assert_array_equal(positive, [1, 3])
        np.testing.assert_array_equal(negative, [-1, -3])
        np.testing.assert_array_equal(_response(np.zeros(2), states, np.zeros(2)), [0, 0])

    def test_response_noise_cannot_change_upstream_fields(self):
        streams = _rng_streams(42)
        streams["response"] = np.random.default_rng(9876)
        with patch("src.lai_environment._rng_streams", return_value=streams):
            changed = generate_environment()
        pd.testing.assert_frame_equal(
            self.data.drop(columns="next_response"), changed.drop(columns="next_response"),
            check_exact=True,
        )
        self.assertEqual(self.data.attrs, changed.attrs)
        self.assertFalse(np.array_equal(self.data.next_response, changed.next_response))

    def test_response_mechanism_cannot_change_upstream_fields(self):
        with patch("src.lai_environment._response", return_value=np.full(2000, 123.0)):
            changed = generate_environment()
        pd.testing.assert_frame_equal(
            self.data.drop(columns="next_response"), changed.drop(columns="next_response"),
            check_exact=True,
        )
        self.assertEqual(self.data.attrs, changed.attrs)
        np.testing.assert_array_equal(changed.next_response, np.full(2000, 123.0))

    def test_configurable_phase_drift(self):
        drift = np.r_[np.zeros(10), np.full(10, 0.02), np.full(10, 0.05)]
        base = generate_environment(n_timesteps=30)
        changed = generate_environment(n_timesteps=30, drift=drift)
        difference = []
        previous = 0.0
        for value in drift:
            previous = 0.97 * previous + value
            difference.append(previous)
        np.testing.assert_allclose(changed.latent_stress - base.latent_stress, difference, atol=1e-15)
        pd.testing.assert_frame_equal(base, generate_environment(n_timesteps=30, drift=np.zeros(30)))
        pd.testing.assert_frame_equal(
            generate_environment(n_timesteps=30, drift=0.02),
            generate_environment(n_timesteps=30, drift=np.full(30, 0.02)),
        )

    def test_invalid_configuration(self):
        for n in (0, -1, 2.5, True):
            with self.subTest(n=n), self.assertRaises(ValueError):
                generate_environment(n_timesteps=n)
        for drift in ([0, 1], np.nan, np.inf, [[0] * 3]):
            with self.subTest(drift=drift), self.assertRaises(ValueError):
                generate_environment(n_timesteps=3, drift=drift)


if __name__ == "__main__":
    unittest.main()
