from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import config
from music.scales import SCALES
from systems.base_system import Array


@dataclass(frozen=True)
class NoteEvent:
    note: int
    velocity: int
    duration: float
    density: float
    channel: int = config.DEFAULT_CHANNEL


class MusicMapper:
    def __init__(self, root_note: int = config.DEFAULT_ROOT_NOTE, scale_name: str = "minor_pentatonic") -> None:
        self.root_note = root_note
        self.scale_name = scale_name

    @property
    def scale(self) -> list[int]:
        return SCALES[self.scale_name]

    def normalize(self, value: float, min_value: float, max_value: float) -> float:
        if abs(max_value - min_value) < 1e-12:
            return 0.0
        return float(np.clip((value - min_value) / (max_value - min_value), 0.0, 1.0))

    def map_to_scale(self, value: float, root: int | None = None, scale: list[int] | None = None, octaves: int = 4) -> int:
        selected_scale = scale or self.scale
        root_note = self.root_note if root is None else root
        value = float(np.clip(value, 0.0, 1.0))
        degree = int(value * (len(selected_scale) * octaves - 1))
        octave, scale_index = divmod(degree, len(selected_scale))
        return int(np.clip(root_note + octave * 12 + selected_scale[scale_index], 0, 127))

    def state_to_note(
        self,
        state: Array,
        system_name: str,
        lyapunov_value: float,
        speed: float = 0.0,
        acceleration: float = 0.0,
        curvature: float = 0.0,
    ) -> NoteEvent:
        values = np.asarray(state, dtype=np.float64)
        x = float(values[0]) if values.size > 0 else 0.0
        y = float(values[1]) if values.size > 1 else x
        z = float(values[2]) if values.size > 2 else 0.0

        if system_name == "Lorenz":
            pitch_value = self.normalize(x, -30.0, 30.0)
            volume_value = self.normalize(y, -35.0, 35.0)
            octave_shift = round(self.normalize(z, 0.0, 55.0) * 12)
        elif system_name == "Rossler":
            pitch_value = self.normalize(x, -15.0, 15.0)
            volume_value = self.normalize(y, -15.0, 15.0)
            octave_shift = round(self.normalize(z, 0.0, 30.0) * 7)
        elif system_name == "Henon":
            pitch_value = self.normalize(x, -1.5, 1.5)
            volume_value = self.normalize(abs(y), 0.0, 0.45)
            octave_shift = 0
        else:
            return self.logistic_to_note(float(values[1] if values.size > 1 else values[0]), float(values[0] if values.size > 1 else 3.7))

        note = self.map_to_scale(pitch_value)
        note = int(np.clip(note + octave_shift, 0, 127))
        velocity = self.speed_to_velocity(speed) + int(volume_value * 28) + int(min(acceleration, 180.0) / 180.0 * 18)
        velocity = int(np.clip(velocity, 28, 124))
        density = self.chaos_to_density(lyapunov_value) + min(curvature / np.pi, 1.0) * 0.15
        duration = float(np.clip(config.DEFAULT_NOTE_DURATION * (1.4 - density), 0.06, 0.6))
        return NoteEvent(note=note, velocity=velocity, duration=duration, density=float(np.clip(density, 0.05, 1.0)))

    def speed_to_velocity(self, speed: float) -> int:
        value = self.normalize(speed, 0.0, 90.0)
        return int(35 + value * 70)

    def chaos_to_density(self, lyapunov_value: float) -> float:
        return float(np.clip((lyapunov_value + 0.5) / 3.5, 0.08, 1.0))

    def logistic_to_note(self, x: float, r: float) -> NoteEvent:
        tension = self.normalize(r, config.BIFURCATION_R_MIN, config.BIFURCATION_R_MAX)
        scale = SCALES["major"] if tension < 0.52 else SCALES["natural_minor"]
        note = self.map_to_scale(float(np.clip(x, 0.0, 1.0)), scale=scale, octaves=5)
        velocity = int(np.clip(38 + tension * 70 + abs(x - 0.5) * 25, 25, 127))
        density = float(np.clip(0.15 + tension * 0.85, 0.1, 1.0))
        subdivision = 0.5 if r < 3.0 else 0.33 if r < 3.55 else 0.16
        return NoteEvent(note=note, velocity=velocity, duration=subdivision, density=density)
