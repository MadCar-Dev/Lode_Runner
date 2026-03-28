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


class TestSoundManagerBGM:
    @pytest.fixture()
    def sm(self):
        """Create a SoundManager with mocked mixer for BGM tests."""
        from sound_manager import SoundManager

        with patch("sound_manager.pygame.mixer") as mock_mixer:
            mock_mixer.get_init.return_value = (44100, -16, 1)
            mock_mixer.init.return_value = None
            mock_channel = MagicMock()
            mock_mixer.Channel.return_value = mock_channel
            with patch(
                "sound_manager.pygame.sndarray.make_sound",
                return_value=MagicMock(),
            ):
                sm = SoundManager()
        sm._bgm_channel = mock_channel
        return sm

    def test_music_off_by_default(self, sm):
        assert sm._music_playing is False

    def test_toggle_music_enables(self, sm):
        sm.toggle_music()
        assert sm._music_playing is True

    def test_toggle_music_disables(self, sm):
        sm.toggle_music()  # on
        sm.toggle_music()  # off
        assert sm._music_playing is False

    def test_toggle_off_stops_bgm(self, sm):
        sm.toggle_music()  # on
        with patch(
            "sound_manager.pygame.sndarray.make_sound",
            return_value=MagicMock(),
        ):
            sm.play_bgm("bgm_game")
        sm.toggle_music()  # off — should stop
        sm._bgm_channel.stop.assert_called()

    def test_play_bgm_when_music_off_is_noop(self, sm):
        sm.play_bgm("bgm_game")
        sm._bgm_channel.play.assert_not_called()

    def test_play_bgm_when_music_on(self, sm):
        sm.toggle_music()  # on
        with patch(
            "sound_manager.pygame.sndarray.make_sound",
            return_value=MagicMock(),
        ):
            sm.play_bgm("bgm_game")
        sm._bgm_channel.play.assert_called_once()

    def test_play_bgm_same_track_no_restart(self, sm):
        sm.toggle_music()
        with patch(
            "sound_manager.pygame.sndarray.make_sound",
            return_value=MagicMock(),
        ):
            sm.play_bgm("bgm_game")
            sm.play_bgm("bgm_game")  # same track — should not restart
        # play called only once (not twice)
        assert sm._bgm_channel.play.call_count == 1

    def test_play_bgm_different_track_switches(self, sm):
        sm.toggle_music()
        with patch(
            "sound_manager.pygame.sndarray.make_sound",
            return_value=MagicMock(),
        ):
            sm.play_bgm("bgm_game")
            sm.play_bgm("bgm_level_complete")
        assert sm._bgm_channel.play.call_count == 2

    def test_stop_bgm_clears_current(self, sm):
        sm.toggle_music()
        with patch(
            "sound_manager.pygame.sndarray.make_sound",
            return_value=MagicMock(),
        ):
            sm.play_bgm("bgm_game")
        sm.stop_bgm()
        assert sm._current_bgm == ""

    def test_all_bgm_tracks_registered(self, sm):
        expected = {"bgm_game", "bgm_level_complete", "bgm_game_over"}
        assert expected.issubset(set(sm._bgm_tracks.keys()))

    def test_toggle_when_disabled_is_noop(self):
        from sound_manager import SoundManager

        with patch("sound_manager.pygame.mixer") as mock_mixer:
            mock_mixer.get_init.return_value = None
            mock_mixer.init.side_effect = Exception("no audio")
            sm = SoundManager()
        sm.toggle_music()  # must not raise
        assert sm._music_playing is False
