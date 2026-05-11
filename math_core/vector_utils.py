from __future__ import annotations

import numpy as np

from systems.base_system import Array


def padded3(state: Array) -> Array:
    values = np.asarray(state, dtype=np.float64)
    if values.size >= 3:
        return values[:3]
    return np.pad(values, (0, 3 - values.size), mode="constant")


def speed(previous: Array | None, current: Array, dt: float) -> float:
    if previous is None or dt <= 0:
        return 0.0
    return float(np.linalg.norm(padded3(current) - padded3(previous)) / dt)


def acceleration(previous_speed: float, current_speed: float, dt: float) -> float:
    if dt <= 0:
        return 0.0
    return abs(current_speed - previous_speed) / dt


def curvature(a: Array, b: Array, c: Array) -> float:
    va = padded3(b) - padded3(a)
    vb = padded3(c) - padded3(b)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom <= 1e-12:
        return 0.0
    cos_angle = float(np.clip(np.dot(va, vb) / denom, -1.0, 1.0))
    return float(np.arccos(cos_angle))
