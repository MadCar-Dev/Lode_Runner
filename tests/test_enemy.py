"""Tests for the Enemy class — state machine, physics, AI, gold carrying, respawn."""

from __future__ import annotations

import constants as C
from enemy import Enemy, EnemyState
from level import Level
from player import Player


def _make_level(
    grid_patch: dict[tuple[int, int], int] | None = None,
    enemy_spawns: list[dict] | None = None,
) -> Level:
    grid = [[C.EMPTY] * C.GRID_COLS for _ in range(C.GRID_ROWS)]
    if grid_patch:
        for (col, row), tile in grid_patch.items():
            grid[row][col] = tile
    return Level(
        {
            "level": 1,
            "grid": grid,
            "player_spawn": {"col": 0, "row": 0},
            "enemy_spawns": enemy_spawns or [{"col": 10, "row": 0}],
            "escape_ladder_cols": [],
        }
    )


def _floor_level(
    floor_row: int = 14,
    extra_patch: dict[tuple[int, int], int] | None = None,
) -> Level:
    patch = {(c, floor_row): C.SOLID_BRICK for c in range(C.GRID_COLS)}
    if extra_patch:
        patch.update(extra_patch)
    return _make_level(patch)


class TestEnemyInit:
    def test_position_pixels(self):
        e = Enemy(10, 5)
        assert e.x == 10 * C.TILE_SIZE
        assert e.y == 5 * C.TILE_SIZE

    def test_col_row_properties(self):
        e = Enemy(10, 5)
        assert e.col == 10
        assert e.row == 5

    def test_initial_state_idle(self):
        e = Enemy(10, 5)
        assert e.state == EnemyState.IDLE

    def test_spawn_stored(self):
        e = Enemy(10, 5)
        assert e._spawn_col == 10
        assert e._spawn_row == 5

    def test_no_gold_initially(self):
        e = Enemy(10, 5)
        assert e.has_gold is False


class TestEnemyGravity:
    def test_enemy_falls_when_unsupported(self):
        level = _make_level()  # all empty
        player = Player(0, 0)
        e = Enemy(10, 5)
        initial_y = e.y
        e.update(1 / 60, level, player)
        assert e.y > initial_y
        assert e.state == EnemyState.FALLING

    def test_enemy_lands_on_floor(self):
        level = _floor_level(floor_row=14)
        player = Player(0, 13)
        e = Enemy(10, 5)
        for _ in range(200):
            e.update(1 / 60, level, player)
            if e.state != EnemyState.FALLING:
                break
        assert e.row == 13
        assert e.state != EnemyState.FALLING


class TestEnemyChase:
    def test_chases_player_left(self):
        level = _floor_level(floor_row=14)
        player = Player(3, 13)
        e = Enemy(10, 13)
        initial_x = e.x
        e.update(1 / 60, level, player)
        assert e.x < initial_x
        assert e.state == EnemyState.RUNNING_LEFT

    def test_chases_player_right(self):
        level = _floor_level(floor_row=14)
        player = Player(20, 13)
        e = Enemy(10, 13)
        initial_x = e.x
        e.update(1 / 60, level, player)
        assert e.x > initial_x
        assert e.state == EnemyState.RUNNING_RIGHT

    def test_idle_at_same_column(self):
        level = _floor_level(floor_row=14)
        player = Player(10, 13)
        e = Enemy(10, 13)
        e.update(1 / 60, level, player)
        # Same col, same row -> should be idle (no movement needed)
        assert e.state == EnemyState.IDLE

    def test_blocked_by_wall(self):
        patch = {(c, 14): C.SOLID_BRICK for c in range(C.GRID_COLS)}
        patch[(9, 13)] = C.SOLID_BRICK  # wall to the left of enemy
        level = _make_level(patch)
        player = Player(3, 13)
        e = Enemy(10, 13)
        for _ in range(100):
            e.update(1 / 60, level, player)
        # Should not pass through wall
        assert e.col >= 10 or e.col == 10  # blocked, needs ladder


