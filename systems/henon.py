from __future__ import annotations

import numpy as np

from .base_system import Array, BaseSystem


class HenonMap(BaseSystem):
    def __init__(self, a: float = 1.4, b: float = 0.3, initial_state: Array | None = None) -> None:
        state = np.asarray(initial_state if initial_state is not None else [0.1, 0.1], dtype=np.float64)
        super().__init__("Henon", state, {"a": a, "b": b}, is_discrete=True)
        self.a = a
        self.b = b

    def derivatives(self, state: Array | None = None) -> Array:
        current = np.asarray(state if state is not None else self.state, dtype=np.float64)
        return self.next_state(current) - current

    def next_state(self, state: Array | None = None) -> Array:
        x, y = np.asarray(state if state is not None else self.state, dtype=np.float64)
        return np.asarray([1.0 - self.a * x * x + y, self.b * x], dtype=np.float64)

    def update(self, dt: float = 1.0) -> Array:
        self.state = self.next_state(self.state)
        return self.current_point()

    def reset(self) -> None:
        self.state = np.asarray([0.1, 0.1], dtype=np.float64)

    def _constructor_kwargs(self) -> dict[str, float]:
        return {"a": self.a, "b": self.b}
