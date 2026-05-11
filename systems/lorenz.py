from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .base_system import Array, BaseSystem


@dataclass
class LorenzSystem(BaseSystem):
    sigma: float = 10.0
    rho: float = 28.0
    beta: float = 8.0 / 3.0

    def __init__(
        self,
        sigma: float = 10.0,
        rho: float = 28.0,
        beta: float = 8.0 / 3.0,
        initial_state: Array | None = None,
    ) -> None:
        state = np.asarray(initial_state if initial_state is not None else [0.1, 1.0, 1.05], dtype=np.float64)
        super().__init__("Lorenz", state, {"sigma": sigma, "rho": rho, "beta": beta})
        self.sigma = sigma
        self.rho = rho
        self.beta = beta

    def derivatives(self, state: Array | None = None) -> Array:
        x, y, z = np.asarray(state if state is not None else self.state, dtype=np.float64)
        return np.asarray(
            [
                self.sigma * (y - x),
                x * (self.rho - z) - y,
                x * y - self.beta * z,
            ],
            dtype=np.float64,
        )

    def reset(self) -> None:
        self.state = np.asarray([0.1, 1.0, 1.05], dtype=np.float64)

    def _constructor_kwargs(self) -> dict[str, float]:
        return {"sigma": self.sigma, "rho": self.rho, "beta": self.beta}
