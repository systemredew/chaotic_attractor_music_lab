from __future__ import annotations

import numpy as np


def speed_color(speed: float, chaos: float) -> tuple[int, int, int]:
    speed_value = float(np.clip(speed / 80.0, 0.0, 1.0))
    chaos_value = float(np.clip((chaos + 0.2) / 3.0, 0.0, 1.0))
    red = int(80 + 160 * chaos_value)
    green = int(120 + 110 * (1.0 - abs(speed_value - 0.5) * 2.0))
    blue = int(170 + 70 * speed_value)
    return red, green, blue