class TestEnemyLadder:
    def test_climbs_up_toward_player(self):
        """Enemy climbs ladder when player is above."""
        patch = {(c, 14): C.SOLID_BRICK for c in range(C.GRID_COLS)}
        for r in range(8, 14):
            patch[(10, r)] = C.LADDER
        level = _make_level(patch)
        player = Player(10, 5)
        e = Enemy(10, 13)
        initial_y = e.y
        e.update(1 / 60, level, player)
        assert e.y < initial_y

    def test_climbs_down_toward_player(self):
        """Enemy climbs ladder when player is below."""
        patch = {(c, 14): C.SOLID_BRICK for c in range(C.GRID_COLS)}
        for r in range(5, 14):
            patch[(10, r)] = C.LADDER
        level = _make_level(patch)
        player = Player(10, 13)
        e = Enemy(10, 5)
        initial_y = e.y
        e.update(1 / 60, level, player)
        assert e.y > initial_y


class TestEnemyTrapping:
    def test_enemy_becomes_trapped_in_hole(self):
        """Enemy on a HOLE_OPEN tile transitions to TRAPPED."""
        patch = {(c, 14): C.DIGGABLE_BRICK for c in range(C.GRID_COLS)}
        patch.update({(c, 15): C.SOLID_BRICK for c in range(C.GRID_COLS)})
        level = _make_level(patch)
        level.dig_hole(10, 14)  # open hole at (10, 14)
        player = Player(0, 13)
        e = Enemy(10, 13)
        # Enemy should fall into the hole
        for _ in range(60):
            e.update(1 / 60, level, player)
            if e.state == EnemyState.TRAPPED:
                break
        assert e.state == EnemyState.TRAPPED

    def test_trapped_enemy_escapes_after_timeout(self):
        """After ENEMY_ESCAPE_TIME, trapped enemy climbs out."""
        patch = {(c, 14): C.DIGGABLE_BRICK for c in range(C.GRID_COLS)}
        patch.update({(c, 15): C.SOLID_BRICK for c in range(C.GRID_COLS)})
        level = _make_level(patch)
        level.dig_hole(10, 14)
        player = Player(0, 0)
        e = Enemy(10, 13)
        # Fall into hole
        for _ in range(60):
            e.update(1 / 60, level, player)
            if e.state == EnemyState.TRAPPED:
                break
        assert e.state == EnemyState.TRAPPED
        # Now advance time past escape threshold
        for _ in range(int(C.ENEMY_ESCAPE_TIME * 60) + 10):
            e.update(1 / 60, level, player)
            if e.state != EnemyState.TRAPPED:
                break
        assert e.state != EnemyState.TRAPPED

    def test_enemy_dies_when_hole_closes(self):
        """If hole fills while enemy is trapped, enemy dies."""
        patch = {(c, 14): C.DIGGABLE_BRICK for c in range(C.GRID_COLS)}
        patch.update({(c, 15): C.SOLID_BRICK for c in range(C.GRID_COLS)})
        level = _make_level(patch)
        level.dig_hole(10, 14)
        player = Player(0, 0)
        e = Enemy(10, 13)
        # Fall into hole
        for _ in range(60):
            e.update(1 / 60, level, player)
            if e.state == EnemyState.TRAPPED:
                break
        assert e.state == EnemyState.TRAPPED
        # Advance hole past its full lifecycle so it closes to DIGGABLE_BRICK
        level.update_holes(C.HOLE_OPEN_DURATION + C.HOLE_FILL_DURATION + 0.1)
        e.update(1 / 60, level, player)
        assert e.state == EnemyState.DEAD

    def test_enemy_dies_on_hole_filling_state(self):
        """Enemy dies when hole enters HOLE_FILLING state, not just when fully closed."""
        patch = {(c, 14): C.DIGGABLE_BRICK for c in range(C.GRID_COLS)}
        patch.update({(c, 15): C.SOLID_BRICK for c in range(C.GRID_COLS)})
        level = _make_level(patch)
        level.dig_hole(10, 14)
        player = Player(0, 0)
        e = Enemy(10, 13)
        # Fall into hole
        for _ in range(60):
            e.update(1 / 60, level, player)
            if e.state == EnemyState.TRAPPED:
                break
        assert e.state == EnemyState.TRAPPED
        # Advance hole to HOLE_FILLING only (not fully closed)
        level.update_holes(C.HOLE_OPEN_DURATION + 0.1)
        assert level.get_tile(10, 14) == C.HOLE_FILLING
        e.update(1 / 60, level, player)
        assert e.state == EnemyState.DEAD


