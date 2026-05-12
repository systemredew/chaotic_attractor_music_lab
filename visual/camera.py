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
    offset_x: float = 0.0
    offset_y: float = 0.0

    def project(self, point3d: Array) -> tuple[int, int]:
        screen_x, screen_y, _depth = self.project_with_depth(point3d)
        return screen_x, screen_y

    def project_with_depth(self, point3d: Array) -> tuple[int, int, float]:
        x, y, z = np.asarray(point3d, dtype=np.float64)[:3]
        cy, sy = math.cos(self.rotation_y), math.sin(self.rotation_y)
        cx, sx = math.cos(self.rotation_x), math.sin(self.rotation_x)
        xz = x * cy + z * sy
        zz = -x * sy + z * cy
        yz = y * cx - zz * sx
        depth = y * sx + zz * cx
        screen_x = int(self.width * 0.5 + self.offset_x + xz * self.zoom)
        screen_y = int(self.height * 0.53 + self.offset_y - yz * self.zoom)
        return screen_x, screen_y, float(depth)

    def rotate(self, delta_x: float, delta_y: float) -> None:
        self.rotation_y += delta_x
        self.rotation_x = float(np.clip(self.rotation_x + delta_y, -1.45, 1.45))

    def adjust_zoom(self, delta: float) -> None:
        self.zoom = float(np.clip(self.zoom + delta, config.MIN_CAMERA_ZOOM, config.MAX_CAMERA_ZOOM))

    def pan(self, delta_x: float, delta_y: float) -> None:
        self.offset_x += delta_x
        self.offset_y += delta_y
