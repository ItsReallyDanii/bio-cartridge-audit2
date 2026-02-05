import numpy as np
import pytest

from src.profile_loader import AuditIntegrityError
from src.baseline_v1_1_2b import (
    DEFAULT_PRIORS,
    build_prior_def,
    run_simulation,
    sample_priors,
)


def test_mode_a_null_op_hash_unchanged():
    np.random.seed(42)
    s1 = sample_priors(50, DEFAULT_PRIORS)
    m1, _, _ = run_simulation(s1)

    np.random.seed(42)
    resolved_def, prov = build_prior_def(None)
    s2 = sample_priors(50, resolved_def)
    m2, _, _ = run_simulation(s2)

    assert prov["profile_name"] == "baseline"
    assert np.array_equal(m1, m2)


def test_invalid_profile_name_raises_error():
    with pytest.raises(AuditIntegrityError):
        build_prior_def(profile_name="non_existent_profile")
