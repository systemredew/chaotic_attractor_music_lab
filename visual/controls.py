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
        pygame.draw.rect(surface, fill, self.rect, border_radius=config.UI_RADIUS)
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

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, small_font: pygame.font.Font) -> None:
        value_text = f"{int(self.value)}" if self.integer else f"{self.value:.2f}"
        label = small_font.render(f"{self.label}: {value_text}", True, config.TEXT_COLOR)
        surface.blit(label, (self.rect.left, self.rect.top - 22))
        track_y = self.rect.centery
        pygame.draw.line(surface, config.UI_BORDER_COLOR, (self.rect.left, track_y), (self.rect.right, track_y), 4)
        pygame.draw.line(surface, config.UI_ACCENT_COLOR, (self.rect.left, track_y), (self.knob_x(), track_y), 4)
        pygame.draw.circle(surface, config.TEXT_COLOR, (self.knob_x(), track_y), 8)


class ControlPanel:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.font = pygame.font.SysFont("segoeui", 14)
        self.small_font = pygame.font.SysFont("segoeui", 13)
        self.buttons: list[Button] = []
        self.sliders: list[Slider] = []
        self._build()

    def _build(self) -> None:
        panel_top = self.height - config.UI_PANEL_HEIGHT
        x = config.UI_MARGIN
        y = panel_top + 42
        button_h = 30
        button_gap = 7
        preset_w = 126
        self.buttons = []
        preset_labels = ["Calm", "Butterfly", "Drone", "Henon", "Bifurcation"]
        for index, _preset in enumerate(PRESETS):
            self.buttons.append(Button(pygame.Rect(x, y, preset_w, button_h), f"{index + 1} {preset_labels[index]}", f"preset:{index}"))
            x += preset_w + button_gap

        y2 = y + button_h + 12
        x2 = config.UI_MARGIN
        for label, action, width in [
            ("Pause", "pause", 78),
            ("Reset", "reset", 78),
            ("Mute", "mute", 72),
            ("MIDI", "save_midi", 78),
            ("Bifurc.", "bifurcation", 92),
            ("Chaos", "chaos", 76),
            ("Exit", "exit", 66),
        ]:
            self.buttons.append(Button(pygame.Rect(x2, y2, width, button_h), label, action))
            x2 += width + button_gap

        slider_x = 720
        self.sliders = [
            Slider(
                pygame.Rect(slider_x, y + 18, 430, 24),
                "Speed",
                config.MIN_STEPS_PER_FRAME,
                config.MAX_STEPS_PER_FRAME,
                config.DEFAULT_STEPS_PER_FRAME,
                "speed",
                integer=True,
            ),
            Slider(
                pygame.Rect(slider_x, y2 + 18, 430, 24),
                "Density",
                config.MIN_DENSITY_MULTIPLIER,
                config.MAX_DENSITY_MULTIPLIER,
                1.0,
                "density",
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

        for slider in self.sliders:
            if slider.action == "speed":
                slider.value = state.steps_per_frame
            elif slider.action == "density":
                slider.value = state.density_multiplier

    def draw(self, surface: pygame.Surface, state: UIState) -> None:
        self.sync(state)
        panel_rect = pygame.Rect(0, self.height - config.UI_PANEL_HEIGHT, self.width, config.UI_PANEL_HEIGHT)
        pygame.draw.rect(surface, config.UI_BACKGROUND_COLOR, panel_rect)
        pygame.draw.line(surface, config.UI_BORDER_COLOR, panel_rect.topleft, panel_rect.topright, 1)
        title = self.small_font.render("Controls", True, config.MUTED_TEXT_COLOR)
        surface.blit(title, (config.UI_MARGIN, panel_rect.top + 14))
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.draw(surface, self.font, mouse_pos)
        for slider in self.sliders:
            slider.draw(surface, self.font, self.small_font)

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
