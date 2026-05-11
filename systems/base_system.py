from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray


Array = NDArray[np.float64]


@dataclass
class BaseSystem(ABC):
    name: str
    state: Array
    parameters: dict[str, float] = field(default_factory=dict)
    is_discrete: bool = False

    @abstractmethod
    def derivatives(self, state: Array | None = None) -> Array:
        """Return derivatives for continuous systems or next delta for maps."""

    @abstractmethod
    def reset(self) -> None:
        """Reset state to a stable demonstration initial condition."""

    def update(self, dt: float = 0.01) -> Array:
        self.state = self.state + self.derivatives(self.state) * dt
        return self.current_point()

    def current_point(self) -> Array:
        return np.asarray(self.state, dtype=np.float64)

    def set_state(self, state: Array) -> None:
        self.state = np.asarray(state, dtype=np.float64)

    def parameter_text(self) -> str:
        return ", ".join(f"{key}={value:.3g}" for key, value in self.parameters.items())

    def clone_with_state(self, state: Array) -> "BaseSystem":
        copied = self.__class__(**self._constructor_kwargs())  # type: ignore[arg-type]
        copied.set_state(np.asarray(state, dtype=np.float64))
        return copied

    def _constructor_kwargs(self) -> dict[str, Any]:
        return dict(self.parameters)
