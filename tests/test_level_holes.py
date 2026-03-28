"""Tests for the hole lifecycle in level.py."""

from __future__ import annotations

import constants as C
from level import Level


def _make_level(grid_patch: dict[tuple[int, int], int] | None = None) -> Level:
    """Build a Level with an optional tile patch dict."""
    grid = [[C.EMPTY] * C.GRID_COLS for _ in range(C.GRID_ROWS)]
    if grid_patch:
        for (col, row), tile in grid_patch.items():
            grid[row][col] = tile
    return Level(
        {
            "level": 1,
            "grid": grid,
            "player_spawn": {"col": 0, "row": 0},
            "enemy_spawns": [],
            "escape_ladder_cols": [],
        }
    )


class TestDigHole:
    def test_dig_converts_diggable_to_hole_open(self):
        level = _make_level({(5, 10): C.DIGGABLE_BRICK})
        result = level.dig_hole(5, 10)
        assert result is True
        assert level.get_tile(5, 10) == C.HOLE_OPEN

    def test_dig_fails_on_solid_brick(self):
        level = _make_level({(5, 10): C.SOLID_BRICK})
        result = level.dig_hole(5, 10)
        assert result is False
        assert level.get_tile(5, 10) == C.SOLID_BRICK

    def test_dig_fails_on_empty(self):
        level = _make_level()
        result = level.dig_hole(5, 10)
        assert result is False

    def test_dig_fails_on_already_open_hole(self):
        level = _make_level({(5, 10): C.DIGGABLE_BRICK})
        level.dig_hole(5, 10)
        result = level.dig_hole(5, 10)
        assert result is False

    def test_dig_fails_out_of_bounds(self):
        level = _make_level()
        result = level.dig_hole(-1, 0)
        assert result is False

    def test_dig_records_hole_in_internal_dict(self):
        level = _make_level({(5, 10): C.DIGGABLE_BRICK})
        level.dig_hole(5, 10)
        assert (5, 10) in level._holes


class TestUpdateHoles:
    def test_hole_stays_open_within_duration(self):
        level = _make_level({(5, 10): C.DIGGABLE_BRICK})
        level.dig_hole(5, 10)
        level.update_holes(C.HOLE_OPEN_DURATION - 0.1)
        assert level.get_tile(5, 10) == C.HOLE_OPEN

    def test_hole_transitions_to_filling(self):
        level = _make_level({(5, 10): C.DIGGABLE_BRICK})
        level.dig_hole(5, 10)
        level.update_holes(C.HOLE_OPEN_DURATION + 0.01)
        assert level.get_tile(5, 10) == C.HOLE_FILLING

    def test_hole_transitions_back_to_brick(self):
        level = _make_level({(5, 10): C.DIGGABLE_BRICK})
        level.dig_hole(5, 10)
        # Advance past open + fill durations
        level.update_holes(C.HOLE_OPEN_DURATION + C.HOLE_FILL_DURATION + 0.01)
        assert level.get_tile(5, 10) == C.DIGGABLE_BRICK
        assert (5, 10) not in level._holes

    def test_incremental_updates_work(self):
        """Calling update_holes many times with small dt works the same as one big call."""
        level = _make_level({(5, 10): C.DIGGABLE_BRICK})
        level.dig_hole(5, 10)
        # 100 small steps totalling just past HOLE_OPEN_DURATION
        for _ in range(100):
            level.update_holes(C.HOLE_OPEN_DURATION / 100 + 0.001)
        assert level.get_tile(5, 10) == C.HOLE_FILLING

    def test_multiple_holes_independent(self):
        level = _make_level({(3, 10): C.DIGGABLE_BRICK, (7, 10): C.DIGGABLE_BRICK})
        level.dig_hole(3, 10)
        level.update_holes(C.HOLE_OPEN_DURATION / 2)
        level.dig_hole(7, 10)  # dug later
        level.update_holes(C.HOLE_OPEN_DURATION / 2 + 0.01)
        # First hole has elapsed HOLE_OPEN_DURATION + 0.01 -> FILLING
        assert level.get_tile(3, 10) == C.HOLE_FILLING
        # Second hole has only elapsed HOLE_OPEN_DURATION/2 + 0.01 -> still OPEN
        assert level.get_tile(7, 10) == C.HOLE_OPEN


class TestGetHoleProgress:
    def test_returns_zero_for_non_hole(self):
        level = _make_level()
        assert level.get_hole_progress(5, 10) == 0.0

    def test_returns_zero_for_just_opened(self):
        level = _make_level({(5, 10): C.DIGGABLE_BRICK})
        level.dig_hole(5, 10)
        assert level.get_hole_progress(5, 10) == 0.0

    def test_returns_zero_during_open_phase(self):
        level = _make_level({(5, 10): C.DIGGABLE_BRICK})
        level.dig_hole(5, 10)
        level.update_holes(C.HOLE_OPEN_DURATION / 2)
        assert level.get_hole_progress(5, 10) == 0.0

    def test_returns_midpoint_during_filling(self):
        level = _make_level({(5, 10): C.DIGGABLE_BRICK})
        level.dig_hole(5, 10)
        level.update_holes(C.HOLE_OPEN_DURATION + C.HOLE_FILL_DURATION / 2)
        progress = level.get_hole_progress(5, 10)
        assert 0.4 < progress < 0.6  # approximately 0.5

    def test_returns_near_one_at_end_of_filling(self):
        level = _make_level({(5, 10): C.DIGGABLE_BRICK})
        level.dig_hole(5, 10)
        level.update_holes(C.HOLE_OPEN_DURATION + C.HOLE_FILL_DURATION - 0.01)
        progress = level.get_hole_progress(5, 10)
        assert progress > 0.9
