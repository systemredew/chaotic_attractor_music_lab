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
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Chaotic Attractor Music Lab")
        self.visual_rect = pygame.Rect(0, 0, width, height - config.UI_PANEL_HEIGHT)
        self.camera = Camera(width=width, height=self.visual_rect.height)
        self.overlay = UIOverlay()
        self.controls = ControlPanel(width, height)
        self.trail: deque[tuple[Array, float, float]] = deque(maxlen=config.TRAIL_LIMIT)
        self.pulse_power = 0.0

    def reset_trail(self) -> None:
        self.trail.clear()

    def append_point(self, point: Array, speed: float, chaos: float) -> None:
        self.trail.append((np.asarray(point, dtype=np.float64), speed, chaos))

    def trigger_note_pulse(self) -> None:
        self.pulse_power = 1.0

    def handle_ui_event(self, event: pygame.event.Event) -> tuple[str, float | None] | None:
        return self.controls.handle_event(event)

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
    ) -> None:
        self.screen.fill(config.BACKGROUND_COLOR)
        pygame.draw.rect(self.screen, config.BACKGROUND_COLOR, self.visual_rect)
        self.screen.set_clip(self.visual_rect)
        if system_name in {"Lorenz", "Rossler"}:
            self._draw_3d_trail()
        else:
            self._draw_2d_trail(system_name)
        self.screen.set_clip(None)

        status = "PAUSED" if paused else "RUNNING"
        sound = "MUTED" if muted else "LIVE"
        lines = [
            "Chaotic Attractor Music Lab",
            f"{preset_name} | {system_name} | {status} | {sound}",
            f"params: {params}",
            f"lyapunov: {lyapunov:+.4f} | scale: {scale_name} | note: {current_note or '-'} | fps: {fps:.1f}",
            f"speed: {steps_per_frame} | density: {density_multiplier:.2f} | chaos mode: {'on' if chaos_mode else 'off'}",
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
            ),
        )
        self.pulse_power *= config.PULSE_DECAY
        pygame.display.flip()

    def _draw_3d_trail(self) -> None:
        previous: tuple[int, int] | None = None
        for point, point_speed, chaos in self.trail:
            projected = self.camera.project(point)
            color = speed_color(point_speed, chaos)
            if previous is not None:
                pygame.draw.line(self.screen, color, previous, projected, 1)
            previous = projected
        if previous is not None:
            self._draw_current_point(previous)

    def _draw_2d_trail(self, system_name: str) -> None:
        bounds = config.SYSTEM_BOUNDS[system_name]
        previous: tuple[int, int] | None = None
        for point, point_speed, chaos in self.trail:
            x, y = float(point[0]), float(point[1]) if len(point) > 1 else 0.0
            screen_x = int(np.interp(x, [bounds.x_min, bounds.x_max], [config.VISUAL_PADDING, self.width - config.VISUAL_PADDING]))
            screen_y = int(
                np.interp(
                    y,
                    [bounds.y_min, bounds.y_max],
                    [self.visual_rect.bottom - config.VISUAL_PADDING, 96],
                )
            )
            projected = (screen_x, screen_y)
            color = speed_color(point_speed * 25.0, chaos)
            if previous is not None:
                pygame.draw.line(self.screen, color, previous, projected, 1)
            previous = projected
        if previous is not None:
            self._draw_current_point(previous)

    def _draw_current_point(self, point: tuple[int, int]) -> None:
        radius = config.POINT_RADIUS + 2 + int(self.pulse_power * config.PULSE_RADIUS_BOOST)
        if self.pulse_power > 0.03:
            pulse_color = (98, 210, 190)
            pygame.draw.circle(self.screen, pulse_color, point, radius, 2)
        core_radius = config.POINT_RADIUS + 3 + int(self.pulse_power * 5)
        pygame.draw.circle(self.screen, (255, 255, 245), point, core_radius)
