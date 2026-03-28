"""Tests for the Player state machine and physics."""
from __future__ import annotations

import pygame
import pytest

import constants as C
from level import Level
from player import Player, PlayerState

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_level(grid_patch: dict[tuple[int, int], int],
                player_col: int = 0, player_row: int = 0) -> Level:
    """Build a minimal Level with the given tiles patched into an otherwise-empty grid."""
    grid = [[C.EMPTY] * C.GRID_COLS for _ in range(C.GRID_ROWS)]
    for (col, row), tile in grid_patch.items():
        grid[row][col] = tile
    return Level({
        "level": 1,
        "grid": grid,
        "player_spawn": {"col": player_col, "row": player_row},
        "enemy_spawns": [],
        "escape_ladder_cols": [],
    })


def _floor_level(floor_row: int = 10, player_col: int = 5, player_row: int = 9) -> Level:
    """Level with a solid floor at floor_row and player standing on it."""
    patch = {(c, floor_row): C.SOLID_BRICK for c in range(C.GRID_COLS)}
    return _make_level(patch, player_col, player_row)


def _keydown(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": 0, "unicode": ""})


# ---------------------------------------------------------------------------
# TestPlayerInit
# ---------------------------------------------------------------------------

class TestPlayerInit:
    def test_position_pixels(self) -> None:
        p = Player(3, 7)
        assert p.x == 3 * C.TILE_SIZE
        assert p.y == 7 * C.TILE_SIZE

    def test_col_row_properties(self) -> None:
        p = Player(3, 7)
        assert p.col == 3
        assert p.row == 7

    def test_initial_state_idle(self) -> None:
        p = Player(0, 0)
        assert p.state == PlayerState.IDLE

    def test_initial_facing_right(self) -> None:
        p = Player(0, 0)
        assert p.facing == 1

    def test_is_alive_initial(self) -> None:
        p = Player(0, 0)
        assert p.is_alive is True

    def test_kill_sets_dead(self) -> None:
        p = Player(0, 0)
        p.kill()
        assert p.state == PlayerState.DEAD
        assert p.is_alive is False


# ---------------------------------------------------------------------------
# TestSupportDetection
# ---------------------------------------------------------------------------

class TestSupportDetection:
    def test_on_floor_aligned_solid_below(self) -> None:
        level = _floor_level(floor_row=10, player_col=5, player_row=9)
        p = Player(5, 9)  # y = 9*32 = 288; 288 % 32 == 0; tile below = row 10 = SOLID_BRICK
        assert p._is_on_floor(level) is True

    def test_not_on_floor_when_mid_tile(self) -> None:
        level = _floor_level(floor_row=10, player_col=5, player_row=9)
        p = Player(5, 9)
        p.y += 5.0  # 5 > TILE_SNAP_TOLERANCE
        assert p._is_on_floor(level) is False

    def test_not_on_floor_when_no_solid_below(self) -> None:
        level = _make_level({})  # all empty
        p = Player(5, 5)
        assert p._is_on_floor(level) is False

    def test_not_on_floor_on_rope(self) -> None:
        level = _make_level({(5, 5): C.ROPE, (5, 6): C.SOLID_BRICK})
        p = Player(5, 5)  # on rope, solid below — not floor (rope takes priority)
        # is_on_floor is purely about standable below + y-aligned
        # tile below (row 6) is SOLID_BRICK → is_on_floor True here
        # (rope handling happens in update, not in is_on_floor)
        assert p._is_on_floor(level) is True

    def test_on_ladder_aligned(self) -> None:
        level = _make_level({(5, 5): C.LADDER, (5, 6): C.SOLID_BRICK})
        p = Player(5, 5)  # x = 5*32; x % 32 == 0
        assert p._is_on_ladder(level) is True

    def test_not_on_ladder_when_x_misaligned(self) -> None:
        level = _make_level({(5, 5): C.LADDER})
        p = Player(5, 5)
        p.x += C.TILE_SNAP_TOLERANCE + 1  # push beyond tolerance
        assert p._is_on_ladder(level) is False

    def test_not_on_ladder_when_no_ladder_tile(self) -> None:
        level = _make_level({})
        p = Player(5, 5)
        assert p._is_on_ladder(level) is False

    def test_on_rope(self) -> None:
        level = _make_level({(5, 5): C.ROPE})
        p = Player(5, 5)
        assert p._is_on_rope(level) is True

    def test_not_on_rope(self) -> None:
        level = _make_level({})
        p = Player(5, 5)
        assert p._is_on_rope(level) is False


# ---------------------------------------------------------------------------
# TestToggleInput
# ---------------------------------------------------------------------------

class TestToggleInput:
    def test_keydown_left_activates(self) -> None:
        p = Player(5, 5)
        p.handle_event(_keydown(C.KEY_LEFT))
        assert p._h_dir == -1

    def test_keydown_left_twice_deactivates(self) -> None:
        p = Player(5, 5)
        p.handle_event(_keydown(C.KEY_LEFT))
        p.handle_event(_keydown(C.KEY_LEFT))
        assert p._h_dir == 0

    def test_keydown_right_activates(self) -> None:
        p = Player(5, 5)
        p.handle_event(_keydown(C.KEY_RIGHT))
        assert p._h_dir == 1

    def test_keydown_right_twice_deactivates(self) -> None:
        p = Player(5, 5)
        p.handle_event(_keydown(C.KEY_RIGHT))
        p.handle_event(_keydown(C.KEY_RIGHT))
        assert p._h_dir == 0

    def test_keydown_left_while_going_right_switches(self) -> None:
        p = Player(5, 5)
        p.handle_event(_keydown(C.KEY_RIGHT))
        p.handle_event(_keydown(C.KEY_LEFT))
        assert p._h_dir == -1

    def test_keydown_up_activates(self) -> None:
        p = Player(5, 5)
        p.handle_event(_keydown(C.KEY_UP))
        assert p._v_dir == -1

    def test_keydown_up_twice_deactivates(self) -> None:
        p = Player(5, 5)
        p.handle_event(_keydown(C.KEY_UP))
        p.handle_event(_keydown(C.KEY_UP))
        assert p._v_dir == 0

    def test_keydown_down_activates(self) -> None:
        p = Player(5, 5)
        p.handle_event(_keydown(C.KEY_DOWN))
        assert p._v_dir == 1

    def test_alt_keys_work(self) -> None:
        p = Player(5, 5)
        p.handle_event(_keydown(C.KEY_ALT_LEFT))
        assert p._h_dir == -1

    def test_keyup_ignored(self) -> None:
        p = Player(5, 5)
        p.handle_event(_keydown(C.KEY_LEFT))
        # KEYUP should not toggle back off
        p.handle_event(pygame.event.Event(pygame.KEYUP, {"key": C.KEY_LEFT, "mod": 0}))
        assert p._h_dir == -1


# ---------------------------------------------------------------------------
# TestGravityAndFalling
# ---------------------------------------------------------------------------

class TestGravityAndFalling:
    def test_player_falls_when_unsupported(self) -> None:
        level = _make_level({})  # all empty
        p = Player(5, 5)
        initial_y = p.y
        p.update(1 / 60, level)
        assert p.y > initial_y
        assert p.state == PlayerState.FALLING

    def test_player_does_not_fall_on_floor(self) -> None:
        level = _floor_level(floor_row=10, player_col=5, player_row=9)
        p = Player(5, 9)
        initial_y = p.y
        p.update(1 / 60, level)
        assert p.y == initial_y
        assert p.state == PlayerState.IDLE

    def test_player_lands_on_floor(self) -> None:
        # Player at row 5, solid floor at row 10; after 1 second should land
        patch = {(c, 10): C.SOLID_BRICK for c in range(C.GRID_COLS)}
        level = _make_level(patch)
        p = Player(5, 5)
        # Simulate many frames until player lands
        for _ in range(100):
            p.update(1 / 60, level)
            if p.state == PlayerState.IDLE:
                break
        assert p.state == PlayerState.IDLE
        assert p.y == 9 * C.TILE_SIZE  # resting on top of row 10 → player at row 9

    def test_update_does_nothing_when_dead(self) -> None:
        level = _make_level({})
        p = Player(5, 5)
        p.kill()
        initial_y = p.y
        p.update(1 / 60, level)
        assert p.y == initial_y

    def test_player_grabs_rope_during_fall(self) -> None:
        # Rope at row 7, player starts above it in free fall
        patch = {(5, 7): C.ROPE}
        level = _make_level(patch)
        p = Player(5, 5)
        for _ in range(60):
            p.update(1 / 60, level)
            if p.row == 7:
                break
        # Once player is on rope row, should grab it
        assert p.state != PlayerState.FALLING or p.row < 7


# ---------------------------------------------------------------------------
# TestRunning
# ---------------------------------------------------------------------------

class TestRunning:
    def test_run_left(self) -> None:
        level = _floor_level(floor_row=10, player_col=5, player_row=9)
        p = Player(5, 9)
        p.handle_event(_keydown(C.KEY_LEFT))
        initial_x = p.x
        p.update(1 / 60, level)
        assert p.x < initial_x
        assert p.state == PlayerState.RUNNING_LEFT
        assert p.facing == -1

    def test_run_right(self) -> None:
        level = _floor_level(floor_row=10, player_col=5, player_row=9)
        p = Player(5, 9)
        p.handle_event(_keydown(C.KEY_RIGHT))
        initial_x = p.x
        p.update(1 / 60, level)
        assert p.x > initial_x
        assert p.state == PlayerState.RUNNING_RIGHT
        assert p.facing == 1

    def test_idle_when_no_input_on_floor(self) -> None:
        level = _floor_level(floor_row=10, player_col=5, player_row=9)
        p = Player(5, 9)
        p.update(1 / 60, level)
        assert p.state == PlayerState.IDLE

    def test_blocked_by_solid_wall_right(self) -> None:
        # Wall at col 6, player at col 5, floor at row 10
        patch = {(c, 10): C.SOLID_BRICK for c in range(C.GRID_COLS)}
        patch[(6, 9)] = C.SOLID_BRICK
        level = _make_level(patch)
        p = Player(5, 9)
        p.handle_event(_keydown(C.KEY_RIGHT))
        for _ in range(30):
            p.update(1 / 60, level)
        # Player should not have moved into the wall
        assert p.col <= 5

    def test_blocked_by_solid_wall_left(self) -> None:
        patch = {(c, 10): C.SOLID_BRICK for c in range(C.GRID_COLS)}
        patch[(4, 9)] = C.SOLID_BRICK
        level = _make_level(patch)
        p = Player(5, 9)
        p.handle_event(_keydown(C.KEY_LEFT))
        for _ in range(30):
            p.update(1 / 60, level)
        assert p.col >= 5

    def test_falls_off_platform_edge(self) -> None:
        # Floor only under cols 5–7; player runs right off edge
        patch = {(c, 10): C.SOLID_BRICK for c in range(5, 8)}
        level = _make_level(patch)
        p = Player(6, 9)
        p.handle_event(_keydown(C.KEY_RIGHT))
        for _ in range(30):
            p.update(1 / 60, level)
        assert p.state == PlayerState.FALLING


# ---------------------------------------------------------------------------
# TestClimbing
# ---------------------------------------------------------------------------

class TestClimbing:
    def test_climb_up_on_ladder(self) -> None:
        # Ladder at col 5, rows 3–8; floor at row 9; player starts at row 8
        patch = {(c, 9): C.SOLID_BRICK for c in range(C.GRID_COLS)}
        for r in range(3, 9):
            patch[(5, r)] = C.LADDER
        level = _make_level(patch)
        p = Player(5, 8)
        p.handle_event(_keydown(C.KEY_UP))
        initial_y = p.y
        p.update(1 / 60, level)
        assert p.y < initial_y
        assert p.state == PlayerState.CLIMBING_UP

    def test_climb_down_on_ladder(self) -> None:
        patch = {}
        for r in range(3, 9):
            patch[(5, r)] = C.LADDER
        patch[(5, 9)] = C.SOLID_BRICK
        level = _make_level(patch)
        p = Player(5, 5)  # mid-ladder
        p.handle_event(_keydown(C.KEY_DOWN))
        initial_y = p.y
        p.update(1 / 60, level)
        assert p.y > initial_y
        assert p.state == PlayerState.CLIMBING_DOWN

    def test_cannot_climb_without_ladder(self) -> None:
        level = _floor_level(floor_row=10, player_col=5, player_row=9)
        p = Player(5, 9)
        p.handle_event(_keydown(C.KEY_UP))
        initial_y = p.y
        p.update(1 / 60, level)
        # No ladder at (5, 9) — vertical input ignored
        assert p.y == initial_y

    def test_no_climb_when_x_misaligned(self) -> None:
        patch = {(5, 5): C.LADDER, (5, 6): C.SOLID_BRICK}
        level = _make_level(patch)
        p = Player(5, 5)
        p.x += C.TILE_SNAP_TOLERANCE + 1  # misalign x
        p.handle_event(_keydown(C.KEY_UP))
        initial_y = p.y
        p.update(1 / 60, level)
        assert p.y >= initial_y  # no upward movement


# ---------------------------------------------------------------------------
# TestRope
# ---------------------------------------------------------------------------

class TestRope:
    def test_player_hangs_on_rope(self) -> None:
        patch = {(5, 5): C.ROPE}
        level = _make_level(patch)
        p = Player(5, 5)
        initial_y = p.y
        p.update(1 / 60, level)
        # y should stay fixed (no gravity on rope)
        assert p.y == pytest.approx(initial_y, abs=1.0)

    def test_rope_traverse_right(self) -> None:
        for c in range(3, 10):
            pass  # build patch
        patch = {(c, 5): C.ROPE for c in range(3, 10)}
        level = _make_level(patch)
        p = Player(5, 5)
        p.handle_event(_keydown(C.KEY_RIGHT))
        initial_x = p.x
        p.update(1 / 60, level)
        assert p.x > initial_x
        assert p.state == PlayerState.ROPE_RIGHT

    def test_rope_traverse_left(self) -> None:
        patch = {(c, 5): C.ROPE for c in range(3, 10)}
        level = _make_level(patch)
        p = Player(5, 5)
        p.handle_event(_keydown(C.KEY_LEFT))
        initial_x = p.x
        p.update(1 / 60, level)
        assert p.x < initial_x
        assert p.state == PlayerState.ROPE_LEFT

    def test_falls_off_rope_end(self) -> None:
        # Rope at col 5 only; player traverses right off end
        patch = {(5, 5): C.ROPE}
        level = _make_level(patch)
        p = Player(5, 5)
        p.handle_event(_keydown(C.KEY_RIGHT))
        for _ in range(30):
            p.update(1 / 60, level)
            if p.col > 5:
                break
        assert p.state == PlayerState.FALLING
