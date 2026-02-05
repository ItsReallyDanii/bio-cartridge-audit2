import numpy as np
from src.baseline_v1_1_2b import run_simulation, sample_priors, MAX_CAPACITY


def test_simulator_invariants():
    n = 50
    samples = sample_priors(n)
    mw, mp, mi = run_simulation(samples)

    assert mw.shape == (n, 168)
    assert not np.isnan(mw).any()
    assert (mw >= 0).all()
    assert (mp >= 0).all()
    assert (mi >= 0).all()
    assert (mw <= MAX_CAPACITY + 1e-9).all()
    assert (np.diff(mp, axis=1) >= 0).all()
    assert (np.diff(mi, axis=1) >= 0).all()
