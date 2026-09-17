"""Engineering construction checks for the separate E3 environment."""
import unittest
import numpy as np
import pandas as pd
from src import lai_transition_environment as env


class TransitionEnvironmentTests(unittest.TestCase):
    def test_length_and_hidden_metadata(self):
        data = env.generate_transition(1000, .01)
        self.assertEqual(len(data), 1200)
        self.assertEqual(data.attrs, dict(T_warning=400, T_structural=600))
        self.assertNotIn('T_warning', data.columns)
        self.assertNotIn('T_structural', data.columns)

    def test_frozen_alpha_schedule(self):
        alpha = env.alpha_schedule()
        np.testing.assert_array_equal(alpha[:600], np.ones(600))
        np.testing.assert_array_equal(alpha[600:900], 1 + 2 * (np.arange(600, 900)-600)/299)
        self.assertEqual(alpha[600], 1)
        self.assertEqual(alpha[899], 3)
        np.testing.assert_array_equal(alpha[900:], np.full(300, 3))
        np.testing.assert_array_equal(env.alpha_schedule(True), np.ones(1200))

    def test_drift_schedule(self):
        for d in (.01, .02, .03, .04):
            drift = env.drift_schedule(d)
            np.testing.assert_array_equal(drift[:400], np.zeros(400))
            np.testing.assert_array_equal(drift[400:750], np.full(350, d))
            np.testing.assert_array_equal(drift[750:], np.zeros(450))

    def test_matched_worlds_and_response_noise(self):
        transition = env.generate_transition(1000, .02)
        control = env.generate_transition(1000, .02, control=True)
        shared = ['t', 'latent_stress', 'fragility', 'crowding', 'liquidity_stress', 'nuisance', 'shock']
        pd.testing.assert_frame_equal(transition[shared], control[shared], check_exact=True)
        noise = np.random.default_rng(np.random.SeedSequence(1000).spawn(5)[4]).normal(0, .5, 1200)
        for data in (transition, control):
            np.testing.assert_array_equal(data.next_response, data.alpha * data.shock + noise)
        np.testing.assert_allclose(transition.next_response-control.next_response,
                                   (transition.alpha-control.alpha)*transition.shock, atol=1e-15)

    def test_streams_and_equations(self):
        data = env.generate_transition(1001, .03)
        seeds = np.random.SeedSequence(1001).spawn(5)
        innovation = np.random.default_rng(seeds[0]).normal(0, .15, 1200)
        np.testing.assert_allclose(data.latent_stress,
            .97*np.r_[0., data.latent_stress.to_numpy()[:-1]] + env.drift_schedule(.03) + innovation)
        noise = np.random.default_rng(seeds[1]).normal(0, .5, (1200, 3))
        expected = 1/(1+np.exp(-(data.latent_stress.to_numpy()[:, None]*[1,.8,1.1]+noise)))
        np.testing.assert_allclose(data[['fragility','crowding','liquidity_stress']], expected)
        np.testing.assert_array_equal(data.nuisance, np.random.default_rng(seeds[2]).normal(0,1,1200))
        np.testing.assert_array_equal(data.shock, np.random.default_rng(seeds[3]).normal(0,1,1200))
        changed = env.generate_transition(1001, .04)
        np.testing.assert_array_equal(data.shock, changed.shock)
        np.testing.assert_array_equal(data.nuisance, changed.nuisance)
        np.testing.assert_array_equal(data.next_response, changed.next_response)

    def test_determinism_and_different_seed(self):
        data = env.generate_transition(1000, .01)
        pd.testing.assert_frame_equal(data, env.generate_transition(1000,.01), check_exact=True)
        self.assertFalse(data.equals(env.generate_transition(1001,.01)))
