from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import config


def logistic_bifurcation_data(
    r_min: float = config.BIFURCATION_R_MIN,
    r_max: float = config.BIFURCATION_R_MAX,
    r_steps: int = config.BIFURCATION_R_STEPS,
    iterations: int = config.BIFURCATION_ITERATIONS,
    warmup: int = config.BIFURCATION_WARMUP,
    x0: float = 0.5,
) -> tuple[np.ndarray, np.ndarray]:
    r_values: list[float] = []
    x_values: list[float] = []
    for r in np.linspace(r_min, r_max, r_steps):
        x = x0
        for i in range(iterations):
            x = r * x * (1.0 - x)
            if i >= warmup:
                r_values.append(float(r))
                x_values.append(float(x))
    return np.asarray(r_values), np.asarray(x_values)


def save_logistic_bifurcation(path: str | Path = config.BIFURCATION_IMAGE) -> Path:
    output = Path(path)
    r_values, x_values = logistic_bifurcation_data()
    plt.figure(figsize=(12, 7), dpi=140)
    plt.plot(r_values, x_values, ",", color="#d9f99d", alpha=0.45)
    plt.title("Logistic Map Bifurcation Diagram")
    plt.xlabel("r")
    plt.ylabel("x")
    plt.tight_layout()
    plt.savefig(output)
    plt.close()
    return output
