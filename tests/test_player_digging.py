"""Tests for the player digging action."""

from __future__ import annotations

import pygame

import constants as C
from level import Level
from player import Player, PlayerState


def _make_level(
    grid_patch: dict[tuple[int, int], int], player_col: int = 0, player_row: int = 0
) -> Level:
    grid = [[C.EMPTY] * C.GRID_COLS for _ in range(C.GRID_ROWS)]
    for (col, row), tile in grid_patch.items():
        grid[row][col] = tile
    return Level(
        {
            "level": 1,
            "grid": grid,
            "player_spawn": {"col": player_col, "row": player_row},
            "enemy_spawns": [],
            "escape_ladder_cols": [],
        }
    )


def _floor_level(floor_row: int = 10, player_col: int = 5, player_row: int = 9) -> Level:
    patch = {(c, floor_row): C.DIGGABLE_BRICK for c in range(C.GRID_COLS)}
    return _make_level(patch, player_col, player_row)


def _keydown(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": 0, "unicode": ""})


class TestDigLeft:
    def test_dig_left_creates_hole(self):
        """Player at (5,9), floor of DIGGABLE_BRICK at row 10. Dig left -> hole at (4,10)."""
        level = _floor_level(floor_row=10, player_col=5, player_row=9)
        p = Player(5, 9)
        p.handle_event(_keydown(C.KEY_DIG_LEFT))
        p.update(1 / 60, level)
        assert level.get_tile(4, 10) == C.HOLE_OPEN

    def test_dig_left_alt_key(self):
        level = _floor_level(floor_row=10, player_col=5, player_row=9)
        p = Player(5, 9)
        p.handle_event(_keydown(C.KEY_ALT_DIG_LEFT))
        p.update(1 / 60, level)
        assert level.get_tile(4, 10) == C.HOLE_OPEN


class TestDigRight:
    def test_dig_right_creates_hole(self):
        """Player at (5,9), floor of DIGGABLE_BRICK at row 10. Dig right -> hole at (6,10)."""
        level = _floor_level(floor_row=10, player_col=5, player_row=9)
        p = Player(5, 9)
        p.handle_event(_keydown(C.KEY_DIG_RIGHT))
        p.update(1 / 60, level)
        assert level.get_tile(6, 10) == C.HOLE_OPEN

    def test_dig_right_alt_key(self):
        level = _floor_level(floor_row=10, player_col=5, player_row=9)
        p = Player(5, 9)
        p.handle_event(_keydown(C.KEY_ALT_DIG_RIGHT))
        p.update(1 / 60, level)
        assert level.get_tile(6, 10) == C.HOLE_OPEN


class TestDigConstraints:
    def test_cannot_dig_solid_brick(self):
        """Solid brick below-left should not be dug."""
        patch = {(c, 10): C.SOLID_BRICK for c in range(C.GRID_COLS)}
        level = _make_level(patch)
        p = Player(5, 9)
        p.handle_event(_keydown(C.KEY_DIG_LEFT))
        p.update(1 / 60, level)
        assert level.get_tile(4, 10) == C.SOLID_BRICK

    def test_cannot_dig_while_falling(self):
        """Player in free-fall cannot dig."""
        level = _make_level({(4, 10): C.DIGGABLE_BRICK})  # no floor under player
        p = Player(5, 5)
        p.state = PlayerState.FALLING
        p.handle_event(_keydown(C.KEY_DIG_LEFT))
        p.update(1 / 60, level)
        # Tile should remain unchanged (may not even be at row 10 yet)
        assert level.get_tile(4, 10) == C.DIGGABLE_BRICK

    def test_cannot_dig_while_on_rope(self):
        """Player on a rope cannot dig."""
        patch = {(5, 5): C.ROPE, (4, 6): C.DIGGABLE_BRICK}
        level = _make_level(patch)
        p = Player(5, 5)
        p.handle_event(_keydown(C.KEY_DIG_LEFT))
        p.update(1 / 60, level)
        assert level.get_tile(4, 6) == C.DIGGABLE_BRICK

    def test_cannot_dig_while_dead(self):
        level = _floor_level(floor_row=10, player_col=5, player_row=9)
        p = Player(5, 9)
        p.kill()
        p.handle_event(_keydown(C.KEY_DIG_LEFT))
        p.update(1 / 60, level)
        assert level.get_tile(4, 10) == C.DIGGABLE_BRICK

    def test_cannot_dig_empty_below(self):
        """If there's nothing below-left, dig does nothing."""
        patch = {(c, 10): C.DIGGABLE_BRICK for c in range(C.GRID_COLS)}
        patch[(4, 10)] = C.EMPTY  # gap where dig target would be
        level = _make_level(patch)
        p = Player(5, 9)
        p.handle_event(_keydown(C.KEY_DIG_LEFT))
        p.update(1 / 60, level)
        assert level.get_tile(4, 10) == C.EMPTY

    def test_dig_is_one_shot(self):
        """A single dig key press digs once; holding does not continuously dig."""
        level = _floor_level(floor_row=10, player_col=5, player_row=9)
        p = Player(5, 9)
        p.handle_event(_keydown(C.KEY_DIG_LEFT))
        p.update(1 / 60, level)
        assert level.get_tile(4, 10) == C.HOLE_OPEN
        # Second frame without new keypress should NOT dig again
        p.update(1 / 60, level)
        # (3, 10) should be unaffected
        assert level.get_tile(3, 10) == C.DIGGABLE_BRICK

    def test_can_dig_while_climbing_ladder(self):
        """Player on a ladder CAN dig."""
        patch = {(5, 9): C.LADDER}
        for c in range(C.GRID_COLS):
            patch[(c, 10)] = C.DIGGABLE_BRICK
        level = _make_level(patch)
        p = Player(5, 9)
        p.handle_event(_keydown(C.KEY_DIG_LEFT))
        p.update(1 / 60, level)
        assert level.get_tile(4, 10) == C.HOLE_OPEN
