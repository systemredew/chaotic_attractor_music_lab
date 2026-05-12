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
        if self._should_play_audio(event):
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
            if self._should_play_audio(event):
                self._play_tone(event)
        return True

    def _should_play_audio(self, event: NoteEvent) -> bool:
        if not self._audio_ready:
            return False
        return self._midi_out is None or event.echo > 0.01 or event.fuzz > 0.01

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
        echo = float(np.clip(event.echo, 0.0, 1.0))
        base_samples = max(1, int(sample_rate * event.duration))
        echo_tail = int(sample_rate * (0.35 + echo * 0.9))
        n_samples = base_samples + (echo_tail if echo > 0.01 else 0)
        t = np.linspace(0.0, event.duration, base_samples, False)
        envelope = np.minimum(1.0, np.linspace(0.0, 12.0, base_samples)) * np.linspace(1.0, 0.0, base_samples)
        base_wave = np.sin(2.0 * math.pi * frequency * t) * envelope * (event.velocity / 127.0)
        dry_gain = 0.0 if self._midi_out is not None and event.fuzz <= 0.01 and echo > 0.01 else 1.0
        wave = np.zeros(n_samples, dtype=np.float64)
        wave[:base_samples] = base_wave * dry_gain
        echo_source = np.zeros(n_samples, dtype=np.float64)
        echo_source[:base_samples] = base_wave
        if event.fuzz > 0.01:
            drive = 1.0 + event.fuzz * 7.0
            wave = np.tanh(wave * drive) / np.tanh(drive)
            echo_source = np.tanh(echo_source * drive) / np.tanh(drive)
        if echo > 0.01:
            delay = int(sample_rate * 0.11)
            echo_wave = np.zeros_like(wave)
            if delay < n_samples:
                feedback = 0.22 + echo * 0.36
                wet_gain = 0.45 + echo * 0.65
                for repeat, decay in enumerate((1.0, 0.58, 0.34, 0.2), start=1):
                    offset = delay * repeat
                    if offset < n_samples:
                        echo_wave[offset:] += echo_source[:-offset] * feedback * decay * wet_gain
            wave = wave + echo_wave
            peak = float(np.max(np.abs(wave)))
            if peak > 0.82:
                wave = wave / peak * 0.82
        audio = (wave * 32767).astype(np.int16)
        mixer_info = pygame.mixer.get_init()
        if mixer_info is not None and mixer_info[2] == 2:
            audio = np.column_stack((audio, audio))
        sound = pygame.sndarray.make_sound(audio)
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
