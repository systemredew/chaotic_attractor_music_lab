from __future__ import annotations

import numpy as np


def shannon_entropy(values: list[float] | np.ndarray, bins: int = 32) -> float:
    if len(values) == 0:
        return 0.0
    counts, _ = np.histogram(values, bins=bins, density=False)
    probabilities = counts[counts > 0] / max(1, counts.sum())
    return float(-np.sum(probabilities * np.log2(probabilities)))
