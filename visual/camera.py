from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

import config
from systems.base_system import Array


@dataclass
class Camera:
    width: int = config.WINDOW_WIDTH
    height: int = config.WINDOW_HEIGHT - config.UI_PANEL_HEIGHT
    rotation_x: float = 0.65
    rotation_y: float = -0.55
    zoom: float = 9.6

    def project(self, point3d: Array) -> tuple[int, int]:
        x, y, z = np.asarray(point3d, dtype=np.float64)[:3]
        cy, sy = math.cos(self.rotation_y), math.sin(self.rotation_y)
        cx, sx = math.cos(self.rotation_x), math.sin(self.rotation_x)
        xz = x * cy + z * sy
        zz = -x * sy + z * cy
        yz = y * cx - zz * sx
        screen_x = int(self.width * 0.5 + xz * self.zoom)
        screen_y = int(self.height * 0.53 - yz * self.zoom)
        return screen_x, screen_y
