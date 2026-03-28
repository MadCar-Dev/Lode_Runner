"""Unit tests for level.py — Level class."""

import pytest

import constants as C

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_LEVEL_DATA = {
    "level": 1,
    "grid": [
        [C.EMPTY] * C.GRID_COLS for _ in range(C.GRID_ROWS - 1)
    ] + [[C.SOLID_BRICK] * C.GRID_COLS],  # solid bottom row
    "player_spawn": {"col": 1, "row": 14},
    "enemy_spawns": [{"col": 26, "row": 0}],
    "escape_ladder_cols": [13],
}

# Add one of every tile type so tests can reference them
FULL_TILE_DATA = {
    "level": 2,
    "grid": [[C.EMPTY] * C.GRID_COLS for _ in range(C.GRID_ROWS)],
    "player_spawn": {"col": 0, "row": 0},
    "enemy_spawns": [],
    "escape_ladder_cols": [],
}
# Manually place specific tiles for targeted tests
_full_grid = [row[:] for row in FULL_TILE_DATA["grid"]]
_full_grid[0][0] = C.EMPTY
_full_grid[0][1] = C.DIGGABLE_BRICK
_full_grid[0][2] = C.SOLID_BRICK
_full_grid[0][3] = C.LADDER
_full_grid[0][4] = C.ROPE
_full_grid[0][5] = C.GOLD
_full_grid[0][6] = C.HIDDEN_LADDER
_full_grid[0][7] = C.FALSE_BRICK
_full_grid[0][8] = C.HOLE_OPEN
_full_grid[0][9] = C.HOLE_FILLING
_full_grid[1][0] = C.GOLD   # second gold for multi-gold tests
_full_grid[1][6] = C.HIDDEN_LADDER  # second hidden ladder tile (same col as [0][6])
FULL_TILE_DATA["grid"] = _full_grid
FULL_TILE_DATA["escape_ladder_cols"] = [6]


@pytest.fixture
def minimal_level():
    from level import Level
    return Level(MINIMAL_LEVEL_DATA)


@pytest.fixture
def full_tile_level():
    from level import Level
    return Level(FULL_TILE_DATA)


# ---------------------------------------------------------------------------
# Construction and loading
# ---------------------------------------------------------------------------

class TestLevelConstruction:
    def test_level_number(self, minimal_level):
        assert minimal_level.number == 1

    def test_player_spawn(self, minimal_level):
        assert minimal_level.player_spawn.col == 1
        assert minimal_level.player_spawn.row == 14

    def test_enemy_spawns(self, minimal_level):
        assert len(minimal_level.enemy_spawns) == 1
        assert minimal_level.enemy_spawns[0].col == 26
        assert minimal_level.enemy_spawns[0].row == 0

    def test_escape_ladder_cols(self, minimal_level):
        assert minimal_level.escape_ladder_cols == [13]

    def test_grid_dimensions(self, minimal_level):
        # grid is 16 rows x 28 cols
        assert len(minimal_level._grid) == C.GRID_ROWS
        assert all(len(row) == C.GRID_COLS for row in minimal_level._grid)

    def test_from_file_round_trip(self, tmp_path, minimal_level):
        from level import Level
        path = tmp_path / "test_level.json"
        minimal_level.to_file(path)
        loaded = Level.from_file(path)
        assert loaded.number == minimal_level.number
        assert loaded.player_spawn == minimal_level.player_spawn
        assert loaded.enemy_spawns == minimal_level.enemy_spawns
        assert loaded._grid == minimal_level._grid

    def test_construction_does_not_mutate_input(self):
        from level import Level
        data = {
            "level": 1,
            "grid": [[C.EMPTY] * C.GRID_COLS for _ in range(C.GRID_ROWS)],
            "player_spawn": {"col": 0, "row": 0},
            "enemy_spawns": [],
            "escape_ladder_cols": [],
        }
        level = Level(data)
        level.set_tile(0, 0, C.GOLD)
        # Original data must not be mutated
        assert data["grid"][0][0] == C.EMPTY


