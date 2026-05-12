from __future__ import annotations

from dataclasses import dataclass
from collections import deque
import math

import numpy as np

import config
from math_core.integrators import rk4_step
from systems.base_system import Array, BaseSystem


def estimate_lyapunov(system: BaseSystem, steps: int = 1000, dt: float = 0.01, epsilon: float = 1e-7) -> float:
    estimator = LyapunovEstimator(system, dt=dt, epsilon=epsilon)
    value = 0.0
    for _ in range(steps):
        value = estimator.step()
    return value


@dataclass
class LyapunovEstimator:
    system: BaseSystem
    dt: float = config.DEFAULT_DT
    epsilon: float = config.LYAPUNOV_EPSILON
    renormalize_every: int = config.LYAPUNOV_RENORMALIZE_EVERY

    def __post_init__(self) -> None:
        base_state = self.system.current_point()
        if self.system.name == "Logistic":
            base_state = np.asarray([self.system.state[0]], dtype=np.float64)
        perturbation = np.zeros_like(base_state)
        perturbation[0] = self.epsilon
        self.reference = np.asarray(base_state, dtype=np.float64)
        self.neighbor = self.reference + perturbation
        self.iteration = 0
        self.values: deque[float] = deque(maxlen=config.LYAPUNOV_WINDOW)

    def reset(self) -> None:
        self.__post_init__()

    def step(self) -> float:
        self.iteration += 1
        with np.errstate(over="ignore", invalid="ignore"):
            if self.system.is_discrete:
                self.reference = self._map_next(self.reference)
                self.neighbor = self._map_next(self.neighbor)
            else:
                self.reference = rk4_step(self.system, self.reference, self.dt)
                self.neighbor = rk4_step(self.system, self.neighbor, self.dt)

        if not (np.all(np.isfinite(self.reference)) and np.all(np.isfinite(self.neighbor))):
            self.reset()
            return self.current()

        distance = float(np.linalg.norm(self.neighbor - self.reference))
        if distance <= 1e-15 or not math.isfinite(distance):
            return self.current()

        if self.iteration % self.renormalize_every == 0:
            self.values.append(math.log(distance / self.epsilon))
            direction = (self.neighbor - self.reference) / distance
            self.neighbor = self.reference + direction * self.epsilon
        return self.current()

    def current(self) -> float:
        if not self.values:
            return 0.0
        time_scale = self.renormalize_every * (self.dt if not self.system.is_discrete else 1.0)
        value = float(sum(self.values) / (len(self.values) * time_scale))
        return value if math.isfinite(value) else 0.0

    def _map_next(self, state: Array) -> Array:
        return self.system.next_state(state)  # type: ignore[attr-defined]
