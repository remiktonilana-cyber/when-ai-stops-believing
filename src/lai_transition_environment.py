"""Separate E3 controlled transition; never changes the frozen E1 generator.

Row t contains time-t footprints and shock E_t, plus next_response R_(t+1).
The outcome is available only at evaluation time t+1. latent_stress and alpha
are hidden truth; T_warning/T_structural in attrs are benchmark metadata only.
F/C/L/nuisance are pre-shock observables. Shock is observable upon arrival.
This full research table is not an Agent-facing adapter.
"""
import numpy as np
import pandas as pd

N = 1200
T_WARNING = 400
T_STRUCTURAL = 600


def alpha_schedule(control=False):
    alpha = np.ones(N)
    if not control:
        alpha[600:900] = 1 + 2 * np.arange(300) / 299
        alpha[900:] = 3
    return alpha


def drift_schedule(d_plus):
    drift = np.zeros(N)
    drift[400:750] = d_plus
    return drift


def _rng_streams(seed):
    names = ('latent', 'measurement', 'nuisance', 'shock', 'response')
    return dict(zip(names, (np.random.default_rng(s) for s in
                           np.random.SeedSequence(seed).spawn(5))))


def generate_transition(seed, d_plus, *, control=False):
    """Matched calls share all five random realizations; only alpha differs.

    Z_-1=0; Z_t=.97*Z_(t-1)+d_t+N(0,.15²). d_t=d_plus for
    400<=t<750, zero elsewhere. F/C/L=sigmoid((1,.8,1.1)*Z+N(0,.5²)).
    Nuisance and shocks are separate N(0,1) streams. R=alpha*E+N(0,.5²).
    Default transition alpha: 1 through 599, 1+2*(t-600)/299 through
    899, then 3. Control alpha is always 1. No default scientific seed.
    """
    if not np.isfinite(d_plus):
        raise ValueError('d_plus must be finite')
    rng = _rng_streams(seed)
    innovation = rng['latent'].normal(0, .15, N)
    drift = drift_schedule(d_plus)
    stress = np.empty(N)
    previous = 0.
    for t in range(N):
        previous = .97 * previous + drift[t] + innovation[t]
        stress[t] = previous
    logits = stress[:, None] * [1, .8, 1.1] + rng['measurement'].normal(0, .5, (N, 3))
    footprints = np.exp(-np.logaddexp(0, -logits))
    nuisance = rng['nuisance'].normal(0, 1, N)
    shock = rng['shock'].normal(0, 1, N)
    noise = rng['response'].normal(0, .5, N)
    alpha = alpha_schedule(control)
    data = pd.DataFrame(dict(t=np.arange(N), latent_stress=stress,
                            fragility=footprints[:, 0], crowding=footprints[:, 1],
                            liquidity_stress=footprints[:, 2], nuisance=nuisance,
                            alpha=alpha, shock=shock, next_response=alpha * shock + noise))
    data.attrs.update(T_warning=T_WARNING, T_structural=T_STRUCTURAL)
    return data