# ---------------------------------------------------------------------------
# get_tile
# ---------------------------------------------------------------------------

class TestGetTile:
    def test_get_tile_empty(self, full_tile_level):
        assert full_tile_level.get_tile(0, 0) == C.EMPTY

    def test_get_tile_diggable_brick(self, full_tile_level):
        assert full_tile_level.get_tile(1, 0) == C.DIGGABLE_BRICK

    def test_get_tile_solid_brick(self, full_tile_level):
        assert full_tile_level.get_tile(2, 0) == C.SOLID_BRICK

    def test_get_tile_ladder(self, full_tile_level):
        assert full_tile_level.get_tile(3, 0) == C.LADDER

    def test_get_tile_rope(self, full_tile_level):
        assert full_tile_level.get_tile(4, 0) == C.ROPE

    def test_get_tile_gold(self, full_tile_level):
        assert full_tile_level.get_tile(5, 0) == C.GOLD

    def test_get_tile_hidden_ladder(self, full_tile_level):
        assert full_tile_level.get_tile(6, 0) == C.HIDDEN_LADDER

    def test_get_tile_false_brick(self, full_tile_level):
        assert full_tile_level.get_tile(7, 0) == C.FALSE_BRICK

    def test_get_tile_hole_open(self, full_tile_level):
        assert full_tile_level.get_tile(8, 0) == C.HOLE_OPEN

    def test_get_tile_hole_filling(self, full_tile_level):
        assert full_tile_level.get_tile(9, 0) == C.HOLE_FILLING

    def test_out_of_bounds_left(self, minimal_level):
        assert minimal_level.get_tile(-1, 0) == C.SOLID_BRICK

    def test_out_of_bounds_right(self, minimal_level):
        assert minimal_level.get_tile(C.GRID_COLS, 0) == C.SOLID_BRICK

    def test_out_of_bounds_top(self, minimal_level):
        assert minimal_level.get_tile(0, -1) == C.SOLID_BRICK

    def test_out_of_bounds_bottom(self, minimal_level):
        assert minimal_level.get_tile(0, C.GRID_ROWS) == C.SOLID_BRICK


# ---------------------------------------------------------------------------
# set_tile
# ---------------------------------------------------------------------------

class TestSetTile:
    def test_set_tile_basic(self, minimal_level):
        minimal_level.set_tile(5, 5, C.GOLD)
        assert minimal_level.get_tile(5, 5) == C.GOLD

    def test_set_tile_out_of_bounds_ignored(self, minimal_level):
        # Should not raise; out-of-bounds writes are silently ignored
        minimal_level.set_tile(-1, 0, C.GOLD)
        minimal_level.set_tile(C.GRID_COLS, 0, C.GOLD)
        minimal_level.set_tile(0, -1, C.GOLD)
        minimal_level.set_tile(0, C.GRID_ROWS, C.GOLD)

    def test_set_tile_overwrites(self, full_tile_level):
        full_tile_level.set_tile(1, 0, C.EMPTY)
        assert full_tile_level.get_tile(1, 0) == C.EMPTY


# ---------------------------------------------------------------------------
# Tile property predicates
# ---------------------------------------------------------------------------

