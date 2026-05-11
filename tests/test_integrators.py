from __future__ import annotations

from math_core.integrators import rk4_step
from systems import LorenzSystem


def test_rk4_does_not_crash_on_lorenz() -> None:
    system = LorenzSystem()
    next_state = rk4_step(system, system.current_point(), 0.01)
    assert next_state.shape == (3,)
