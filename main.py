from __future__ import annotations

import argparse
from pathlib import Path

import pygame

import config
from math_core.bifurcation import save_logistic_bifurcation
from math_core.integrators import rk4_step
from math_core.lyapunov import LyapunovEstimator
from math_core.vector_utils import acceleration, curvature, speed
from music.mapper import MusicMapper
from music.music_engine import MusicEngine
from music.scales import SCALES
from presets.presets import PRESETS, Preset
from systems import HenonMap, LogisticMap, LorenzSystem, RosslerSystem
from systems.base_system import BaseSystem
from visual.renderer import Renderer


def create_system(preset: Preset) -> BaseSystem:
    if preset.system == "Lorenz":
        return LorenzSystem(**preset.parameters)
    if preset.system == "Rossler":
        return RosslerSystem(**preset.parameters)
    if preset.system == "Henon":
        return HenonMap(**preset.parameters)
    if preset.system == "Logistic":
        return LogisticMap(**preset.parameters)
    raise ValueError(f"Unknown system: {preset.system}")


class ChaoticAttractorMusicLab:
    def __init__(self, preset_index: int = 1) -> None:
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
            )
            self.clock.tick(config.FPS)
        pygame.quit()

    def _simulate(self) -> None:
        self.simulation_credit += (self.steps_per_frame * self.preset.speed_multiplier) / config.SIMULATION_SPEED_DIVISOR
        steps_to_run = int(self.simulation_credit)
        self.simulation_credit -= steps_to_run
        for _ in range(steps_to_run):
            if self.system.is_discrete:
                point = self.system.update()
            else:
                self.system.set_state(rk4_step(self.system, self.system.current_point(), config.DEFAULT_DT))
                point = self.system.current_point()

            lyapunov_raw = self.lyapunov.step() if self.chaos_mode else 0.0
            lyapunov_value = lyapunov_raw * self.chaos_influence
            current_speed = speed(self.previous_point, point, config.DEFAULT_DT)
            current_acceleration = acceleration(self.previous_speed, current_speed, config.DEFAULT_DT)
            self.points_for_curvature.append(point.copy())
            self.points_for_curvature = self.points_for_curvature[-3:]
            current_curvature = 0.0
            if len(self.points_for_curvature) == 3:
                current_curvature = curvature(*self.points_for_curvature)

            note = self.mapper.state_to_note(
                point,
                self.system.name,
                lyapunov_value,
                speed=current_speed,
                acceleration=current_acceleration,
                curvature=current_curvature,
            )
            if self.music.play_note(note, self.density_multiplier):
                self.renderer.trigger_note_pulse()
            self.renderer.append_point(point, current_speed, lyapunov_value)
            self.previous_point = point.copy()
            self.previous_speed = current_speed

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
        elif action == "mute":
            self.music.toggle_mute()
        elif action == "save_midi":
            output = Path(config.EXPORT_DIR) / config.DEFAULT_MIDI_FILE
            self.music.export_midi(output)
        elif action == "bifurcation":
            save_logistic_bifurcation(Path(config.EXPORT_DIR) / config.BIFURCATION_IMAGE)
        elif action == "chaos":
            self.chaos_mode = not self.chaos_mode
        elif action == "scale":
            self._cycle_scale()
        elif action == "auto_camera":
            self.auto_camera = not self.auto_camera
        elif action == "fullscreen":
            self.renderer.toggle_fullscreen()
        elif action == "exit":
            self.running = False
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
        elif action == "camera_zoom" and value is not None:
            self.renderer.camera.zoom = float(value)
        elif action == "camera_rotation_x" and value is not None:
            self.renderer.camera.rotation_x = float(value)
        elif action == "camera_rotation_y" and value is not None:
            self.renderer.camera.rotation_y = float(value)

    def _cycle_scale(self) -> None:
        names = list(SCALES)
        current = names.index(self.mapper.scale_name) if self.mapper.scale_name in names else 0
        self.mapper.scale_name = names[(current + 1) % len(names)]

    def _handle_key(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_SPACE:
            self.paused = not self.paused
        elif key == pygame.K_r:
            self.reset()
        elif pygame.K_1 <= key <= pygame.K_5:
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
