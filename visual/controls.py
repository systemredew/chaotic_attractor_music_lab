from __future__ import annotations

from dataclasses import dataclass

import pygame

import config
from presets.presets import PRESETS


@dataclass
class UIState:
    preset_index: int
    paused: bool
    chaos_mode: bool
    steps_per_frame: int
    density_multiplier: float
    root_note: int
    chaos_influence: float
    trail_limit: int
    scale_name: str
    auto_camera: bool
    performance_mode: bool
    visual_style: str
    bpm: int
    note_length_multiplier: float
    octave_range: int
    note_probability: float
    swing: float
    multi_voice: bool
    system_name: str
    parameter_values: dict[str, float]


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

        if self.action == "pause":
            self._draw_play_icon(surface) if self.active else self._draw_pause_icon(surface)
        elif self.action == "reset":
            self._draw_reset_icon(surface)
        else:
            text = font.render(self.label, True, config.TEXT_COLOR)
            surface.blit(text, text.get_rect(center=self.rect.center))

    def _draw_pause_icon(self, surface: pygame.Surface) -> None:
        bar_w = 4
        bar_h = self.rect.height // 2
        y = self.rect.centery - bar_h // 2
        x = self.rect.centerx - 7
        pygame.draw.rect(surface, config.TEXT_COLOR, pygame.Rect(x, y, bar_w, bar_h), border_radius=2)
        pygame.draw.rect(surface, config.TEXT_COLOR, pygame.Rect(x + 10, y, bar_w, bar_h), border_radius=2)

    def _draw_play_icon(self, surface: pygame.Surface) -> None:
        size = self.rect.height // 3
        x = self.rect.centerx - 4
        points = [(x, self.rect.centery - size), (x, self.rect.centery + size), (x + size + 7, self.rect.centery)]
        pygame.draw.polygon(surface, config.TEXT_COLOR, points)

    def _draw_reset_icon(self, surface: pygame.Surface) -> None:
        radius = self.rect.height // 3
        center = self.rect.center
        arc_rect = pygame.Rect(center[0] - radius, center[1] - radius, radius * 2, radius * 2)
        pygame.draw.arc(surface, config.TEXT_COLOR, arc_rect, 0.25, 5.15, 2)
        arrow = [
            (center[0] + radius - 2, center[1] - 7),
            (center[0] + radius + 6, center[1] - 2),
            (center[0] + radius - 1, center[1] + 4),
        ]
        pygame.draw.polygon(surface, config.TEXT_COLOR, arrow)


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
            ("", "pause", 46),
            ("", "reset", 46),
            ("Default", "defaults", 72),
            ("MIDI", "save_midi", 62),
            ("Shot", "screenshot", 62),
            ("Bifurc.", "bifurcation", 74),
            ("Chaos", "chaos", 66),
            ("Scale", "scale", 88),
            ("Auto", "auto_camera", 62),
            ("Style", "visual_style", 66),
            ("Voice", "multi_voice", 62),
            ("Perf", "performance", 58),
        ]:
            self.buttons.append(Button(pygame.Rect(x2, y2, width, button_h), label, action))
            x2 += width + button_gap

        left_x = config.UI_MARGIN
        middle_x = max(390, self.width // 3 + 20)
        right_x = max(720, (self.width // 3) * 2 + 20)
        column_w = max(280, min(360, (self.width - config.UI_MARGIN * 2 - 52) // 3))
        right_w = max(260, self.width - right_x - config.UI_MARGIN)
        y3 = y2 + button_h + 42
        row_gap = 42
        self.sliders = [
            Slider(pygame.Rect(left_x, y3, column_w, 22), "Speed", config.MIN_STEPS_PER_FRAME, config.MAX_STEPS_PER_FRAME, config.DEFAULT_STEPS_PER_FRAME, "speed", True),
            Slider(pygame.Rect(left_x, y3 + row_gap, column_w, 22), "Density", config.MIN_DENSITY_MULTIPLIER, config.MAX_DENSITY_MULTIPLIER, 1.0, "density"),
            Slider(pygame.Rect(left_x, y3 + row_gap * 2, column_w, 22), "Root", config.MIN_ROOT_NOTE, config.MAX_ROOT_NOTE, config.DEFAULT_ROOT_NOTE, "root_note", True),
            Slider(pygame.Rect(middle_x, y3, column_w, 22), "Chaos influence", config.MIN_CHAOS_INFLUENCE, config.MAX_CHAOS_INFLUENCE, 1.0, "chaos_influence"),
            Slider(pygame.Rect(middle_x, y3 + row_gap, column_w, 22), "Trail", config.MIN_TRAIL_LIMIT, config.MAX_TRAIL_LIMIT, config.TRAIL_LIMIT, "trail_limit", True),
            Slider(pygame.Rect(middle_x, y3 + row_gap * 2, column_w, 22), "BPM", config.MIN_BPM, config.MAX_BPM, config.DEFAULT_TEMPO_BPM, "bpm", True),
            Slider(pygame.Rect(right_x, y3, right_w, 22), "Length", config.MIN_NOTE_LENGTH_MULTIPLIER, config.MAX_NOTE_LENGTH_MULTIPLIER, 1.0, "note_length"),
            Slider(pygame.Rect(right_x, y3 + row_gap, right_w, 22), "Octaves", config.MIN_OCTAVE_RANGE, config.MAX_OCTAVE_RANGE, 4, "octave_range", True),
            Slider(pygame.Rect(right_x, y3 + row_gap * 2, right_w, 22), "Probability", config.MIN_NOTE_PROBABILITY, config.MAX_NOTE_PROBABILITY, 1.0, "note_probability"),
            Slider(pygame.Rect(left_x, y3 + row_gap * 3, column_w, 22), "Swing", config.MIN_SWING, config.MAX_SWING, 0.0, "swing"),
            Slider(pygame.Rect(middle_x, y3 + row_gap * 3, column_w, 22), "Param", 0.0, 1.0, 0.0, "parameter:0"),
            Slider(pygame.Rect(left_x, y3 + row_gap * 4, column_w, 22), "Param", 0.0, 1.0, 0.0, "parameter:1"),
            Slider(pygame.Rect(middle_x, y3 + row_gap * 4, column_w, 22), "Param", 0.0, 1.0, 0.0, "parameter:2"),
        ]

    def sync(self, state: UIState) -> None:
        for button in self.buttons:
            if button.action.startswith("preset:"):
                button.active = int(button.action.split(":", maxsplit=1)[1]) == state.preset_index
            elif button.action == "pause":
                button.active = state.paused
            elif button.action == "chaos":
                button.active = state.chaos_mode
            elif button.action == "scale":
                button.label = f"Scale: {self._short_scale(state.scale_name)}"
            elif button.action == "auto_camera":
                button.active = state.auto_camera
            elif button.action == "performance":
                button.active = state.performance_mode
            elif button.action == "visual_style":
                button.label = f"Style: {state.visual_style}"
            elif button.action == "multi_voice":
                button.active = state.multi_voice

        parameter_items = list(state.parameter_values.items())
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
            elif slider.action == "bpm":
                slider.value = state.bpm
            elif slider.action == "note_length":
                slider.value = state.note_length_multiplier
            elif slider.action == "octave_range":
                slider.value = state.octave_range
            elif slider.action == "note_probability":
                slider.value = state.note_probability
            elif slider.action == "swing":
                slider.value = state.swing
            elif slider.action.startswith("parameter:"):
                index = int(slider.action.split(":", maxsplit=1)[1])
                if index < len(parameter_items):
                    name, value = parameter_items[index]
                    minimum, maximum = config.SYSTEM_PARAMETER_RANGES.get(state.system_name, {}).get(name, (0.0, 1.0))
                    slider.label = name
                    slider.minimum = minimum
                    slider.maximum = maximum
                    slider.value = value
                else:
                    slider.label = "-"
                    slider.minimum = 0.0
                    slider.maximum = 1.0
                    slider.value = 0.0

    def draw(self, surface: pygame.Surface, state: UIState) -> None:
        self.sync(state)
        if state.performance_mode:
            return
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
            "major": "major",
        }
        return names.get(scale_name, scale_name)
