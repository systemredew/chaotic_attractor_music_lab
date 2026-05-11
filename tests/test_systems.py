from __future__ import annotations

import numpy as np

from systems import HenonMap, LogisticMap, LorenzSystem, RosslerSystem


def test_lorenz_derivatives_has_three_values() -> None:
    assert LorenzSystem().derivatives().shape == (3,)


def test_rossler_derivatives_has_three_values() -> None:
    assert RosslerSystem().derivatives().shape == (3,)


def test_henon_updates_state() -> None:
    system = HenonMap()
    before = system.current_point().copy()
    after = system.update()
    assert not np.allclose(before, after)


def test_logistic_value_stays_in_unit_interval() -> None:
    system = LogisticMap(r=3.7, x0=0.5)
    for _ in range(20):
        point = system.update()
        assert 0.0 <= point[1] <= 1.0
