from __future__ import annotations

from dataclasses import dataclass

import pygame

import config
from presets.presets import PRESETS


@dataclass
class UIState:
    preset_index: int
    paused: bool
    muted: bool
    chaos_mode: bool
    steps_per_frame: int
    density_multiplier: float
    root_note: int
    chaos_influence: float
    trail_limit: int
    scale_name: str
    camera_rotation_x: float
    camera_rotation_y: float
    camera_zoom: float
    auto_camera: bool


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    action: str
    active: bool = False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, mouse_pos: tuple[int, int]) -> None:
        hovered = self.rect.collidepoint(mouse_pos)
        if self.active:
            fill = config.UI_ACTIVE_COLOR
            border = config.UI_ACCENT_COLOR
        elif hovered:
            fill = config.UI_HOVER_COLOR
            border = config.UI_BORDER_COLOR
        else:
            fill = config.UI_PANEL_COLOR
            border = config.UI_BORDER_COLOR
        button_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.rect(button_surface, (*fill, config.UI_PANEL_ALPHA), button_surface.get_rect(), border_radius=config.UI_RADIUS)
        surface.blit(button_surface, self.rect.topleft)
        pygame.draw.rect(surface, border, self.rect, 1, border_radius=config.UI_RADIUS)
        text = font.render(self.label, True, config.TEXT_COLOR)
        surface.blit(text, text.get_rect(center=self.rect.center))


