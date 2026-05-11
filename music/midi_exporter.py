from __future__ import annotations

from pathlib import Path

import mido

import config
from music.mapper import NoteEvent


def seconds_to_ticks(seconds: float, tempo: int, ticks_per_beat: int) -> int:
    return max(1, int(mido.second2tick(seconds, ticks_per_beat, tempo)))


class MidiExporter:
    def __init__(self, tempo_bpm: int = config.DEFAULT_TEMPO_BPM) -> None:
        self.tempo = mido.bpm2tempo(tempo_bpm)
        self.ticks_per_beat = config.MIDI_TICKS_PER_BEAT

    def export(self, events: list[tuple[float, NoteEvent]], filename: str | Path) -> Path:
        output = Path(filename)
        output.parent.mkdir(parents=True, exist_ok=True)
        midi = mido.MidiFile(ticks_per_beat=self.ticks_per_beat)
        track = mido.MidiTrack()
        midi.tracks.append(track)
        track.append(mido.MetaMessage("set_tempo", tempo=self.tempo, time=0))

        last_time = 0.0
        for event_time, event in sorted(events, key=lambda item: item[0]):
            delta_seconds = max(0.0, event_time - last_time)
            track.append(
                mido.Message(
                    "note_on",
                    note=event.note,
                    velocity=event.velocity,
                    channel=event.channel,
                    time=seconds_to_ticks(delta_seconds, self.tempo, self.ticks_per_beat),
                )
            )
            track.append(
                mido.Message(
                    "note_off",
                    note=event.note,
                    velocity=0,
                    channel=event.channel,
                    time=seconds_to_ticks(event.duration, self.tempo, self.ticks_per_beat),
                )
            )
            last_time = event_time + event.duration

        midi.save(output)
        return output
