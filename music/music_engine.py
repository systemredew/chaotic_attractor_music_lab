from __future__ import annotations

from pathlib import Path
import math
import time

import numpy as np
import pygame

import config
from music.mapper import NoteEvent
from music.midi_exporter import MidiExporter


class MusicEngine:
    def __init__(self) -> None:
        self.muted = False
        self.last_note_time = 0.0
        self.current_note: int | None = None
        self.current_notes: list[int] = []
        self.events: list[tuple[float, NoteEvent]] = []
        self.tempo_bpm = config.DEFAULT_TEMPO_BPM
        self.echo_amount = 0.0
        self._midi_out = None
        self._audio_ready = False
        self.init_midi()
        self._init_audio_fallback()

    def init_midi(self) -> None:
        try:
            import mido

            outputs = mido.get_output_names()
            if outputs:
                self._midi_out = mido.open_output(outputs[0])
        except Exception:
            self._midi_out = None

    def _init_audio_fallback(self) -> None:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
            self._audio_ready = True
        except Exception:
            self._audio_ready = False

    def play_note(self, event: NoteEvent, density_multiplier: float = 1.0) -> bool:
        now = time.monotonic()
        cooldown = np.interp(
            np.clip(event.density * density_multiplier, 0.0, 1.0),
            [0.0, 1.0],
            [config.MAX_NOTE_COOLDOWN, config.MIN_NOTE_COOLDOWN],
        )
        cooldown *= config.DEFAULT_TEMPO_BPM / max(config.MIN_BPM, self.tempo_bpm)
        if self.muted or now - self.last_note_time < cooldown:
            return False
        self.last_note_time = now
        self.current_note = event.note
        self.current_notes = [event.note]
        self.events.append((now, event))
        if self._midi_out is not None:
            self._play_midi(event)
        elif self._audio_ready:
            self._play_tone(event)
        return True

    def play_events(self, events: list[NoteEvent], density_multiplier: float = 1.0) -> bool:
        if not events:
            return False
        now = time.monotonic()
        gate_event = max(events, key=lambda event: event.density)
        cooldown = np.interp(
            np.clip(gate_event.density * density_multiplier, 0.0, 1.0),
            [0.0, 1.0],
            [config.MAX_NOTE_COOLDOWN, config.MIN_NOTE_COOLDOWN],
        )
        cooldown *= config.DEFAULT_TEMPO_BPM / max(config.MIN_BPM, self.tempo_bpm)
        if self.muted or now - self.last_note_time < cooldown:
            return False
        self.last_note_time = now
        self.current_note = events[0].note
        self.current_notes = [event.note for event in events]
        for event in events:
            self.events.append((now, event))
            if self._midi_out is not None:
                self._play_midi(event)
            elif self._audio_ready:
                self._play_tone(event)
        return True

    def _play_midi(self, event: NoteEvent) -> None:
        import mido

        self._midi_out.send(mido.Message("note_on", note=event.note, velocity=event.velocity, channel=event.channel))
        pygame.time.set_timer(pygame.USEREVENT + 1, int(event.duration * 1000), loops=1)

    def note_off(self, note: int | None = None) -> None:
        notes = self.current_notes if note is None else [note]
        if not notes or self._midi_out is None:
            return
        import mido

        for current in notes:
            self._midi_out.send(mido.Message("note_off", note=current, velocity=0, channel=config.DEFAULT_CHANNEL))

    def _play_tone(self, event: NoteEvent) -> None:
        frequency = 440.0 * (2.0 ** ((event.note - 69) / 12.0))
        sample_rate = 44100
        base_samples = max(1, int(sample_rate * event.duration))
        echo_tail = int(sample_rate * (0.28 + np.clip(self.echo_amount, 0.0, 1.0) * 0.45))
        n_samples = base_samples + (echo_tail if self.echo_amount > 0.01 else 0)
        t = np.linspace(0.0, event.duration, base_samples, False)
        envelope = np.minimum(1.0, np.linspace(0.0, 12.0, base_samples)) * np.linspace(1.0, 0.0, base_samples)
        base_wave = np.sin(2.0 * math.pi * frequency * t) * envelope * (event.velocity / 127.0)
        wave = np.zeros(n_samples, dtype=np.float64)
        wave[:base_samples] = base_wave
        if event.fuzz > 0.01:
            drive = 1.0 + event.fuzz * 18.0
            wave = np.tanh(wave * drive) / np.tanh(drive)
        if self.echo_amount > 0.01:
            delay = int(sample_rate * 0.14)
            echo = np.zeros_like(wave)
            if delay < n_samples:
                feedback = np.clip(self.echo_amount, 0.0, 1.0) * 0.72
                echo[delay:] += wave[:-delay] * feedback
                second_delay = delay * 2
                if second_delay < n_samples:
                    echo[second_delay:] += wave[:-second_delay] * feedback * 0.52
                third_delay = delay * 3
                if third_delay < n_samples:
                    echo[third_delay:] += wave[:-third_delay] * feedback * 0.28
            wave = np.clip(wave + echo, -1.0, 1.0)
        sound = pygame.sndarray.make_sound((wave * 32767).astype(np.int16))
        sound.play()

    def mute(self) -> None:
        self.muted = True
        self.note_off()

    def unmute(self) -> None:
        self.muted = False

    def toggle_mute(self) -> None:
        self.unmute() if self.muted else self.mute()

    def export_midi(self, filename: str | Path) -> Path:
        exporter = MidiExporter(self.tempo_bpm)
        return exporter.export(self.events, filename)
