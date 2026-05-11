from __future__ import annotations

import numpy as np

from music.mapper import MusicMapper


def test_music_mapper_returns_valid_midi_note() -> None:
    mapper = MusicMapper(scale_name="natural_minor")
    event = mapper.state_to_note(np.asarray([1.0, 2.0, 3.0]), "Lorenz", lyapunov_value=0.7)
    assert 0 <= event.note <= 127
