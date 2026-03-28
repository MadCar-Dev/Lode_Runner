"""Tests for GameState — construction, phase, handle_event delegation."""

from __future__ import annotations

import pygame

import constants as C
from game import GamePhase, GameState


class TestGameStateInit:
    def test_default_construction(self):
        gs = GameState()
        assert gs.level_number == 1
        assert gs.score == 0
        assert gs.lives == C.STARTING_LIVES
        assert gs.phase == GamePhase.PLAYING

    def test_gold_remaining_matches_level(self):
        gs = GameState()
        assert gs.gold_remaining == len(gs.level.gold_positions())

    def test_player_at_spawn(self):
        gs = GameState()
        assert gs.player.col == gs.level.player_spawn.col
        assert gs.player.row == gs.level.player_spawn.row

    def test_enemies_spawned(self):
        gs = GameState()
        assert len(gs.enemies) == len(gs.level.enemy_spawns)

    def test_phase_is_enum(self):
        assert GamePhase.PLAYING != GamePhase.GAME_OVER
        assert GamePhase.PLAYER_DEAD != GamePhase.LEVEL_COMPLETE


class TestGameStateHandleEvent:
    def test_handle_event_in_playing_phase(self):
        pygame.init()
        gs = GameState()
        # Send a LEFT keydown — should not crash
        event = pygame.event.Event(pygame.KEYDOWN, key=C.KEY_LEFT)
        gs.handle_event(event)  # must not raise

    def test_handle_event_ignored_in_game_over(self):
        pygame.init()
        gs = GameState()
        gs.phase = GamePhase.GAME_OVER
        event = pygame.event.Event(pygame.KEYDOWN, key=C.KEY_LEFT)
        gs.handle_event(event)  # must not raise; input ignored in GAME_OVER
