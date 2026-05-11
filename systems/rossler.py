from __future__ import annotations

import numpy as np

from .base_system import Array, BaseSystem


class RosslerSystem(BaseSystem):
    def __init__(
        self,
        a: float = 0.2,
        b: float = 0.2,
        c: float = 5.7,
        initial_state: Array | None = None,
    ) -> None:
        state = np.asarray(initial_state if initial_state is not None else [0.2, 0.1, 0.1], dtype=np.float64)
        super().__init__("Rossler", state, {"a": a, "b": b, "c": c})
        self.a = a
        self.b = b
        self.c = c

    def derivatives(self, state: Array | None = None) -> Array:
        x, y, z = np.asarray(state if state is not None else self.state, dtype=np.float64)
        return np.asarray(
            [
                -y - z,
                x + self.a * y,
                self.b + z * (x - self.c),
            ],
            dtype=np.float64,
        )

    def reset(self) -> None:
        self.state = np.asarray([0.2, 0.1, 0.1], dtype=np.float64)

    def _constructor_kwargs(self) -> dict[str, float]:
        return {"a": self.a, "b": self.b, "c": self.c}