class TestTilePredicates:
    def test_is_solid_diggable_brick(self, full_tile_level):
        assert full_tile_level.is_solid(1, 0) is True

    def test_is_solid_solid_brick(self, full_tile_level):
        assert full_tile_level.is_solid(2, 0) is True

    def test_is_solid_empty(self, full_tile_level):
        assert full_tile_level.is_solid(0, 0) is False

    def test_is_solid_ladder(self, full_tile_level):
        assert full_tile_level.is_solid(3, 0) is False

    def test_is_solid_false_brick_is_passable(self, full_tile_level):
        # False bricks look solid but entities fall through — NOT solid for physics
        assert full_tile_level.is_solid(7, 0) is False

    def test_is_standable_diggable_brick(self, full_tile_level):
        assert full_tile_level.is_standable(1, 0) is True

    def test_is_standable_solid_brick(self, full_tile_level):
        assert full_tile_level.is_standable(2, 0) is True

    def test_is_standable_empty(self, full_tile_level):
        assert full_tile_level.is_standable(0, 0) is False

    def test_is_standable_false_brick(self, full_tile_level):
        assert full_tile_level.is_standable(7, 0) is False

    def test_is_diggable_diggable_brick(self, full_tile_level):
        assert full_tile_level.is_diggable(1, 0) is True

    def test_is_diggable_solid_brick(self, full_tile_level):
        assert full_tile_level.is_diggable(2, 0) is False

    def test_is_diggable_empty(self, full_tile_level):
        assert full_tile_level.is_diggable(0, 0) is False

    def test_is_ladder_ladder(self, full_tile_level):
        assert full_tile_level.is_ladder(3, 0) is True

    def test_is_ladder_empty(self, full_tile_level):
        assert full_tile_level.is_ladder(0, 0) is False

    def test_is_rope_rope(self, full_tile_level):
        assert full_tile_level.is_rope(4, 0) is True

    def test_is_rope_ladder(self, full_tile_level):
        assert full_tile_level.is_rope(3, 0) is False

    def test_is_passable_empty(self, full_tile_level):
        assert full_tile_level.is_passable(0, 0) is True

    def test_is_passable_solid_brick(self, full_tile_level):
        assert full_tile_level.is_passable(2, 0) is False

    def test_is_passable_diggable_brick(self, full_tile_level):
        assert full_tile_level.is_passable(1, 0) is False

    def test_is_passable_hole_open(self, full_tile_level):
        assert full_tile_level.is_passable(8, 0) is True

    def test_is_passable_false_brick(self, full_tile_level):
        assert full_tile_level.is_passable(7, 0) is True

    def test_is_passable_hole_filling(self, full_tile_level):
        assert full_tile_level.is_passable(9, 0) is False

    def test_is_passable_hidden_ladder(self, full_tile_level):
        assert full_tile_level.is_passable(6, 0) is True


# ---------------------------------------------------------------------------
# Gold tracking
# ---------------------------------------------------------------------------

class TestGoldPositions:
    def test_gold_positions_returns_all_gold(self, full_tile_level):
        positions = full_tile_level.gold_positions()
        assert (5, 0) in positions
        assert (0, 1) in positions
        assert len(positions) == 2

    def test_gold_positions_empty_when_no_gold(self, minimal_level):
        positions = minimal_level.gold_positions()
        assert positions == []

    def test_gold_positions_updates_after_set_tile(self, full_tile_level):
        # Remove a gold piece
        full_tile_level.set_tile(5, 0, C.EMPTY)
        positions = full_tile_level.gold_positions()
        assert (5, 0) not in positions
        assert len(positions) == 1


# ---------------------------------------------------------------------------
# Escape ladder
# ---------------------------------------------------------------------------

class TestEscapeLadder:
    def test_hidden_ladder_not_visible_before_reveal(self, full_tile_level):
        assert full_tile_level.get_tile(6, 0) == C.HIDDEN_LADDER

    def test_reveal_escape_ladder_converts_hidden_to_ladder(self, full_tile_level):
        full_tile_level.reveal_escape_ladder()
        assert full_tile_level.get_tile(6, 0) == C.LADDER
        assert full_tile_level.get_tile(6, 1) == C.LADDER

    def test_reveal_escape_ladder_only_affects_escape_cols(self, full_tile_level):
        # Col 3 has a regular ladder — should remain LADDER, not be changed
        full_tile_level.reveal_escape_ladder()
        assert full_tile_level.get_tile(3, 0) == C.LADDER  # unchanged

    def test_reveal_escape_ladder_idempotent(self, full_tile_level):
        full_tile_level.reveal_escape_ladder()
        full_tile_level.reveal_escape_ladder()  # calling twice is safe
        assert full_tile_level.get_tile(6, 0) == C.LADDER
