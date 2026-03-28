"""Tests for SoundManager — SFX synthesis, play_event, and BGM toggle."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestSoundManagerInit:
    def test_import(self):
        from sound_manager import SoundManager  # noqa: F401

    def test_construction_with_mixer(self):
        """SoundManager initializes when pygame.mixer is available."""
        import pygame

        pygame.init()
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
            mixer_available = True
        except pygame.error:
            mixer_available = False
        if mixer_available:
            from sound_manager import SoundManager

            sm = SoundManager()
            assert sm.enabled is True
            pygame.mixer.quit()
        else:
            pytest.skip("pygame.mixer not available in this environment")
        pygame.quit()

    def test_construction_without_mixer(self):
        """SoundManager gracefully degrades when mixer is unavailable."""
        from sound_manager import SoundManager

        with patch("sound_manager.pygame.mixer") as mock_mixer:
            mock_mixer.get_init.return_value = None
            mock_mixer.init.side_effect = Exception("no audio")
            sm = SoundManager()
            assert sm.enabled is False

    def test_play_event_when_disabled_does_not_raise(self):
        """play_event is a no-op when mixer is unavailable."""
        from sound_manager import SoundManager

        with patch("sound_manager.pygame.mixer") as mock_mixer:
            mock_mixer.get_init.return_value = None
            mock_mixer.init.side_effect = Exception("no audio")
            sm = SoundManager()
            sm.play_event("gold_pickup")  # must not raise


class TestSoundManagerSFX:
    @pytest.fixture()
    def sm(self):
        """Create a SoundManager with mocked mixer."""
        from sound_manager import SoundManager

        with patch("sound_manager.pygame.mixer") as mock_mixer:
            mock_mixer.get_init.return_value = (44100, -16, 1)
            mock_mixer.init.return_value = None
            mock_sound = MagicMock()
            with patch(
                "sound_manager.pygame.sndarray.make_sound",
                return_value=mock_sound,
            ):
                sm = SoundManager()
        return sm

    def test_all_sfx_names_registered(self, sm):
        expected = {
            "footstep",
            "dig",
            "gold_pickup",
            "enemy_trap",
            "enemy_death",
            "player_death",
            "ladder_reveal",
            "level_complete",
            "game_over",
        }
        assert expected.issubset(set(sm._sounds.keys()))

    def test_play_event_known_name(self, sm):
        """play_event with a known name calls Sound.play()."""
        sm._sounds["gold_pickup"] = MagicMock()
        sm.play_event("gold_pickup")
        sm._sounds["gold_pickup"].play.assert_called_once()

    def test_play_event_unknown_name_does_not_raise(self, sm):
        """play_event with an unknown name silently does nothing."""
        sm.play_event("nonexistent_sound")  # must not raise
