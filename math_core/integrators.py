from __future__ import annotations

import numpy as np

from systems.base_system import Array, BaseSystem


def euler_step(system: BaseSystem, state: Array, dt: float) -> Array:
    return np.asarray(state, dtype=np.float64) + system.derivatives(state) * dt


def rk4_step(system: BaseSystem, state: Array, dt: float) -> Array:
    state = np.asarray(state, dtype=np.float64)
    k1 = system.derivatives(state)
    k2 = system.derivatives(state + 0.5 * dt * k1)
    k3 = system.derivatives(state + 0.5 * dt * k2)
    k4 = system.derivatives(state + dt * k3)
    return state + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
