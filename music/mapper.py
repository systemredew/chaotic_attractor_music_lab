from __future__ import annotations

from dataclasses import dataclass
import random

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
    fuzz: float = 0.0
    channel: int = config.DEFAULT_CHANNEL
    echo: float = 0.0


class MusicMapper:
    def __init__(self, root_note: int = config.DEFAULT_ROOT_NOTE, scale_name: str = "minor_pentatonic") -> None:
        self.root_note = root_note
        self.scale_name = scale_name
        self.bpm = config.DEFAULT_TEMPO_BPM
        self.note_length_multiplier = 1.0
        self.octave_range = 4
        self.note_probability = 1.0
        self.swing = 0.0
        self.fuzz_amount = 0.0
        self.multi_voice = True
        self._event_counter = 0

    @property
    def scale(self) -> list[int]:
        return SCALES[self.scale_name]

    def normalize(self, value: float, min_value: float, max_value: float) -> float:
        if not np.isfinite(value):
            return 0.0
        if abs(max_value - min_value) < 1e-12:
            return 0.0
        return float(np.clip((value - min_value) / (max_value - min_value), 0.0, 1.0))

    def map_to_scale(self, value: float, root: int | None = None, scale: list[int] | None = None, octaves: int | None = None) -> int:
        selected_scale = scale or self.scale
        root_note = self.root_note if root is None else root
        selected_octaves = self.octave_range if octaves is None else octaves
        value = float(np.clip(value, 0.0, 1.0))
        degree = int(value * (len(selected_scale) * selected_octaves - 1))
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
        values = np.nan_to_num(np.asarray(state, dtype=np.float64), nan=0.0, posinf=0.0, neginf=0.0)
        x = float(values[0]) if values.size > 0 else 0.0
        y = float(values[1]) if values.size > 1 else x
        z = float(values[2]) if values.size > 2 else 0.0

        if system_name == "Lorenz":
            pitch_value = self.normalize(x, -30.0, 30.0)
            echo_value = min(0.7, self.normalize(abs(y), 0.0, 35.0) * 0.75)
            octave_shift = round(self.normalize(z, 0.0, 55.0) * 12)
        elif system_name == "Rossler":
            pitch_value = self.normalize(x, -15.0, 15.0)
            echo_value = min(0.7, self.normalize(abs(y), 0.0, 15.0) * 0.75)
            octave_shift = round(self.normalize(z, 0.0, 30.0) * 7)
        elif system_name == "Halvorsen":
            pitch_value = self.normalize(x, -12.0, 12.0)
            echo_value = min(0.7, self.normalize(abs(y), 0.0, 12.0) * 0.75)
            octave_shift = round(self.normalize(z, -12.0, 12.0) * 10)
        elif system_name == "Henon":
            pitch_value = self.normalize(x, -1.5, 1.5)
            echo_value = min(0.7, self.normalize(abs(y), 0.0, 0.45) * 0.8)
            octave_shift = 0
        else:
            return self.logistic_to_note(float(values[1] if values.size > 1 else values[0]), float(values[0] if values.size > 1 else 3.7))

        note = self.map_to_scale(pitch_value)
        note = int(np.clip(note + octave_shift, 0, 127))
        acceleration = 0.0 if not np.isfinite(acceleration) else acceleration
        curvature = 0.0 if not np.isfinite(curvature) else curvature
        velocity = self.speed_to_velocity(speed) + int(min(acceleration, 180.0) / 180.0 * 18)
        velocity = int(np.clip(velocity, 28, 124))
        density = self.chaos_to_density(lyapunov_value) + min(curvature / np.pi, 1.0) * 0.15
        duration = self._duration(float(np.clip(config.DEFAULT_NOTE_DURATION * (1.4 - density), 0.06, 0.6)))
        return NoteEvent(
            note=note,
            velocity=velocity,
            duration=duration,
            density=float(np.clip(density, 0.05, 1.0)),
            fuzz=float(np.clip(self.fuzz_amount, 0.0, 1.0)),
            echo=echo_value,
        )

    def speed_to_velocity(self, speed: float) -> int:
        if not np.isfinite(speed):
            speed = 0.0
        value = self.normalize(speed, 0.0, 90.0)
        return int(35 + value * 70)

    def chaos_to_density(self, lyapunov_value: float) -> float:
        if not np.isfinite(lyapunov_value):
            lyapunov_value = 0.0
        return float(np.clip((lyapunov_value + 0.5) / 3.5, 0.08, 1.0))

    def logistic_to_note(self, x: float, r: float) -> NoteEvent:
        x = 0.5 if not np.isfinite(x) else x
        r = 3.7 if not np.isfinite(r) else r
        tension = self.normalize(r, config.BIFURCATION_R_MIN, config.BIFURCATION_R_MAX)
        scale = SCALES["major"] if tension < 0.52 else SCALES["natural_minor"]
        note = self.map_to_scale(float(np.clip(x, 0.0, 1.0)), scale=scale, octaves=5)
        velocity = int(np.clip(38 + tension * 70 + abs(x - 0.5) * 25, 25, 127))
        density = float(np.clip(0.15 + tension * 0.85, 0.1, 1.0))
        subdivision = self._duration(0.5 if r < 3.0 else 0.33 if r < 3.55 else 0.16)
        return NoteEvent(
            note=note,
            velocity=velocity,
            duration=subdivision,
            density=density,
            fuzz=float(np.clip(self.fuzz_amount, 0.0, 1.0)),
            echo=min(0.7, abs(x - 0.5) * 1.4),
        )

    def state_to_events(
        self,
        state: Array,
        system_name: str,
        lyapunov_value: float,
        speed: float = 0.0,
        acceleration: float = 0.0,
        curvature: float = 0.0,
    ) -> list[NoteEvent]:
        if random.random() > self.note_probability:
            return []
        lead = self.state_to_note(state, system_name, lyapunov_value, speed, acceleration, curvature)
        self._event_counter += 1
        if self.swing > 0.0 and self._event_counter % 2 == 0:
            lead = NoteEvent(lead.note, lead.velocity, lead.duration * (1.0 + self.swing * 0.5), lead.density, lead.fuzz, lead.channel, lead.echo)
        if not self.multi_voice:
            return [lead]

        events = [lead]
        if system_name == "Rossler":
            bass = NoteEvent(max(0, lead.note - 24), max(22, lead.velocity - 36), lead.duration * 2.6, max(0.05, lead.density * 0.35), lead.fuzz * 0.45, 1, lead.echo * 0.8)
            events.append(bass)
        elif system_name == "Henon":
            perc_note = 36 + (lead.note % 12)
            events.append(NoteEvent(perc_note, min(127, lead.velocity + 12), max(0.035, lead.duration * 0.35), min(1.0, lead.density + 0.2), lead.fuzz, 9, lead.echo))
        elif lyapunov_value > 0.35:
            interval = 7 if curvature < 1.2 else 10
            harmony = NoteEvent(min(127, lead.note + interval), max(24, lead.velocity - 24), lead.duration * 1.35, lead.density * 0.55, lead.fuzz * 0.7, 2, lead.echo * 0.9)
            events.append(harmony)
        return events

    def _duration(self, duration: float) -> float:
        beat_seconds = 60.0 / max(config.MIN_BPM, self.bpm)
        scaled = duration * self.note_length_multiplier
        return float(np.clip(scaled, beat_seconds * 0.08, beat_seconds * 2.0))
