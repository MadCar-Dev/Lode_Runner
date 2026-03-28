"""Procedural audio — all sounds synthesized with numpy + pygame.sndarray."""

from __future__ import annotations

import numpy as np
import pygame


class SoundManager:
    """Synthesizes and plays all game audio. No external audio files.

    Gracefully no-ops if pygame.mixer cannot initialize (headless/CI).
    """

    def __init__(self) -> None:
        self.enabled: bool = False
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._music_playing: bool = False
        self._bgm_tracks: dict[str, np.ndarray] = {}
        self._bgm_channel: pygame.mixer.Channel | None = None
        self._current_bgm: str = ""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
            self.enabled = True
        except Exception:
            return
        self._build_sfx()
        self._build_bgm()
        self._bgm_channel = pygame.mixer.Channel(7)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def play_event(self, name: str) -> None:
        """Play a one-shot sound effect by name. No-op if disabled."""
        if not self.enabled:
            return
        sound = self._sounds.get(name)
        if sound is not None:
            sound.play()

    def play_bgm(self, name: str) -> None:
        """Start looping a BGM track by name. No-op if disabled."""
        if not self.enabled or not self._music_playing:
            return
        if name == self._current_bgm:
            return
        arr = self._bgm_tracks.get(name)
        if arr is None:
            return
        snd = pygame.sndarray.make_sound(arr)
        if self._bgm_channel is not None:
            self._bgm_channel.stop()
            loop = -1 if name == "bgm_game" else 0
            self._bgm_channel.play(snd, loops=loop)
        self._current_bgm = name

    def stop_bgm(self) -> None:
        """Stop any playing BGM."""
        if self._bgm_channel is not None:
            self._bgm_channel.stop()
        self._current_bgm = ""

    def toggle_music(self) -> None:
        """Toggle BGM on/off. Called when the player presses M."""
        if not self.enabled:
            return
        self._music_playing = not self._music_playing
        if not self._music_playing:
            self.stop_bgm()

    # ------------------------------------------------------------------
    # Waveform helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sine(freq: float, duration: float, volume: float = 0.3) -> np.ndarray:
        """Generate a mono 16-bit sine wave."""
        sr = 44100
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        wave = np.sin(2 * np.pi * freq * t) * volume
        return (wave * 32767).astype(np.int16)

    @staticmethod
    def _square(freq: float, duration: float, volume: float = 0.2) -> np.ndarray:
        """Generate a mono 16-bit square wave."""
        sr = 44100
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        wave = np.sign(np.sin(2 * np.pi * freq * t)) * volume
        return (wave * 32767).astype(np.int16)

    @staticmethod
    def _noise(duration: float, volume: float = 0.15) -> np.ndarray:
        """Generate mono 16-bit white noise."""
        sr = 44100
        samples = int(sr * duration)
        rng = np.random.default_rng(seed=42)
        wave = rng.uniform(-1.0, 1.0, samples) * volume
        return (wave * 32767).astype(np.int16)

    @staticmethod
    def _fade_out(arr: np.ndarray) -> np.ndarray:
        """Apply a linear fade-out envelope to the entire array."""
        envelope = np.linspace(1.0, 0.0, len(arr))
        return (arr * envelope).astype(np.int16)

    @staticmethod
    def _fade_in(arr: np.ndarray, frac: float = 0.1) -> np.ndarray:
        """Apply a linear fade-in to the first `frac` of the array."""
        n = max(1, int(len(arr) * frac))
        envelope = np.ones(len(arr))
        envelope[:n] = np.linspace(0.0, 1.0, n)
        return (arr * envelope).astype(np.int16)

    def _make_sound(self, arr: np.ndarray) -> pygame.mixer.Sound:
        """Convert a 1-D int16 numpy array to a pygame Sound.

        Handles both mono (1-channel) and stereo (2-channel) mixer configurations
        by duplicating the mono signal across channels when needed.
        """
        mixer_info = pygame.mixer.get_init()
        if mixer_info is not None:
            channels = mixer_info[2]
            if channels == 2 and arr.ndim == 1:
                arr = np.column_stack([arr, arr])
        return pygame.sndarray.make_sound(arr)

    # ------------------------------------------------------------------
    # SFX builders
    # ------------------------------------------------------------------

    def _build_sfx(self) -> None:
        """Synthesize all one-shot sound effects."""
        # Footstep — short quiet tick
        self._sounds["footstep"] = self._make_sound(self._fade_out(self._square(200, 0.04, 0.1)))

        # Dig — crunchy noise burst
        dig = self._noise(0.15, 0.2)
        dig = self._fade_out(dig)
        self._sounds["dig"] = self._make_sound(dig)

        # Gold pickup — two-tone ascending chime
        tone1 = self._sine(880, 0.08, 0.3)
        tone2 = self._sine(1320, 0.12, 0.3)
        gold = np.concatenate([tone1, tone2])
        gold = self._fade_out(gold)
        self._sounds["gold_pickup"] = self._make_sound(gold)

        # Enemy trap — low thud
        trap = self._sine(120, 0.2, 0.35)
        trap = self._fade_out(trap)
        self._sounds["enemy_trap"] = self._make_sound(trap)

        # Enemy death — descending buzz
        sr = 44100
        dur = 0.3
        t = np.linspace(0, dur, int(sr * dur), endpoint=False)
        freq = np.linspace(300, 80, len(t))
        wave = np.sign(np.sin(2 * np.pi * freq * t)) * 0.2
        death = (wave * 32767).astype(np.int16)
        death = self._fade_out(death)
        self._sounds["enemy_death"] = self._make_sound(death)

        # Player death — long descending tone
        dur = 0.6
        t = np.linspace(0, dur, int(sr * dur), endpoint=False)
        freq = np.linspace(600, 100, len(t))
        wave = np.sin(2 * np.pi * freq * t) * 0.35
        pd = (wave * 32767).astype(np.int16)
        pd = self._fade_out(pd)
        self._sounds["player_death"] = self._make_sound(pd)

        # Ladder reveal — ascending arpeggio
        notes = [440, 554, 659, 880]
        parts = [self._fade_out(self._sine(n, 0.1, 0.25)) for n in notes]
        reveal = np.concatenate(parts)
        self._sounds["ladder_reveal"] = self._make_sound(reveal)

        # Level complete — triumphant fanfare
        fanfare_notes = [523, 659, 784, 1047]
        fanfare_parts = [self._sine(n, 0.15, 0.3) for n in fanfare_notes]
        fanfare = np.concatenate(fanfare_parts)
        fanfare = self._fade_out(fanfare)
        self._sounds["level_complete"] = self._make_sound(fanfare)

        # Game over — slow descending tones
        go_notes = [440, 349, 262, 196]
        go_parts = [self._fade_out(self._sine(n, 0.25, 0.3)) for n in go_notes]
        game_over = np.concatenate(go_parts)
        self._sounds["game_over"] = self._make_sound(game_over)

    # ------------------------------------------------------------------
    # BGM builders
    # ------------------------------------------------------------------

    def _build_bgm(self) -> None:
        """Synthesize background music tracks as numpy arrays."""
        sr = 44100

        # BGM game — simple looping bass line (2 bars, ~2 seconds)
        notes = [130.81, 146.83, 164.81, 146.83]  # C3 D3 E3 D3
        bar_dur = 0.5
        parts = []
        for note in notes:
            t = np.linspace(0, bar_dur, int(sr * bar_dur), endpoint=False)
            wave = np.sin(2 * np.pi * note * t) * 0.15
            parts.append((wave * 32767).astype(np.int16))
        self._bgm_tracks["bgm_game"] = np.concatenate(parts)

        # BGM level complete — bright major chord held
        dur = 3.0
        t = np.linspace(0, dur, int(sr * dur), endpoint=False)
        chord = (
            np.sin(2 * np.pi * 523.25 * t)
            + np.sin(2 * np.pi * 659.25 * t) * 0.8
            + np.sin(2 * np.pi * 783.99 * t) * 0.6
        )
        chord = chord / 3.0 * 0.2
        env = np.linspace(1.0, 0.0, len(t))
        bgm_lc = (chord * env * 32767).astype(np.int16)
        self._bgm_tracks["bgm_level_complete"] = bgm_lc

        # BGM game over — minor chord fade
        dur = 4.0
        t = np.linspace(0, dur, int(sr * dur), endpoint=False)
        chord = (
            np.sin(2 * np.pi * 220.0 * t)
            + np.sin(2 * np.pi * 261.63 * t) * 0.8
            + np.sin(2 * np.pi * 329.63 * t) * 0.6
        )
        chord = chord / 3.0 * 0.2
        env = np.linspace(1.0, 0.0, len(t))
        bgm_go = (chord * env * 32767).astype(np.int16)
        self._bgm_tracks["bgm_game_over"] = bgm_go
