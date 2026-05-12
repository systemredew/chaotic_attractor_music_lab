from __future__ import annotations

import argparse
import ctypes
from pathlib import Path

import numpy as np
import pygame

import config
from math_core.bifurcation import save_logistic_bifurcation
from math_core.integrators import rk4_step
from math_core.lyapunov import LyapunovEstimator
from math_core.vector_utils import acceleration, curvature, speed
from music.mapper import MusicMapper
from music.music_engine import MusicEngine
from presets.presets import PRESETS, Preset
from systems import HalvorsenSystem, HenonMap, LogisticMap, LorenzSystem, RosslerSystem
from systems.base_system import BaseSystem
from visual.renderer import Renderer


def configure_windows_app_identity() -> None:
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(config.APP_ID)
    except (AttributeError, OSError):
        pass


def create_system(preset: Preset) -> BaseSystem:
    if preset.system == "Lorenz":
        return LorenzSystem(**preset.parameters)
    if preset.system == "Rossler":
        return RosslerSystem(**preset.parameters)
    if preset.system == "Halvorsen":
        return HalvorsenSystem(**preset.parameters)
    if preset.system == "Henon":
        return HenonMap(**preset.parameters)
    if preset.system == "Logistic":
        return LogisticMap(**preset.parameters)
    raise ValueError(f"Unknown system: {preset.system}")


