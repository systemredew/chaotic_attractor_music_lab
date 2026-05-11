from __future__ import annotations

import numpy as np

from .base_system import Array, BaseSystem


class LogisticMap(BaseSystem):
    def __init__(
        self,
        r: float = 3.7,
        x0: float = 0.5,
        r_min: float = 2.5,
        r_max: float = 4.0,
        r_step: float = 0.0006,
    ) -> None:
        super().__init__("Logistic", np.asarray([x0], dtype=np.float64), {"r": r}, is_discrete=True)
        self.r = r
        self.x0 = x0
        self.r_min = r_min
        self.r_max = r_max
        self.r_step = r_step

    def derivatives(self, state: Array | None = None) -> Array:
        current = np.asarray(state if state is not None else self.state, dtype=np.float64)
        return self.next_state(current) - current

    def next_state(self, state: Array | None = None) -> Array:
        x = float(np.asarray(state if state is not None else self.state, dtype=np.float64)[0])
        return np.asarray([self.r * x * (1.0 - x)], dtype=np.float64)

    def update(self, dt: float = 1.0) -> Array:
        self.state = np.clip(self.next_state(self.state), 0.0, 1.0)
        self.r += self.r_step
        if self.r > self.r_max:
            self.r = self.r_min
        self.parameters["r"] = self.r
        return self.current_point()

    def reset(self) -> None:
        self.r = self.r_min
        self.parameters["r"] = self.r
        self.state = np.asarray([self.x0], dtype=np.float64)

    def current_point(self) -> Array:
        return np.asarray([self.r, float(self.state[0])], dtype=np.float64)

    def _constructor_kwargs(self) -> dict[str, float]:
        return {"r": self.r, "x0": self.x0, "r_min": self.r_min, "r_max": self.r_max, "r_step": self.r_step}
