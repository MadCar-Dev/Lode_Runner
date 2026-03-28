"""Tests for GameState — construction, phase, handle_event delegation."""

from __future__ import annotations

import pygame

import constants as C
from enemy import Enemy, EnemyState
from game import GamePhase, GameState
from level import Level
from player import Player


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


def _make_game_with_patch(grid_patch: dict) -> "GameState":
    """Create a GameState but swap out its level with a custom grid."""
    gs = GameState()
    grid = [[C.EMPTY] * C.GRID_COLS for _ in range(C.GRID_ROWS)]
    for (col, row), tile in grid_patch.items():
        grid[row][col] = tile
    gs.level = Level(
        {
            "level": 1,
            "grid": grid,
            "player_spawn": {"col": 5, "row": 13},
            "enemy_spawns": [],
            "escape_ladder_cols": [0],
        }
    )
    gs.player = Player(gs.level.player_spawn.col, gs.level.player_spawn.row)
    gs.enemies = []
    gs.gold_remaining = len(gs.level.gold_positions())
    return gs


class TestPlayerEnemyCollision:
    def test_enemy_on_same_tile_kills_player(self):
        """RUNNING enemy at player's tile transitions game to PLAYER_DEAD."""
        gs = GameState()
        # Place player and enemy at same tile
        gs.player = Player(5, 5)
        enemy = Enemy(5, 5)
        enemy.state = EnemyState.RUNNING_RIGHT  # alive, not trapped/dead
        gs.enemies = [enemy]
        gs._check_player_collision()
        assert gs.phase == GamePhase.PLAYER_DEAD
        assert not gs.player.is_alive

    def test_dead_enemy_does_not_kill_player(self):
        gs = GameState()
        gs.player = Player(5, 5)
        enemy = Enemy(5, 5)
        enemy.state = EnemyState.DEAD
        gs.enemies = [enemy]
        gs._check_player_collision()
        assert gs.phase == GamePhase.PLAYING  # no kill

    def test_trapped_enemy_does_not_kill_player(self):
        gs = GameState()
        gs.player = Player(5, 5)
        enemy = Enemy(5, 5)
        enemy.state = EnemyState.TRAPPED
        gs.enemies = [enemy]
        gs._check_player_collision()
        assert gs.phase == GamePhase.PLAYING  # no kill


class TestGoldPickup:
    def test_player_on_gold_tile_removes_gold(self):
        patch = {(5, 13): C.GOLD, **{(c, 14): C.SOLID_BRICK for c in range(C.GRID_COLS)}}
        gs = _make_game_with_patch(patch)
        gs.player = Player(5, 13)
        assert gs.gold_remaining == 1
        gs._check_gold_pickup()
        assert gs.gold_remaining == 0
        assert gs.level.get_tile(5, 13) == C.EMPTY

    def test_gold_pickup_adds_score(self):
        patch = {(5, 13): C.GOLD, **{(c, 14): C.SOLID_BRICK for c in range(C.GRID_COLS)}}
        gs = _make_game_with_patch(patch)
        gs.player = Player(5, 13)
        gs._check_gold_pickup()
        assert gs.score == C.SCORE_GOLD

    def test_dead_player_cannot_pick_up_gold(self):
        patch = {(5, 13): C.GOLD, **{(c, 14): C.SOLID_BRICK for c in range(C.GRID_COLS)}}
        gs = _make_game_with_patch(patch)
        gs.player = Player(5, 13)
        gs.player.kill()
        gs._check_gold_pickup()
        assert gs.gold_remaining == 1  # unchanged


class TestEscapeLadderReveal:
    def test_all_gold_collected_reveals_escape_ladder(self):
        patch = {(5, 13): C.GOLD, **{(c, 14): C.SOLID_BRICK for c in range(C.GRID_COLS)}}
        patch[(0, 0)] = C.HIDDEN_LADDER
        gs = _make_game_with_patch(patch)
        gs.player = Player(5, 13)
        # Before pickup, hidden
        assert gs.level.get_tile(0, 0) == C.HIDDEN_LADDER
        gs._check_gold_pickup()
        assert gs.gold_remaining == 0
        # Escape ladder revealed
        assert gs.level.get_tile(0, 0) == C.LADDER
