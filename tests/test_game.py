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
        assert gs._phase_timer == 0.0

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


class TestEnemyScoring:
    def test_enemy_trapped_awards_score(self):
        """Score increases by SCORE_ENEMY_TRAPPED when enemy becomes TRAPPED."""
        gs = GameState()
        # Manufacture a transition: IDLE → TRAPPED
        enemy = Enemy(5, 5)
        enemy.state = EnemyState.IDLE
        gs.enemies = [enemy]
        old_state = enemy.state
        enemy.state = EnemyState.TRAPPED  # simulate transition
        gs._check_enemy_score(old_state, enemy)
        assert gs.score == C.SCORE_ENEMY_TRAPPED

    def test_enemy_killed_awards_score(self):
        """Score increases by SCORE_ENEMY_KILLED when TRAPPED enemy becomes DEAD."""
        gs = GameState()
        enemy = Enemy(5, 5)
        enemy.state = EnemyState.TRAPPED
        old_state = enemy.state
        enemy.state = EnemyState.DEAD  # simulate hole closing
        gs._check_enemy_score(old_state, enemy)
        assert gs.score == C.SCORE_ENEMY_KILLED

    def test_non_trapped_to_dead_does_not_score(self):
        """Enemies that die without being trapped (e.g. respawn) give no kill score."""
        gs = GameState()
        enemy = Enemy(5, 5)
        enemy.state = EnemyState.FALLING
        old_state = enemy.state
        enemy.state = EnemyState.DEAD
        gs._check_enemy_score(old_state, enemy)
        assert gs.score == 0  # no score for non-trap death

    def test_enemy_respawn_does_not_score(self):
        """Enemy going DEAD → FALLING (respawn) gives no score."""
        gs = GameState()
        enemy = Enemy(5, 5)
        enemy.state = EnemyState.DEAD
        old_state = enemy.state
        enemy.state = EnemyState.FALLING
        gs._check_enemy_score(old_state, enemy)
        assert gs.score == 0


class TestDeathAndRestart:
    def test_player_dead_phase_decrements_lives_after_timer(self):
        gs = GameState()
        initial_lives = gs.lives
        gs.phase = GamePhase.PLAYER_DEAD
        gs._phase_timer = 0.0
        # Advance past DEATH_DISPLAY_TIME
        gs.update(C.DEATH_DISPLAY_TIME + 0.1)
        assert gs.lives == initial_lives - 1

    def test_death_with_lives_remaining_restarts_level(self):
        gs = GameState()
        gs.lives = 2
        gs.phase = GamePhase.PLAYER_DEAD
        gs._phase_timer = 0.0
        gs.update(C.DEATH_DISPLAY_TIME + 0.1)
        assert gs.phase == GamePhase.PLAYING
        assert gs.lives == 1
        # Player should be reset to spawn
        assert gs.player.col == gs.level.player_spawn.col
        assert gs.player.row == gs.level.player_spawn.row

    def test_death_at_zero_lives_triggers_game_over(self):
        gs = GameState()
        gs.lives = 1
        gs.phase = GamePhase.PLAYER_DEAD
        gs._phase_timer = 0.0
        gs.update(C.DEATH_DISPLAY_TIME + 0.1)
        assert gs.phase == GamePhase.GAME_OVER
        assert gs.lives == 0

    def test_game_over_update_does_nothing(self):
        gs = GameState()
        gs.phase = GamePhase.GAME_OVER
        gs.score = 999
        gs.update(10.0)  # large dt
        assert gs.score == 999  # unchanged
        assert gs.phase == GamePhase.GAME_OVER


class TestLevelComplete:
    def test_player_on_escape_ladder_at_row_0_completes_level(self):
        """Player at col in escape_ladder_cols, row 0 → LEVEL_COMPLETE."""
        gs = GameState()
        gs.gold_remaining = 0  # all gold collected
        gs.level.reveal_escape_ladder()
        # Put player at top of escape ladder (col 0, row 0)
        gs.player = Player(0, 0)
        gs._check_level_complete()
        assert gs.phase == GamePhase.LEVEL_COMPLETE

    def test_level_complete_requires_zero_gold(self):
        gs = GameState()
        gs.gold_remaining = 1  # still gold left
        gs.player = Player(0, 0)
        gs._check_level_complete()
        assert gs.phase == GamePhase.PLAYING  # not complete yet

    def test_level_complete_awards_score_and_life(self):
        gs = GameState()
        gs.gold_remaining = 0
        gs.level.reveal_escape_ladder()
        gs.player = Player(0, 0)
        initial_score = gs.score
        initial_lives = gs.lives
        gs._check_level_complete()
        assert gs.score == initial_score + C.SCORE_LEVEL_COMPLETE
        assert gs.lives == initial_lives + C.LIVES_PER_LEVEL

    def test_level_complete_delay_loads_next_level(self):
        gs = GameState()
        gs.phase = GamePhase.LEVEL_COMPLETE
        gs._phase_timer = 0.0
        # Keep score from being reset (it persists across levels)
        gs.score = 500
        gs.update(C.LEVEL_COMPLETE_DELAY + 0.1)
        assert gs.phase == GamePhase.PLAYING
        assert gs.score == 500  # score persists across levels
