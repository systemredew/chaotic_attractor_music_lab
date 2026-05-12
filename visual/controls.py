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
        center = self.rect.center
        radius = 8
        pygame.draw.circle(surface, config.TEXT_COLOR, center, radius, 2)
        pygame.draw.circle(surface, config.UI_PANEL_COLOR, (center[0] + 5, center[1] - 7), 5)
        arrow = [(center[0] + 8, center[1] - 10), (center[0] + 13, center[1] - 4), (center[0] + 5, center[1] - 3)]
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
        edge = config.UI_EDGE_MARGIN
        panel_top = self.height - config.UI_PANEL_HEIGHT + edge
        inset = edge + config.UI_PANEL_INSET
        x = inset
        y = panel_top + 40
        button_h = 28
        button_gap = 6
        preset_w = max(82, min(104, (self.width // 2 - inset * 2 - button_gap * 4) // 5))
        self.buttons = []
        preset_labels = ["Calm", "Butterfly", "Drone", "Henon", "Bifurcation"]
        for index, _preset in enumerate(PRESETS):
            self.buttons.append(Button(pygame.Rect(x, y, preset_w, button_h), f"{index + 1} {preset_labels[index]}", f"preset:{index}"))
            x += preset_w + button_gap

        attractor_end = x - button_gap
        x2 = attractor_end + 34
        y2 = y
        transport_start = x2
        max_controls_right = self.width - edge - inset
        for label, action, width in [
            ("", "pause", 46),
            ("", "reset", 46),
            ("Default", "defaults", 72),
            ("Rec", "save_midi", 62),
            ("Bifurc.", "bifurcation", 74),
            ("Chaos", "chaos", 66),
            ("Scale", "scale", 88),
            ("Auto Cam", "auto_camera", 86),
            ("Style", "visual_style", 66),
            ("Voice", "multi_voice", 62),
            ("Perf", "performance", 58),
        ]:
            if x2 + width > max_controls_right:
                x2 = transport_start
                y2 += button_h + 8
            self.buttons.append(Button(pygame.Rect(x2, y2, width, button_h), label, action))
            x2 += width + button_gap
        transport_end = x2 - button_gap

        left_x = inset
        middle_x = max(390, self.width // 3 + 24)
        right_x = max(720, (self.width // 3) * 2 + 24)
        column_w = max(280, min(360, (self.width - inset * 2 - edge * 2 - 60) // 3))
        right_w = max(260, self.width - right_x - inset - edge)
        section_top = panel_top + 124
        section_height = self.height - edge - section_top - 16
        self.section_rects = [
            pygame.Rect(left_x - 8, section_top, column_w + 16, section_height),
            pygame.Rect(middle_x - 8, section_top, column_w + 16, section_height),
            pygame.Rect(right_x - 8, section_top, right_w + 16, section_height),
        ]
        self.section_titles = ["SYSTEM", "MUSIC", "VISUAL"]
        self.top_section_rects = [
            pygame.Rect(inset - 8, y - 18, attractor_end - inset + 16, button_h + 32),
            pygame.Rect(transport_start - 8, y - 18, max(160, transport_end - transport_start + 16), (y2 - y) + button_h + 32),
        ]
        self.top_section_titles = ["ATTRACTOR", "CONTROLS"]
        y3 = section_top + 48
        row_gap = 30
        self.sliders = [
            Slider(pygame.Rect(left_x, y3, column_w, 22), "Param", 0.0, 1.0, 0.0, "parameter:0"),
            Slider(pygame.Rect(left_x, y3 + row_gap, column_w, 22), "Param", 0.0, 1.0, 0.0, "parameter:1"),
            Slider(pygame.Rect(left_x, y3 + row_gap * 2, column_w, 22), "Param", 0.0, 1.0, 0.0, "parameter:2"),
            Slider(pygame.Rect(middle_x, y3, column_w, 22), "Tone", config.MIN_ROOT_NOTE, config.MAX_ROOT_NOTE, config.DEFAULT_ROOT_NOTE, "root_note", True),
            Slider(pygame.Rect(middle_x, y3 + row_gap, column_w, 22), "Density", config.MIN_DENSITY_MULTIPLIER, config.MAX_DENSITY_MULTIPLIER, 1.0, "density"),
            Slider(pygame.Rect(middle_x, y3 + row_gap * 2, column_w, 22), "BPM", config.MIN_BPM, config.MAX_BPM, config.DEFAULT_TEMPO_BPM, "bpm", True),
            Slider(pygame.Rect(middle_x, y3 + row_gap * 3, column_w, 22), "Length", config.MIN_NOTE_LENGTH_MULTIPLIER, config.MAX_NOTE_LENGTH_MULTIPLIER, 1.0, "note_length"),
            Slider(pygame.Rect(middle_x, y3 + row_gap * 4, column_w, 22), "Octaves", config.MIN_OCTAVE_RANGE, config.MAX_OCTAVE_RANGE, 4, "octave_range", True),
            Slider(pygame.Rect(middle_x, y3 + row_gap * 5, column_w, 22), "Probability", config.MIN_NOTE_PROBABILITY, config.MAX_NOTE_PROBABILITY, 1.0, "note_probability"),
            Slider(pygame.Rect(middle_x, y3 + row_gap * 6, column_w, 22), "Swing", config.MIN_SWING, config.MAX_SWING, 0.0, "swing"),
            Slider(pygame.Rect(right_x, y3, right_w, 22), "Speed", config.MIN_STEPS_PER_FRAME, config.MAX_STEPS_PER_FRAME, config.DEFAULT_STEPS_PER_FRAME, "speed", True),
            Slider(pygame.Rect(right_x, y3 + row_gap, right_w, 22), "Trail", config.MIN_TRAIL_LIMIT, config.MAX_TRAIL_LIMIT, config.TRAIL_LIMIT, "trail_limit", True),
            Slider(pygame.Rect(right_x, y3 + row_gap * 2, right_w, 22), "Chaos influence", config.MIN_CHAOS_INFLUENCE, config.MAX_CHAOS_INFLUENCE, 1.0, "chaos_influence"),
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
        edge = config.UI_EDGE_MARGIN
        panel_rect = pygame.Rect(edge, self.height - config.UI_PANEL_HEIGHT + edge, self.width - edge * 2, config.UI_PANEL_HEIGHT - edge * 2)
        panel_surface = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        panel_surface.fill((*config.UI_BACKGROUND_COLOR, config.UI_BACKGROUND_ALPHA))
        surface.blit(panel_surface, panel_rect.topleft)
        pygame.draw.rect(surface, config.UI_BORDER_COLOR, panel_rect, 1, border_radius=config.UI_RADIUS)
        self._draw_sections(surface)
        self._draw_top_sections(surface)
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.draw(surface, self.font, mouse_pos)
        for slider in self.sliders:
            slider.draw(surface, self.small_font)
        self._draw_tooltip(surface, mouse_pos)

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

    def _draw_sections(self, surface: pygame.Surface) -> None:
        for rect, title in zip(self.section_rects, self.section_titles):
            section_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(section_surface, (5, 9, 14, 78), section_surface.get_rect(), border_radius=config.UI_RADIUS)
            surface.blit(section_surface, rect.topleft)
            pygame.draw.rect(surface, config.UI_BORDER_COLOR, rect, 1, border_radius=config.UI_RADIUS)
            text = self.small_font.render(title, True, config.UI_ACCENT_COLOR)
            label_rect = pygame.Rect(rect.left + 10, rect.top - 10, text.get_width() + 14, 20)
            label_surface = pygame.Surface(label_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(label_surface, (*config.UI_BACKGROUND_COLOR, 215), label_surface.get_rect(), border_radius=5)
            surface.blit(label_surface, label_rect.topleft)
            surface.blit(text, (label_rect.left + 7, label_rect.top + 2))

    def _draw_top_sections(self, surface: pygame.Surface) -> None:
        for rect, title in zip(self.top_section_rects, self.top_section_titles):
            pygame.draw.rect(surface, config.UI_BORDER_COLOR, rect, 1, border_radius=config.UI_RADIUS)
            text = self.small_font.render(title, True, config.UI_ACCENT_COLOR)
            label_rect = pygame.Rect(rect.left + 10, rect.top - 10, text.get_width() + 14, 20)
            label_surface = pygame.Surface(label_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(label_surface, (*config.UI_BACKGROUND_COLOR, 215), label_surface.get_rect(), border_radius=5)
            surface.blit(label_surface, label_rect.topleft)
            surface.blit(text, (label_rect.left + 7, label_rect.top + 2))

    def _draw_tooltip(self, surface: pygame.Surface, mouse_pos: tuple[int, int]) -> None:
        text = self._tooltip_text(mouse_pos)
        if not text:
            return
        rendered = self.small_font.render(text, True, config.TEXT_COLOR)
        padding = 8
        rect = pygame.Rect(mouse_pos[0] + 14, mouse_pos[1] - 34, rendered.get_width() + padding * 2, 26)
        if rect.right > self.width - config.UI_EDGE_MARGIN:
            rect.right = self.width - config.UI_EDGE_MARGIN
        if rect.left < config.UI_EDGE_MARGIN:
            rect.left = config.UI_EDGE_MARGIN
        tooltip_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(tooltip_surface, (5, 8, 14, 232), tooltip_surface.get_rect(), border_radius=5)
        surface.blit(tooltip_surface, rect.topleft)
        pygame.draw.rect(surface, config.UI_ACCENT_COLOR, rect, 1, border_radius=5)
        surface.blit(rendered, (rect.left + padding, rect.top + 5))

    def _tooltip_text(self, mouse_pos: tuple[int, int]) -> str | None:
        for button in self.buttons:
            if button.rect.collidepoint(mouse_pos):
                return self._button_tooltips().get(button.action)
        for slider in self.sliders:
            if slider.rect.inflate(0, 24).collidepoint(mouse_pos):
                if slider.action.startswith("parameter:"):
                    return self._parameter_tooltip(slider.label)
                return self._slider_tooltips().get(slider.action)
        return None

    def _button_tooltips(self) -> dict[str, str]:
        return {
            "pause": "Pause or resume simulation",
            "reset": "Restart current trajectory",
            "defaults": "Restore current preset defaults",
            "save_midi": "Record/export generated notes to MIDI",
            "bifurcation": "Save Logistic bifurcation diagram",
            "chaos": "Toggle Lyapunov chaos influence",
            "scale": "Cycle musical scale",
            "auto_camera": "Rotate camera automatically",
            "visual_style": "Cycle color palette",
            "multi_voice": "Toggle extra musical voices",
            "performance": "Hide GUI for performance view",
        }

    def _slider_tooltips(self) -> dict[str, str]:
        return {
            "root_note": "Tone center: shifts all notes up/down",
            "density": "How often note events are allowed",
            "bpm": "Tempo: affects note spacing and durations",
            "note_length": "Multiplier for note duration",
            "octave_range": "Pitch range in octaves",
            "note_probability": "Chance that a generated note is played",
            "swing": "Offsets/lengthens every second note",
            "speed": "Simulation steps per frame",
            "trail_limit": "Number of trajectory points on screen",
            "chaos_influence": "How strongly chaos affects music density",
        }

    def _parameter_tooltip(self, label: str) -> str | None:
        return {
            "sigma": "Lorenz: x-y coupling speed",
            "rho": "Lorenz: convection/chaos intensity",
            "beta": "Lorenz: vertical damping",
            "a": "System coefficient shaping the attractor",
            "b": "System coefficient shaping feedback",
            "c": "Rossler: spiral height/chaos control",
            "r": "Logistic: growth parameter",
            "r_step": "Logistic: how fast r advances",
        }.get(label)

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