class ChaoticAttractorMusicLab:
    def __init__(self, preset_index: int = 1) -> None:
        configure_windows_app_identity()
        pygame.init()
        self.clock = pygame.time.Clock()
        self.renderer = Renderer()
        self.music = MusicEngine()
        self.preset_index = preset_index
        self.preset = PRESETS[preset_index]
        self.system = create_system(self.preset)
        self.mapper = MusicMapper(scale_name=self.preset.scale)
        self.lyapunov = LyapunovEstimator(self.system)
        self.paused = False
        self.running = True
        self.steps_per_frame = config.DEFAULT_STEPS_PER_FRAME
        self.density_multiplier = self.preset.note_density
        self.chaos_mode = True
        self.chaos_influence = 1.0
        self.auto_camera = False
        self.performance_mode = False
        self.previous_point = None
        self.previous_speed = 0.0
        self.points_for_curvature = []
        self.simulation_credit = 0.0

    def load_preset(self, index: int) -> None:
        self.preset_index = index
        self.preset = PRESETS[index]
        self.system = create_system(self.preset)
        self.mapper.scale_name = self.preset.scale
        self.density_multiplier = self.preset.note_density
        self.lyapunov = LyapunovEstimator(self.system)
        self.renderer.reset_trail()
        self.previous_point = None
        self.previous_speed = 0.0
        self.points_for_curvature = []
        self.simulation_credit = 0.0

    def reset(self) -> None:
        self.system.reset()
        self.lyapunov = LyapunovEstimator(self.system)
        self.renderer.reset_trail()
        self.previous_point = None
        self.previous_speed = 0.0
        self.points_for_curvature = []
        self.simulation_credit = 0.0

    def reset_defaults(self) -> None:
        self.preset = PRESETS[self.preset_index]
        self.system = create_system(self.preset)
        self.mapper.scale_name = self.preset.scale
        self.mapper.root_note = config.DEFAULT_ROOT_NOTE
        self.mapper.bpm = config.DEFAULT_TEMPO_BPM
        self.mapper.note_length_multiplier = 1.0
        self.mapper.octave_range = 4
        self.mapper.note_probability = 1.0
        self.mapper.swing = 0.0
        self.mapper.fuzz_amount = 0.0
        self.mapper.multi_voice = True
        self.music.tempo_bpm = config.DEFAULT_TEMPO_BPM
        self.steps_per_frame = config.DEFAULT_STEPS_PER_FRAME
        self.density_multiplier = self.preset.note_density
        self.chaos_mode = True
        self.chaos_influence = 1.0
        self.auto_camera = False
        self.performance_mode = False
        self.renderer.performance_mode = False
        self.renderer.visual_style = config.VISUAL_STYLES[0]
        self.renderer.pulse_style = config.PULSE_STYLES[0]
        self.renderer.trail_decay_mode = config.TRAIL_DECAY_MODES[0]
        self.renderer.depth_fade = 1.0
        self.renderer.line_thickness = 1
        self.renderer.camera.rotation_x = 0.65
        self.renderer.camera.rotation_y = -0.55
        self.renderer.camera.zoom = 9.6
        self.renderer.camera.offset_x = 0.0
        self.renderer.camera.offset_y = 0.0
        self.renderer.set_trail_limit(config.TRAIL_LIMIT)
        self.lyapunov = LyapunovEstimator(self.system)
        self.renderer.reset_trail()
        self.previous_point = None
        self.previous_speed = 0.0
        self.points_for_curvature = []
        self.simulation_credit = 0.0

    def run(self) -> None:
        while self.running:
            self._handle_events()
            if not self.paused:
                self._simulate()
            self.renderer.render(
                system_name=self.system.name,
                lyapunov=self.lyapunov.current(),
                scale_name=self.mapper.scale_name,
                preset_name=self.preset.name,
                current_note=self.music.current_note,
                fps=self.clock.get_fps(),
                paused=self.paused,
                muted=self.music.muted,
                params=self.system.parameter_text(),
                chaos_mode=self.chaos_mode,
                steps_per_frame=self.steps_per_frame,
                density_multiplier=self.density_multiplier,
                preset_index=self.preset_index,
                root_note=self.mapper.root_note,
                chaos_influence=self.chaos_influence,
                trail_limit=self.renderer.trail_limit,
                auto_camera=self.auto_camera,
                performance_mode=self.performance_mode,
                pulse_style=self.renderer.pulse_style,
                trail_decay_mode=self.renderer.trail_decay_mode,
                depth_fade=self.renderer.depth_fade,
                line_thickness=self.renderer.line_thickness,
                bpm=self.mapper.bpm,
                note_length_multiplier=self.mapper.note_length_multiplier,
                octave_range=self.mapper.octave_range,
                note_probability=self.mapper.note_probability,
                swing=self.mapper.swing,
                fuzz_amount=self.mapper.fuzz_amount,
                multi_voice=self.mapper.multi_voice,
                parameter_values=self._control_parameters(),
            )
            self.clock.tick(config.FPS)
        pygame.quit()

    def _simulate(self) -> None:
        self.simulation_credit += (self.steps_per_frame * self.preset.speed_multiplier) / config.SIMULATION_SPEED_DIVISOR
        steps_to_run = int(self.simulation_credit)
        self.simulation_credit -= steps_to_run
        for _ in range(steps_to_run):
            with np.errstate(over="ignore", invalid="ignore"):
                if self.system.is_discrete:
                    point = self.system.update()
                else:
                    self.system.set_state(rk4_step(self.system, self.system.current_point(), config.DEFAULT_DT))
                    point = self.system.current_point()
            if not self._valid_point(point):
                self._recover_invalid_state()
                break

            lyapunov_raw = self.lyapunov.step() if self.chaos_mode else 0.0
            lyapunov_value = lyapunov_raw * self.chaos_influence
            if not np.isfinite(lyapunov_value):
                lyapunov_value = 0.0
            current_speed = speed(self.previous_point, point, config.DEFAULT_DT)
            current_acceleration = acceleration(self.previous_speed, current_speed, config.DEFAULT_DT)
            self.points_for_curvature.append(point.copy())
            self.points_for_curvature = self.points_for_curvature[-3:]
            current_curvature = 0.0
            if len(self.points_for_curvature) == 3:
                current_curvature = curvature(*self.points_for_curvature)

            events = self.mapper.state_to_events(
                point,
                self.system.name,
                lyapunov_value,
                speed=current_speed,
                acceleration=current_acceleration,
                curvature=current_curvature,
            )
            if self.music.play_events(events, self.density_multiplier):
                self.renderer.trigger_note_pulse()
            self.renderer.append_point(point, current_speed, lyapunov_value)
            self.previous_point = point.copy()
            self.previous_speed = current_speed

    def _valid_point(self, point: object) -> bool:
        values = np.asarray(point, dtype=np.float64)
        return bool(values.size > 0 and np.all(np.isfinite(values)) and np.linalg.norm(values) < 1e6)

    def _recover_invalid_state(self) -> None:
        self.system = create_system(self.preset)
        self.lyapunov = LyapunovEstimator(self.system)
        self.renderer.reset_trail()
        self.previous_point = None
        self.previous_speed = 0.0
        self.points_for_curvature = []
        self.simulation_credit = 0.0

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.renderer.resize(event.w, event.h)
            elif event.type in {pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION, pygame.MOUSEWHEEL}:
                action = self.renderer.handle_ui_event(event)
                if action is not None:
                    self._handle_ui_action(*action)
            elif event.type == pygame.KEYDOWN:
                self._handle_key(event.key)
            elif event.type == pygame.USEREVENT + 1:
                self.music.note_off()

    def _handle_ui_action(self, action: str, value: float | None = None) -> None:
        if action.startswith("preset:"):
            self.load_preset(int(action.split(":", maxsplit=1)[1]))
        elif action == "pause":
            self.paused = not self.paused
        elif action == "reset":
            self.reset()
        elif action == "defaults":
            self.reset_defaults()
        elif action == "save_midi":
            output = Path(config.EXPORT_DIR) / config.DEFAULT_MIDI_FILE
            self.music.export_midi(output)
        elif action == "screenshot":
            output = Path(config.EXPORT_DIR) / config.DEFAULT_SCREENSHOT_FILE
            self.renderer.save_screenshot(output)
        elif action == "bifurcation":
            save_logistic_bifurcation(Path(config.EXPORT_DIR) / config.BIFURCATION_IMAGE)
        elif action == "chaos":
            self.chaos_mode = not self.chaos_mode
        elif action.startswith("scale:"):
            self.mapper.scale_name = action.split(":", maxsplit=1)[1]
        elif action == "auto_camera":
            self.auto_camera = not self.auto_camera
        elif action.startswith("visual_style:"):
            self.renderer.visual_style = action.split(":", maxsplit=1)[1]
        elif action.startswith("pulse_style:"):
            self.renderer.pulse_style = action.split(":", maxsplit=1)[1]
        elif action.startswith("trail_decay:"):
            self.renderer.trail_decay_mode = action.split(":", maxsplit=1)[1]
        elif action == "multi_voice":
            self.mapper.multi_voice = not self.mapper.multi_voice
        elif action == "toggle_panel":
            self._toggle_panel()
        elif action == "speed" and value is not None:
            self.steps_per_frame = int(value)
        elif action == "density" and value is not None:
            self.density_multiplier = float(value)
        elif action == "root_note" and value is not None:
            self.mapper.root_note = int(value)
        elif action == "chaos_influence" and value is not None:
            self.chaos_influence = float(value)
        elif action == "trail_limit" and value is not None:
            self.renderer.set_trail_limit(int(value))
        elif action == "depth_fade" and value is not None:
            self.renderer.depth_fade = float(value)
        elif action == "line_thickness" and value is not None:
            self.renderer.line_thickness = int(value)
        elif action == "bpm" and value is not None:
            self.mapper.bpm = int(value)
            self.music.tempo_bpm = int(value)
        elif action == "note_length" and value is not None:
            self.mapper.note_length_multiplier = float(value)
        elif action == "octave_range" and value is not None:
            self.mapper.octave_range = int(value)
        elif action == "note_probability" and value is not None:
            self.mapper.note_probability = float(value)
        elif action == "swing" and value is not None:
            self.mapper.swing = float(value)
        elif action == "fuzz" and value is not None:
            self.mapper.fuzz_amount = float(value)
        elif action.startswith("parameter:") and value is not None:
            self._set_parameter_by_index(int(action.split(":", maxsplit=1)[1]), float(value))

    def _handle_key(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_SPACE:
            self.paused = not self.paused
        elif key == pygame.K_r:
            self.reset()
        elif pygame.K_1 <= key <= min(pygame.K_9, pygame.K_1 + len(PRESETS) - 1):
            self.load_preset(key - pygame.K_1)
        elif key == pygame.K_m:
            self.music.toggle_mute()
        elif key == pygame.K_s:
            output = Path(config.EXPORT_DIR) / config.DEFAULT_MIDI_FILE
            self.music.export_midi(output)
        elif key == pygame.K_b:
            save_logistic_bifurcation(Path(config.EXPORT_DIR) / config.BIFURCATION_IMAGE)
        elif key == pygame.K_UP:
            self.steps_per_frame = min(config.MAX_STEPS_PER_FRAME, self.steps_per_frame + 1)
        elif key == pygame.K_DOWN:
            self.steps_per_frame = max(config.MIN_STEPS_PER_FRAME, self.steps_per_frame - 1)
        elif key == pygame.K_RIGHT:
            self.density_multiplier = min(config.MAX_DENSITY_MULTIPLIER, self.density_multiplier + 0.1)
        elif key == pygame.K_LEFT:
            self.density_multiplier = max(config.MIN_DENSITY_MULTIPLIER, self.density_multiplier - 0.1)
        elif key == pygame.K_c:
            self.chaos_mode = not self.chaos_mode
        elif key == pygame.K_F11 or (key == pygame.K_RETURN and pygame.key.get_mods() & pygame.KMOD_ALT):
            self.renderer.toggle_fullscreen()
        elif key == pygame.K_TAB:
            self._toggle_panel()
        elif key == pygame.K_F12:
            self.renderer.save_screenshot(Path(config.EXPORT_DIR) / config.DEFAULT_SCREENSHOT_FILE)

    def _control_parameters(self) -> dict[str, float]:
        values = dict(self.system.parameters)
        if hasattr(self.system, "r_step"):
            values["r_step"] = float(self.system.r_step)  # type: ignore[attr-defined]
        return values

    def _set_parameter_by_index(self, index: int, value: float) -> None:
        names = list(self._control_parameters())
        if index >= len(names):
            return
        name = names[index]
        setattr(self.system, name, value)
        if name in self.system.parameters:
            self.system.parameters[name] = value
        if self.system.name == "Logistic" and name == "r":
            self.system.parameters["r"] = value

    def _toggle_panel(self) -> None:
        self.performance_mode = not self.performance_mode
        self.renderer.performance_mode = self.performance_mode


def smoke_test() -> None:
    for preset in PRESETS:
        system = create_system(preset)
        mapper = MusicMapper(scale_name=preset.scale)
        point = system.update() if system.is_discrete else rk4_step(system, system.current_point(), config.DEFAULT_DT)
        note = mapper.state_to_note(point, system.name, 0.1)
        assert 0 <= note.note <= 127
    print("Smoke test passed: systems, RK4, and music mapping are operational.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Chaotic Attractor Music Lab")
    parser.add_argument("--smoke", action="store_true", help="Run a non-interactive startup check")
    args = parser.parse_args()
    if args.smoke:
        smoke_test()
        return
    ChaoticAttractorMusicLab().run()


if __name__ == "__main__":
    main()