class Slider:
    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        minimum: float,
        maximum: float,
        value: float,
        action: str,
        integer: bool = False,
    ) -> None:
        self.rect = rect
        self.label = label
        self.minimum = minimum
        self.maximum = maximum
        self.value = value
        self.action = action
        self.integer = integer
        self.dragging = False

    def set_value_from_pos(self, x: int) -> float:
        ratio = (x - self.rect.left) / max(1, self.rect.width)
        value = self.minimum + max(0.0, min(1.0, ratio)) * (self.maximum - self.minimum)
        self.value = round(value) if self.integer else round(value, 2)
        return self.value

    def knob_x(self) -> int:
        ratio = (self.value - self.minimum) / max(1e-9, self.maximum - self.minimum)
        return int(self.rect.left + max(0.0, min(1.0, ratio)) * self.rect.width)

    def draw(self, surface: pygame.Surface, small_font: pygame.font.Font) -> None:
        value_text = f"{int(self.value)}" if self.integer else f"{self.value:.2f}"
        label = small_font.render(f"{self.label}: {value_text}", True, config.TEXT_COLOR)
        label_rect = pygame.Rect(self.rect.left - 2, self.rect.top - 25, max(110, label.get_width() + 12), 19)
        label_surface = pygame.Surface(label_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(label_surface, (6, 10, 16, 155), label_surface.get_rect(), border_radius=4)
        surface.blit(label_surface, label_rect.topleft)
        surface.blit(label, (label_rect.left + 6, label_rect.top + 1))
        track_y = self.rect.centery
        pygame.draw.line(surface, config.UI_BORDER_COLOR, (self.rect.left, track_y), (self.rect.right, track_y), 5)
        pygame.draw.line(surface, config.UI_ACCENT_COLOR, (self.rect.left, track_y), (self.knob_x(), track_y), 5)
        pygame.draw.circle(surface, config.TEXT_COLOR, (self.knob_x(), track_y), 9)
        pygame.draw.circle(surface, config.UI_ACCENT_COLOR, (self.knob_x(), track_y), 9, 1)


class ControlPanel:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.font = pygame.font.SysFont("segoeui", 13)
        self.small_font = pygame.font.SysFont("segoeui", 12)
        self.buttons: list[Button] = []
        self.sliders: list[Slider] = []
        self._build()

    def resize(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self._build()

    def _build(self) -> None:
        panel_top = self.height - config.UI_PANEL_HEIGHT
        x = config.UI_MARGIN
        y = panel_top + 34
        button_h = 28
        button_gap = 6
        preset_w = max(100, min(112, (self.width - config.UI_MARGIN * 2 - button_gap * 4) // 5))
        self.buttons = []
        preset_labels = ["Calm", "Butterfly", "Drone", "Henon", "Bifurcation"]
        for index, _preset in enumerate(PRESETS):
            self.buttons.append(Button(pygame.Rect(x, y, preset_w, button_h), f"{index + 1} {preset_labels[index]}", f"preset:{index}"))
            x += preset_w + button_gap

        y2 = y + button_h + 10
        x2 = config.UI_MARGIN
        for label, action, width in [
            ("Pause", "pause", 72),
            ("Reset", "reset", 72),
            ("Mute", "mute", 68),
            ("MIDI", "save_midi", 70),
            ("Bifurc.", "bifurcation", 84),
            ("Chaos", "chaos", 72),
            ("Scale", "scale", 106),
            ("AutoCam", "auto_camera", 84),
            ("Full", "fullscreen", 62),
            ("Exit", "exit", 62),
        ]:
            self.buttons.append(Button(pygame.Rect(x2, y2, width, button_h), label, action))
            x2 += width + button_gap

        left_x = config.UI_MARGIN
        right_x = max(500, self.width // 2 + 36)
        slider_w = max(360, min(520, (self.width // 2) - 72))
        right_w = max(300, self.width - right_x - config.UI_MARGIN)
        y3 = y2 + button_h + 42
        row_gap = 42
        self.sliders = [
            Slider(
                pygame.Rect(left_x, y3, slider_w, 22),
                "Speed",
                config.MIN_STEPS_PER_FRAME,
                config.MAX_STEPS_PER_FRAME,
                config.DEFAULT_STEPS_PER_FRAME,
                "speed",
                integer=True,
            ),
            Slider(
                pygame.Rect(left_x, y3 + row_gap, slider_w, 22),
                "Density",
                config.MIN_DENSITY_MULTIPLIER,
                config.MAX_DENSITY_MULTIPLIER,
                1.0,
                "density",
            ),
            Slider(
                pygame.Rect(left_x, y3 + row_gap * 2, slider_w, 22),
                "Root",
                config.MIN_ROOT_NOTE,
                config.MAX_ROOT_NOTE,
                config.DEFAULT_ROOT_NOTE,
                "root_note",
                integer=True,
            ),
            Slider(
                pygame.Rect(right_x, y3, right_w, 22),
                "Chaos influence",
                config.MIN_CHAOS_INFLUENCE,
                config.MAX_CHAOS_INFLUENCE,
                1.0,
                "chaos_influence",
            ),
            Slider(
                pygame.Rect(right_x, y3 + row_gap, right_w, 22),
                "Trail",
                config.MIN_TRAIL_LIMIT,
                config.MAX_TRAIL_LIMIT,
                config.TRAIL_LIMIT,
                "trail_limit",
                integer=True,
            ),
            Slider(
                pygame.Rect(right_x, y3 + row_gap * 2, max(120, right_w // 3 - 16), 22),
                "Zoom",
                config.MIN_CAMERA_ZOOM,
                config.MAX_CAMERA_ZOOM,
                9.6,
                "camera_zoom",
            ),
            Slider(
                pygame.Rect(right_x + right_w // 3 + 8, y3 + row_gap * 2, max(120, right_w // 3 - 16), 22),
                "Rot X",
                config.MIN_CAMERA_ROTATION,
                config.MAX_CAMERA_ROTATION,
                0.65,
                "camera_rotation_x",
            ),
            Slider(
                pygame.Rect(right_x + (right_w // 3) * 2 + 16, y3 + row_gap * 2, max(120, right_w // 3 - 16), 22),
                "Rot Y",
                config.MIN_CAMERA_ROTATION,
                config.MAX_CAMERA_ROTATION,
                -0.55,
                "camera_rotation_y",
            ),
        ]

    def sync(self, state: UIState) -> None:
        for button in self.buttons:
            if button.action.startswith("preset:"):
                button.active = int(button.action.split(":", maxsplit=1)[1]) == state.preset_index
            elif button.action == "pause":
                button.label = "Resume" if state.paused else "Pause"
                button.active = state.paused
            elif button.action == "mute":
                button.label = "Unmute" if state.muted else "Mute"
                button.active = state.muted
            elif button.action == "chaos":
                button.active = state.chaos_mode
            elif button.action == "scale":
                button.label = f"Scale: {self._short_scale(state.scale_name)}"
            elif button.action == "auto_camera":
                button.active = state.auto_camera

        for slider in self.sliders:
            if slider.action == "speed":
                slider.value = state.steps_per_frame
            elif slider.action == "density":
                slider.value = state.density_multiplier
            elif slider.action == "root_note":
                slider.value = state.root_note
            elif slider.action == "chaos_influence":
                slider.value = state.chaos_influence
            elif slider.action == "trail_limit":
                slider.value = state.trail_limit
            elif slider.action == "camera_zoom":
                slider.value = state.camera_zoom
            elif slider.action == "camera_rotation_x":
                slider.value = state.camera_rotation_x
            elif slider.action == "camera_rotation_y":
                slider.value = state.camera_rotation_y

    def draw(self, surface: pygame.Surface, state: UIState) -> None:
        self.sync(state)
        panel_rect = pygame.Rect(0, self.height - config.UI_PANEL_HEIGHT, self.width, config.UI_PANEL_HEIGHT)
        panel_surface = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        panel_surface.fill((*config.UI_BACKGROUND_COLOR, config.UI_BACKGROUND_ALPHA))
        surface.blit(panel_surface, panel_rect.topleft)
        pygame.draw.line(surface, config.UI_BORDER_COLOR, panel_rect.topleft, panel_rect.topright, 1)
        title = self.small_font.render("Controls: drag scene to rotate camera, mouse wheel to zoom", True, config.MUTED_TEXT_COLOR)
        surface.blit(title, (config.UI_MARGIN, panel_rect.top + 14))
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.draw(surface, self.font, mouse_pos)
        for slider in self.sliders:
            slider.draw(surface, self.small_font)

    def handle_event(self, event: pygame.event.Event) -> tuple[str, float | None] | None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.rect.collidepoint(event.pos):
                    return button.action, None
            for slider in self.sliders:
                if slider.rect.inflate(0, 20).collidepoint(event.pos):
                    slider.dragging = True
                    return slider.action, slider.set_value_from_pos(event.pos[0])

        if event.type == pygame.MOUSEMOTION:
            for slider in self.sliders:
                if slider.dragging:
                    return slider.action, slider.set_value_from_pos(event.pos[0])

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for slider in self.sliders:
                slider.dragging = False

        return None

    def _short_scale(self, scale_name: str) -> str:
        names = {
            "minor_pentatonic": "min pent",
            "natural_minor": "nat min",
            "harmonic_minor": "harm min",
            "whole_tone": "whole",
            "chromatic": "chrom",
        }
        return names.get(scale_name, scale_name)
