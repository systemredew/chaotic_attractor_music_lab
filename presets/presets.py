from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Preset:
    name: str
    system: str
    parameters: dict[str, float]
    scale: str
    note_density: float
    description: str
    speed_multiplier: float = 1.0


PRESETS: list[Preset] = [
    Preset("Calm Lorenz", "Lorenz", {"sigma": 10.0, "rho": 20.0, "beta": 8.0 / 3.0}, "minor_pentatonic", 0.55, "slow ambient behavior"),
    Preset("Butterfly Chaos", "Lorenz", {"sigma": 10.0, "rho": 28.0, "beta": 8.0 / 3.0}, "natural_minor", 0.9, "classic chaotic attractor"),
    Preset("Rossler Drone", "Rossler", {"a": 0.2, "b": 0.2, "c": 5.7}, "harmonic_minor", 0.45, "long drone-like behavior", 5.0),
    Preset("Halvorsen Storm", "Halvorsen", {"a": 1.4}, "whole_tone", 0.95, "dense folded motion"),
    Preset("Henon Percussion", "Henon", {"a": 1.4, "b": 0.3}, "whole_tone", 1.15, "short rhythm-oriented output", 0.2),
    Preset("Bifurcation Piano", "Logistic", {"r": 2.5, "x0": 0.5}, "major", 0.85, "order-to-chaos sequencer"),
]