class TestEnemyRespawn:
    def test_dead_enemy_respawns_at_spawn_position(self):
        """Dead enemy respawns at row 0 of its spawn column after delay."""
        patch = {(c, 14): C.SOLID_BRICK for c in range(C.GRID_COLS)}
        level = _make_level(patch)
        player = Player(0, 13)
        e = Enemy(10, 13)
        e.state = EnemyState.DEAD
        e._respawn_timer = 0.0
        # Tick past respawn delay
        for _ in range(int(C.ENEMY_RESPAWN_DELAY * 60) + 60):
            e.update(1 / 60, level, player)
            if e.state != EnemyState.DEAD:
                break
        # Should have respawned
        assert e.state != EnemyState.DEAD
        assert e.col == 10  # spawn column


class TestEnemyGold:
    def test_enemy_picks_up_gold(self):
        """Enemy stepping on a GOLD tile picks it up."""
        patch = {(c, 14): C.SOLID_BRICK for c in range(C.GRID_COLS)}
        patch[(9, 13)] = C.GOLD
        level = _make_level(patch)
        player = Player(0, 13)
        e = Enemy(10, 13)
        # Chase player left, stepping on gold at (9, 13)
        for _ in range(120):
            e.update(1 / 60, level, player)
            if e.col <= 9:
                break
        assert e.has_gold is True
        assert level.get_tile(9, 13) == C.EMPTY

    def test_enemy_drops_gold_on_death(self):
        """When enemy dies, gold is dropped at its position."""
        patch = {(c, 14): C.SOLID_BRICK for c in range(C.GRID_COLS)}
        level = _make_level(patch)
        e = Enemy(10, 13)
        e.has_gold = True
        e.die(level)
        assert e.has_gold is False
        assert level.get_tile(10, 13) == C.GOLD

    def test_enemy_die_is_public(self):
        """enemy.die() (public) kills the enemy and drops gold."""
        patch = {(c, 14): C.SOLID_BRICK for c in range(C.GRID_COLS)}
        level = _make_level(patch)
        e = Enemy(10, 13)
        e.has_gold = True
        e.die(level)  # public method — not _die
        assert e.state == EnemyState.DEAD
        assert e.has_gold is False
        assert level.get_tile(10, 13) == C.GOLD

    def test_enemy_only_carries_one_gold(self):
        """Enemy with gold does not pick up a second gold tile."""
        patch = {(c, 14): C.SOLID_BRICK for c in range(C.GRID_COLS)}
        patch[(8, 13)] = C.GOLD
        patch[(9, 13)] = C.GOLD
        level = _make_level(patch)
        player = Player(0, 13)
        e = Enemy(10, 13)
        for _ in range(200):
            e.update(1 / 60, level, player)
            if e.col <= 7:
                break
        assert e.has_gold is True
        # One gold should still be on the ground (the one not picked up)
        remaining = level.gold_positions()
        assert len(remaining) >= 1


class TestCarryingGold:
    def test_enemy_has_carrying_gold_attr(self):
        e = Enemy(5, 5)
        assert hasattr(e, "carrying_gold")
        assert e.carrying_gold is False
