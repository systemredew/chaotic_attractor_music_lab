from __future__ import annotations

from collections import deque

import numpy as np
import pygame

import config
from systems.base_system import Array
from visual.camera import Camera
from visual.color_mapper import speed_color
from visual.controls import ControlPanel, UIState
from visual.ui_overlay import UIOverlay


class Renderer:
    def __init__(self, width: int = config.WINDOW_WIDTH, height: int = config.WINDOW_HEIGHT) -> None:
        self.width = width
        self.height = height
        self.windowed_size = (width, height)
        self.fullscreen = False
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption("Chaotic Attractor Music Lab")
        self.visual_rect = pygame.Rect(0, 0, width, height)
        self.camera = Camera(width=width, height=self.visual_rect.height)
        self.overlay = UIOverlay()
        self.controls = ControlPanel(width, height)
        self.trail: deque[tuple[Array, float, float]] = deque(maxlen=config.TRAIL_LIMIT)
        self.pulse_power = 0.0
        self.dragging_camera = False
        self.trail_limit = config.TRAIL_LIMIT

    def resize(self, width: int, height: int) -> None:
        self.width = max(config.MIN_WINDOW_WIDTH, width)
        self.height = max(config.MIN_WINDOW_HEIGHT, height)
        if not self.fullscreen:
            self.windowed_size = (self.width, self.height)
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        self.visual_rect = pygame.Rect(0, 0, self.width, self.height)
        self.camera.width = self.width
        self.camera.height = self.height
        self.controls.resize(self.width, self.height)

    def toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.width, self.height = self.screen.get_size()
        else:
            self.width, self.height = self.windowed_size
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        self.visual_rect = pygame.Rect(0, 0, self.width, self.height)
        self.camera.width = self.width
        self.camera.height = self.height
        self.controls.resize(self.width, self.height)

    def reset_trail(self) -> None:
        self.trail.clear()

    def append_point(self, point: Array, speed: float, chaos: float) -> None:
        self.trail.append((np.asarray(point, dtype=np.float64), speed, chaos))

    def set_trail_limit(self, limit: int) -> None:
        limit = int(np.clip(limit, config.MIN_TRAIL_LIMIT, config.MAX_TRAIL_LIMIT))
        if limit == self.trail_limit:
            return
        self.trail_limit = limit
        self.trail = deque(self.trail, maxlen=limit)

    def trigger_note_pulse(self) -> None:
        self.pulse_power = 1.0

    def handle_ui_event(self, event: pygame.event.Event) -> tuple[str, float | None] | None:
        action = self.controls.handle_event(event)
        if action is not None:
            return action

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.visual_rect.collidepoint(event.pos):
            self.dragging_camera = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_camera = False
        elif event.type == pygame.MOUSEMOTION and self.dragging_camera:
            dx, dy = event.rel
            self.camera.rotate(dx * 0.008, dy * 0.008)
            return "camera_drag", None
        elif event.type == pygame.MOUSEWHEEL and self.visual_rect.collidepoint(pygame.mouse.get_pos()):
            self.camera.adjust_zoom(event.y * 0.8)
            return "camera_zoom", self.camera.zoom
        return None

    def render(
        self,
        system_name: str,
        lyapunov: float,
        scale_name: str,
        preset_name: str,
        current_note: int | None,
        fps: float,
        paused: bool,
        muted: bool,
        params: str,
        chaos_mode: bool,
        steps_per_frame: int,
        density_multiplier: float,
        preset_index: int,
        root_note: int,
        chaos_influence: float,
        trail_limit: int,
        auto_camera: bool,
    ) -> None:
        self.screen.fill(config.BACKGROUND_COLOR)
        pygame.draw.rect(self.screen, config.BACKGROUND_COLOR, self.visual_rect)
        if auto_camera:
            self.camera.rotate(0.004, 0.0)
        self.screen.set_clip(self.visual_rect)
        self._draw_3d_trail(system_name)
        self.screen.set_clip(None)

        status = "PAUSED" if paused else "RUNNING"
        sound = "MUTED" if muted else "LIVE"
        lines = [
            "Chaotic Attractor Music Lab",
            f"{preset_name} | {system_name} | {status} | {sound}",
            f"params: {params}",
            f"lyapunov: {lyapunov:+.4f} | scale: {scale_name} | note: {current_note or '-'} | fps: {fps:.1f}",
            f"speed: {steps_per_frame} | density: {density_multiplier:.2f} | root: {root_note} | chaos influence: {chaos_influence:.2f} | trail: {trail_limit}",
        ]
        self.overlay.draw(self.screen, lines)
        self.controls.draw(
            self.screen,
            UIState(
                preset_index=preset_index,
                paused=paused,
                muted=muted,
                chaos_mode=chaos_mode,
                steps_per_frame=steps_per_frame,
                density_multiplier=density_multiplier,
                root_note=root_note,
                chaos_influence=chaos_influence,
                trail_limit=trail_limit,
                scale_name=scale_name,
                camera_rotation_x=self.camera.rotation_x,
                camera_rotation_y=self.camera.rotation_y,
                camera_zoom=self.camera.zoom,
                auto_camera=auto_camera,
            ),
        )
        self.pulse_power *= config.PULSE_DECAY
        pygame.display.flip()

    def _draw_3d_trail(self, system_name: str) -> None:
        previous: tuple[int, int] | None = None
        previous_depth = 0.0
        for point, point_speed, chaos in self.trail:
            projected_point = self._point_to_3d(point, system_name)
            x, y, depth = self.camera.project_with_depth(projected_point)
            projected = (x, y)
            color = self._shade_depth(speed_color(point_speed, chaos), depth)
            if previous is not None:
                thickness = 1 + int(self._depth_factor((previous_depth + depth) * 0.5) > 0.72)
                pygame.draw.line(self.screen, color, previous, projected, thickness)
            previous = projected
            previous_depth = depth
        if previous is not None:
            self._draw_current_point(previous)

    def _point_to_3d(self, point: Array, system_name: str) -> Array:
        values = np.asarray(point, dtype=np.float64)
        if system_name in {"Lorenz", "Rossler"}:
            return values[:3]
        if system_name == "Henon":
            x = float(values[0])
            y = float(values[1]) if values.size > 1 else 0.0
            z = np.sin(x * 5.0) * 5.0 + np.cos(y * 12.0) * 4.0
            return np.asarray([x * 22.0, y * 46.0, z], dtype=np.float64)
        if system_name == "Logistic":
            r = float(values[0])
            x = float(values[1]) if values.size > 1 else 0.0
            angle = (r - config.BIFURCATION_R_MIN) / (config.BIFURCATION_R_MAX - config.BIFURCATION_R_MIN) * np.pi * 5.0
            radius = 12.0 + x * 26.0
            return np.asarray(
                [
                    np.cos(angle) * radius,
                    (x - 0.5) * 64.0,
                    np.sin(angle) * radius + (r - 3.25) * 10.0,
                ],
                dtype=np.float64,
            )
        return np.pad(values, (0, max(0, 3 - values.size)), mode="constant")[:3]

    def _draw_current_point(self, point: tuple[int, int]) -> None:
        radius = config.POINT_RADIUS + 2 + int(self.pulse_power * config.PULSE_RADIUS_BOOST)
        if self.pulse_power > 0.03:
            pulse_color = (98, 210, 190)
            pygame.draw.circle(self.screen, pulse_color, point, radius, 2)
        core_radius = config.POINT_RADIUS + 3 + int(self.pulse_power * 5)
        pygame.draw.circle(self.screen, (255, 255, 245), point, core_radius)

    def _depth_factor(self, depth: float) -> float:
        return float(np.clip((depth + 40.0) / 85.0, 0.28, 1.0))

    def _shade_depth(self, color: tuple[int, int, int], depth: float) -> tuple[int, int, int]:
        factor = self._depth_factor(depth)
        return tuple(int(np.clip(channel * factor + 10 * (1.0 - factor), 0, 255)) for channel in color)
