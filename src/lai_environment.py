"""Isolated LAI E1 synthetic system; no benchmark or agent integration.

Each row pairs time-t state and shock with the outcome R_(t+1).
Pre-shock observables: t, fragility, crowding, liquidity_stress, nuisance.
shock is observable when it arrives, after those footprints and before response.
Hidden ground truth: latent_stress, latent_state, and DataFrame.attrs['theta'].
next_response is a post-shock outcome, never time-t pre-shock information.

The full-trajectory quantile is an offline synthetic ground-truth construction,
not an online estimate or a real-world LAI definition. It uses no responses.
"""

import numpy as np
import pandas as pd


def _rng_streams(seed):
    """Fixed child-stream order; all RNG state is local to a generation call."""
    names = ("latent", "measurement", "nuisance", "shock", "response")
    children = np.random.SeedSequence(seed).spawn(len(names))
    return dict(zip(names, (np.random.default_rng(child) for child in children)))


def _response(shock, latent_state, noise):
    """Symmetric state-dependent shock sensitivity with additive noise."""
    alpha = np.where(latent_state == "AMPLIFYING", 3.0, 1.0)
    return alpha * shock + noise


def generate_environment(n_timesteps=2000, seed=42, *, drift=0.0):
    """Return research data, including hidden truth, as a pandas DataFrame.

    Z_t = .97 Z_(t-1) + drift[t] + eta_t, eta_t ~ N(0, .15^2).
    Engineering initialization: Z_(-1)=0, t=0,...,n_timesteps-1; no burn-in.
    drift is a finite scalar or a finite length-n_timesteps sequence, fixed
    before simulation. A caller can supply piecewise drift for future phases.
    E1 defaults to zero drift and supplies no phase schedule.

    F/C/L = sigmoid((1, .8, 1.1)*Z + independent N(0, .5^2) noise).
    N and E are independent standard normals from separate streams.
    S is AMPLIFYING iff Z > Q_.70(Z), using linear quantile interpolation.
    R_(t+1) = (3 if AMPLIFYING else 1)*E_t + N(0, .5^2).
    The persistence and noise scales are simulation choices, not estimates.
    """
    if (isinstance(n_timesteps, (bool, np.bool_))
            or not isinstance(n_timesteps, (int, np.integer))
            or n_timesteps < 1):
        raise ValueError("n_timesteps must be a positive integer")
    drift_values = np.asarray(drift, dtype=float)
    if drift_values.ndim == 0:
        drift_values = np.full(n_timesteps, float(drift_values))
    if drift_values.shape != (n_timesteps,) or not np.isfinite(drift_values).all():
        raise ValueError("drift must be finite and scalar or length n_timesteps")

    rng = _rng_streams(seed)
    innovations = rng["latent"].normal(0.0, 0.15, n_timesteps)
    stress = np.empty(n_timesteps)
    previous = 0.0
    for t in range(n_timesteps):
        previous = 0.97 * previous + drift_values[t] + innovations[t]
        stress[t] = previous
    if not np.isfinite(stress).all():
        raise ValueError("drift produced nonfinite latent stress")

    measurement = rng["measurement"].normal(0.0, 0.5, (n_timesteps, 3))
    logits = stress[:, None] * np.array([1.0, 0.8, 1.1]) + measurement
    footprints = np.exp(-np.logaddexp(0.0, -logits))  # Stable sigmoid.
    nuisance = rng["nuisance"].normal(0.0, 1.0, n_timesteps)
    # NumPy's default is linear interpolation, including older repo environments.
    theta = float(np.quantile(stress, 0.70))
    state = np.where(stress > theta, "AMPLIFYING", "RESILIENT")

    # Neither shock nor its RNG depends on stress, state, or measurement draws.
    shock = rng["shock"].normal(0.0, 1.0, n_timesteps)
    noise = rng["response"].normal(0.0, 0.5, n_timesteps)
    response = _response(shock, state, noise)
    data = pd.DataFrame({
        "t": np.arange(n_timesteps),
        "latent_stress": stress,
        "fragility": footprints[:, 0],
        "crowding": footprints[:, 1],
        "liquidity_stress": footprints[:, 2],
        "nuisance": nuisance,
        "latent_state": state,
        "shock": shock,
        "next_response": response,
    })
    data.attrs["theta"] = theta
    return data
