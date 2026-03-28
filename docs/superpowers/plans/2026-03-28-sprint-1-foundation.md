# Sprint 1 — Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a running pygame window that loads and renders a static Lode Runner level from a JSON file, with all constants defined and level.py fully tested.

**Architecture:** `constants.py` defines all shared values; `level.py` implements the Level class that loads/queries/mutates the 28×16 tile grid; `renderer.py` draws tiles to screen; `main.py` wires them into a 60fps game loop. All subsequent sprints build on these four files.

**Tech Stack:** Python 3.12, pygame-ce, pytest, uv

**AgentOps:** Register as `python_developer` (PUT /agents/python_developer). The `testing_expert` agent works in parallel on Task 2 while `python_developer` works on Task 1.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `constants.py` | Create | All tile IDs, colors, timing, key bindings, grid dimensions |
| `level.py` | Create | Level class: load/save JSON, query tiles, mutate tiles, gold tracking |
| `renderer.py` | Modify | Static tile rendering (replace stub) |
| `main.py` | Modify | pygame init, window, 60fps game loop (replace stub) |
| `levels/level_01.json` | Create | Level 1 tile grid data |
| `tests/test_level.py` | Create | Full unit test suite for Level class |

---

## Task 1: constants.py

**Files:**
- Create: `constants.py`

- [ ] **Step 1: Create constants.py with all tile IDs, grid dimensions, window config, colors, timing, scoring, and key bindings**

```python
"""All game constants and tuning values. Change balance here, not in entity files."""

import pygame

# ---------------------------------------------------------------------------
# Tile IDs
# ---------------------------------------------------------------------------
EMPTY = 0
DIGGABLE_BRICK = 1
SOLID_BRICK = 2
LADDER = 3
ROPE = 4
GOLD = 5
HIDDEN_LADDER = 6
FALSE_BRICK = 7
HOLE_OPEN = 8
HOLE_FILLING = 9

# Tile sets for fast membership tests
SOLID_TILES = frozenset({SOLID_BRICK, DIGGABLE_BRICK})
STANDABLE_TILES = frozenset({SOLID_BRICK, DIGGABLE_BRICK})  # entities stand on top of these
PASSABLE_TILES = frozenset({EMPTY, LADDER, ROPE, GOLD, HIDDEN_LADDER, HOLE_OPEN, FALSE_BRICK})
CLIMBABLE_TILES = frozenset({LADDER})

# ---------------------------------------------------------------------------
# Grid and window
# ---------------------------------------------------------------------------
GRID_COLS = 28
GRID_ROWS = 16
TILE_SIZE = 32            # pixels per tile
HUD_HEIGHT = 32           # pixels for HUD bar above the grid

WINDOW_WIDTH = GRID_COLS * TILE_SIZE        # 896
WINDOW_HEIGHT = GRID_ROWS * TILE_SIZE + HUD_HEIGHT  # 544
FPS = 60

# Scaling modes
SCALE_1X = 1
SCALE_2X = 2

# ---------------------------------------------------------------------------
# Colors  (hex values from design-document.md §8.2, converted to RGB tuples)
# ---------------------------------------------------------------------------
COLOR_BACKGROUND             = (  0,   0,   0)
COLOR_SOLID_BRICK            = ( 42,  58,  90)
COLOR_DIGGABLE_BRICK         = (139, 108,  66)
COLOR_DIGGABLE_HIGHLIGHT     = (176, 138,  88)
COLOR_DIGGABLE_SHADOW        = ( 92,  71,  40)
COLOR_LADDER                 = (168, 217,  64)
COLOR_ROPE                   = (196, 122,  42)
COLOR_GOLD                   = (245, 197,  66)
COLOR_GOLD_GLINT             = (255, 255, 255)
COLOR_PLAYER_BODY            = (168, 212, 255)
COLOR_PLAYER_OUTLINE         = (232, 232, 232)
COLOR_ENEMY_BODY             = (217,  64,  64)
COLOR_ENEMY_OUTLINE          = (139,  26,  26)
COLOR_HUD_BG                 = ( 10,  10,  20)
COLOR_HUD_TEXT               = (245, 197,  66)
COLOR_HUD_TEXT_DIM           = (106,  96,  64)

# ---------------------------------------------------------------------------
# Timing (seconds)
# ---------------------------------------------------------------------------
HOLE_OPEN_DURATION    = 7.0   # seconds before hole starts filling
HOLE_FILL_DURATION    = 3.0   # seconds for fill animation (total life = 10s)
ENEMY_ESCAPE_TIME     = 2.5   # seconds before trapped enemy climbs out

# ---------------------------------------------------------------------------
# Movement speeds (tiles per second)
# ---------------------------------------------------------------------------
PLAYER_RUN_SPEED    = 7.0
PLAYER_CLIMB_SPEED  = 5.0
PLAYER_ROPE_SPEED   = 6.0
PLAYER_FALL_SPEED   = 10.0

ENEMY_RUN_SPEED     = 5.0
ENEMY_CLIMB_SPEED   = 4.0
ENEMY_FALL_SPEED    = 10.0

# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
SCORE_GOLD              = 250
SCORE_ENEMY_TRAPPED     = 75
SCORE_ENEMY_KILLED      = 75
SCORE_LEVEL_COMPLETE    = 1500

# Championship mode scoring
SCORE_GOLD_CHAMPIONSHIP          = 500
SCORE_LEVEL_COMPLETE_CHAMPIONSHIP = 2000
SCORE_ENEMY_CHAMPIONSHIP         = 100

# ---------------------------------------------------------------------------
# Lives
# ---------------------------------------------------------------------------
STARTING_LIVES  = 5
LIVES_PER_LEVEL = 1

# ---------------------------------------------------------------------------
# Key bindings (defaults; overridable via settings.json)
# ---------------------------------------------------------------------------
# Primary keys
KEY_LEFT      = pygame.K_LEFT
KEY_RIGHT     = pygame.K_RIGHT
KEY_UP        = pygame.K_UP
KEY_DOWN      = pygame.K_DOWN
KEY_DIG_LEFT  = pygame.K_z
KEY_DIG_RIGHT = pygame.K_x
KEY_PAUSE     = pygame.K_ESCAPE
KEY_MUSIC     = pygame.K_m

# Alternate keys (WASD)
KEY_ALT_LEFT  = pygame.K_a
KEY_ALT_RIGHT = pygame.K_d
KEY_ALT_UP    = pygame.K_w
KEY_ALT_DOWN  = pygame.K_s

# Dig alternates
KEY_ALT_DIG_LEFT  = pygame.K_LCTRL
KEY_ALT_DIG_RIGHT = pygame.K_RCTRL

# ---------------------------------------------------------------------------
# Control mode flags (toggled via settings.json)
# ---------------------------------------------------------------------------
CONTROL_TOGGLE_MOVE   = "toggle"   # Apple II authentic: press to start, press again to stop
CONTROL_HOLD_MOVE     = "hold"     # Modern: hold key to move

DIG_MODE_DIRECTIONAL  = "directional"   # Z/X dig relative to player facing
DIG_MODE_FIXED        = "fixed"         # Z always left, X always right
```

- [ ] **Step 2: Verify constants.py imports without error**

```bash
uv run python -c "import constants; print('OK', constants.GRID_COLS, 'x', constants.GRID_ROWS)"
```

Expected output: `OK 28 x 16`

- [ ] **Step 3: Commit**

```bash
git add constants.py
git commit -m "feat: add constants.py with all tile IDs, colors, timing, and key bindings"
```

---

## Task 2: tests/test_level.py (write failing tests first — TDD)

**Files:**
- Create: `tests/test_level.py`

*This task runs in parallel with Task 3 (testing_expert writes tests, python_developer implements Level).*

- [ ] **Step 1: Create tests/test_level.py with full test suite**

```python
"""Unit tests for level.py — Level class."""

import json
import tempfile
from pathlib import Path

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
_full_grid[0][0]  = C.EMPTY
_full_grid[0][1]  = C.DIGGABLE_BRICK
_full_grid[0][2]  = C.SOLID_BRICK
_full_grid[0][3]  = C.LADDER
_full_grid[0][4]  = C.ROPE
_full_grid[0][5]  = C.GOLD
_full_grid[0][6]  = C.HIDDEN_LADDER
_full_grid[0][7]  = C.FALSE_BRICK
_full_grid[0][8]  = C.HOLE_OPEN
_full_grid[0][9]  = C.HOLE_FILLING
_full_grid[1][0]  = C.GOLD   # second gold for multi-gold tests
_full_grid[1][6]  = C.HIDDEN_LADDER  # second hidden ladder tile (same col as [0][6])
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
        from level import Level
        level = Level(MINIMAL_LEVEL_DATA)
        # grid is 16 rows × 28 cols
        assert len(level._grid) == C.GRID_ROWS
        assert all(len(row) == C.GRID_COLS for row in level._grid)

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
        original_grid_id = id(data["grid"][0])
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
```

- [ ] **Step 2: Run tests to confirm they all fail (level.py doesn't exist yet)**

```bash
uv run pytest tests/test_level.py -v 2>&1 | head -30
```

Expected: `ModuleNotFoundError: No module named 'level'` or similar import failures.

- [ ] **Step 3: Commit the failing tests**

```bash
git add tests/test_level.py
git commit -m "test: add failing unit tests for Level class (TDD)"
```

---

## Task 3: level.py

**Files:**
- Create: `level.py`
- Test: `tests/test_level.py`

- [ ] **Step 1: Create level.py**

```python
"""Level data model — tile grid load/save, queries, and mutations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import NamedTuple

import constants as C


class SpawnPoint(NamedTuple):
    col: int
    row: int


class Level:
    """A single game level: 28×16 tile grid with spawn and escape data."""

    def __init__(self, data: dict) -> None:
        self.number: int = data["level"]
        # Deep-copy grid so mutations don't affect the source dict
        self._grid: list[list[int]] = [list(row) for row in data["grid"]]
        self.player_spawn = SpawnPoint(**data["player_spawn"])
        self.enemy_spawns: list[SpawnPoint] = [
            SpawnPoint(**s) for s in data["enemy_spawns"]
        ]
        self.escape_ladder_cols: list[int] = list(data["escape_ladder_cols"])

    # ------------------------------------------------------------------
    # Tile access
    # ------------------------------------------------------------------

    def get_tile(self, col: int, row: int) -> int:
        """Return tile ID at (col, row). Out-of-bounds returns SOLID_BRICK."""
        if col < 0 or col >= C.GRID_COLS or row < 0 or row >= C.GRID_ROWS:
            return C.SOLID_BRICK
        return self._grid[row][col]

    def set_tile(self, col: int, row: int, tile_id: int) -> None:
        """Set tile at (col, row). Out-of-bounds writes are silently ignored."""
        if 0 <= col < C.GRID_COLS and 0 <= row < C.GRID_ROWS:
            self._grid[row][col] = tile_id

    # ------------------------------------------------------------------
    # Tile property predicates
    # ------------------------------------------------------------------

    def is_solid(self, col: int, row: int) -> bool:
        """True if tile blocks movement (solid or diggable brick, NOT false brick)."""
        return self.get_tile(col, row) in C.SOLID_TILES

    def is_standable(self, col: int, row: int) -> bool:
        """True if an entity can stand on top of this tile."""
        return self.get_tile(col, row) in C.STANDABLE_TILES

    def is_diggable(self, col: int, row: int) -> bool:
        """True if the player can dig this tile."""
        return self.get_tile(col, row) == C.DIGGABLE_BRICK

    def is_ladder(self, col: int, row: int) -> bool:
        """True if tile is a climbable ladder."""
        return self.get_tile(col, row) == C.LADDER

    def is_rope(self, col: int, row: int) -> bool:
        """True if tile is a traversable rope/bar."""
        return self.get_tile(col, row) == C.ROPE

    def is_passable(self, col: int, row: int) -> bool:
        """True if an entity can occupy this tile position."""
        return self.get_tile(col, row) in C.PASSABLE_TILES

    # ------------------------------------------------------------------
    # Gold tracking
    # ------------------------------------------------------------------

    def gold_positions(self) -> list[tuple[int, int]]:
        """Return list of (col, row) for all GOLD tiles currently on the grid."""
        return [
            (col, row)
            for row in range(C.GRID_ROWS)
            for col in range(C.GRID_COLS)
            if self._grid[row][col] == C.GOLD
        ]

    # ------------------------------------------------------------------
    # Escape ladder
    # ------------------------------------------------------------------

    def reveal_escape_ladder(self) -> None:
        """Convert all HIDDEN_LADDER tiles in escape_ladder_cols to LADDER."""
        for col in self.escape_ladder_cols:
            for row in range(C.GRID_ROWS):
                if self._grid[row][col] == C.HIDDEN_LADDER:
                    self._grid[row][col] = C.LADDER

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    @classmethod
    def from_file(cls, path: str | Path) -> Level:
        """Load a Level from a JSON file."""
        with open(path) as f:
            data = json.load(f)
        return cls(data)

    def to_file(self, path: str | Path) -> None:
        """Save the Level to a JSON file."""
        data = {
            "level": self.number,
            "grid": self._grid,
            "player_spawn": {"col": self.player_spawn.col, "row": self.player_spawn.row},
            "enemy_spawns": [{"col": s.col, "row": s.row} for s in self.enemy_spawns],
            "escape_ladder_cols": self.escape_ladder_cols,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
```

- [ ] **Step 2: Run the tests — all should pass**

```bash
uv run pytest tests/test_level.py -v
```

Expected: All tests `PASSED`. Fix any failures before continuing.

- [ ] **Step 3: Commit**

```bash
git add level.py
git commit -m "feat: implement Level class with tile grid, queries, and escape ladder"
```

---

## Task 4: levels/level_01.json

**Files:**
- Create: `levels/level_01.json`

- [ ] **Step 1: Create the level file**

The grid is 16 rows × 28 columns. Row 0 = top of screen, row 15 = bottom.
Tile IDs: EMPTY=0, DIGGABLE=1, SOLID=2, LADDER=3, ROPE=4, GOLD=5, HIDDEN_LADDER=6, FALSE_BRICK=7

Design notes:
- Row 15: solid brick floor
- Rows 3, 5, 7, 9, 11, 13: diggable brick platforms with gaps
- Ladders at columns 6, 13, 18 connecting all platforms
- Hidden ladder at column 0 (rows 0–2) — becomes escape route
- Rope at row 8 cols 2–5 and cols 21–24
- Gold scattered on platform rows
- Player spawns at col 1, row 14 (ground level, left side)
- Enemy spawns at col 26, row 0 (top right)

```json
{
  "level": 1,
  "grid": [
    [6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,1,1,1,1,1,3,1,1,1,1,1,0,1,1,1,1,1,3,1,1,1,1,1,1,1,1,0],
    [0,0,0,5,0,0,3,0,0,0,5,0,0,0,0,0,5,0,3,0,0,0,0,5,0,0,0,0],
    [1,1,1,1,1,1,3,0,1,1,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1,1],
    [0,0,0,0,0,0,3,0,0,0,0,0,0,3,0,0,0,0,3,0,0,0,0,0,0,0,0,0],
    [0,1,1,1,0,1,3,1,1,1,5,1,1,3,1,1,5,1,3,1,1,1,0,0,1,1,1,0],
    [0,0,4,4,4,4,3,0,0,0,0,0,0,3,0,0,0,0,3,0,0,4,4,4,4,0,0,0],
    [1,1,1,0,5,1,3,1,1,1,1,0,1,3,1,0,1,1,3,1,1,1,0,5,1,1,1,1],
    [0,0,0,0,0,0,3,0,0,0,0,0,0,3,0,0,0,0,3,0,0,0,0,0,0,0,0,0],
    [0,1,1,1,1,1,3,1,1,0,5,1,1,3,1,1,0,0,3,1,1,1,1,1,1,0,1,0],
    [0,0,5,0,0,0,3,0,0,0,0,0,0,3,0,0,0,0,3,0,0,5,0,0,0,0,0,0],
    [1,1,1,1,1,1,3,1,1,1,1,1,1,3,1,1,1,1,3,1,1,1,1,1,1,1,1,1],
    [0,0,0,0,5,0,3,0,0,5,0,0,0,3,0,0,5,0,3,0,0,0,5,0,0,0,0,0],
    [2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2]
  ],
  "player_spawn": {"col": 1, "row": 14},
  "enemy_spawns": [{"col": 26, "row": 0}],
  "escape_ladder_cols": [0]
}
```

- [ ] **Step 2: Verify the level file loads correctly**

```bash
uv run python -c "
from level import Level
import constants as C
lv = Level.from_file('levels/level_01.json')
print('Level:', lv.number)
print('Gold pieces:', len(lv.gold_positions()))
print('Player spawn:', lv.player_spawn)
print('Enemy spawns:', lv.enemy_spawns)
print('Bottom row tile 0:', lv.get_tile(0, C.GRID_ROWS - 1))  # should be 2 (SOLID_BRICK)
"
```

Expected output:
```
Level: 1
Gold pieces: 10
Player spawn: SpawnPoint(col=1, row=14)
Enemy spawns: [SpawnPoint(col=26, row=0)]
Bottom row tile 0: 2
```

- [ ] **Step 3: Commit**

```bash
git add levels/level_01.json
git commit -m "feat: add level 01 JSON data (reference level for Sprint 1)"
```

---

## Task 5: renderer.py (static tiles)

**Files:**
- Modify: `renderer.py`

- [ ] **Step 1: Replace renderer.py with static tile rendering**

```python
"""Renderer — draws game state to a pygame surface each frame."""

from __future__ import annotations

import pygame

import constants as C
from level import Level


class Renderer:
    """Draws the current game state. Sprint 1: static tiles only."""

    def __init__(self, screen: pygame.Surface) -> None:
        self._screen = screen
        # Offscreen surface at native resolution; scaled to window on flip
        self._surface = pygame.Surface((C.WINDOW_WIDTH, C.WINDOW_HEIGHT))
        pygame.font.init()
        self._font = pygame.font.SysFont("monospace", 14)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def draw(self, level: Level) -> None:
        """Draw the full frame: clear → tiles → HUD → blit to screen."""
        self._surface.fill(C.COLOR_BACKGROUND)
        self._draw_tiles(level)
        self._draw_hud()
        # Scale offscreen surface to actual screen size
        if self._screen.get_size() != (C.WINDOW_WIDTH, C.WINDOW_HEIGHT):
            scaled = pygame.transform.scale(self._surface, self._screen.get_size())
            self._screen.blit(scaled, (0, 0))
        else:
            self._screen.blit(self._surface, (0, 0))

    # ------------------------------------------------------------------
    # Tile drawing
    # ------------------------------------------------------------------

    def _draw_tiles(self, level: Level) -> None:
        for row in range(C.GRID_ROWS):
            for col in range(C.GRID_COLS):
                tile = level.get_tile(col, row)
                x = col * C.TILE_SIZE
                y = row * C.TILE_SIZE + C.HUD_HEIGHT
                self._draw_tile(tile, x, y)

    def _draw_tile(self, tile_id: int, x: int, y: int) -> None:
        ts = C.TILE_SIZE
        rect = pygame.Rect(x, y, ts, ts)

        if tile_id == C.SOLID_BRICK:
            pygame.draw.rect(self._surface, C.COLOR_SOLID_BRICK, rect)

        elif tile_id in (C.DIGGABLE_BRICK, C.FALSE_BRICK):
            # FALSE_BRICK looks identical to DIGGABLE_BRICK — that's intentional
            pygame.draw.rect(self._surface, C.COLOR_DIGGABLE_BRICK, rect)
            # Top-left highlight edge
            pygame.draw.line(self._surface, C.COLOR_DIGGABLE_HIGHLIGHT,
                             (x, y), (x + ts - 1, y))
            pygame.draw.line(self._surface, C.COLOR_DIGGABLE_HIGHLIGHT,
                             (x, y), (x, y + ts - 1))
            # Bottom-right shadow edge
            pygame.draw.line(self._surface, C.COLOR_DIGGABLE_SHADOW,
                             (x + ts - 1, y), (x + ts - 1, y + ts - 1))
            pygame.draw.line(self._surface, C.COLOR_DIGGABLE_SHADOW,
                             (x, y + ts - 1), (x + ts - 1, y + ts - 1))
            # Mortar line (horizontal, centered)
            pygame.draw.line(self._surface, C.COLOR_DIGGABLE_SHADOW,
                             (x, y + ts // 2), (x + ts - 1, y + ts // 2))

        elif tile_id == C.LADDER:
            # Two vertical rails + horizontal rungs
            rail_x1 = x + ts // 4
            rail_x2 = x + (ts * 3) // 4
            pygame.draw.line(self._surface, C.COLOR_LADDER,
                             (rail_x1, y), (rail_x1, y + ts - 1))
            pygame.draw.line(self._surface, C.COLOR_LADDER,
                             (rail_x2, y), (rail_x2, y + ts - 1))
            # Four rungs evenly spaced
            for i in range(4):
                rung_y = y + (ts * i) // 4 + ts // 8
                pygame.draw.line(self._surface, C.COLOR_LADDER,
                                 (rail_x1, rung_y), (rail_x2, rung_y))

        elif tile_id == C.ROPE:
            # Horizontal line at 1/3 height + knots every 8px
            rope_y = y + ts // 3
            pygame.draw.line(self._surface, C.COLOR_ROPE,
                             (x, rope_y), (x + ts - 1, rope_y), 2)
            for kx in range(x + 4, x + ts, 8):
                pygame.draw.circle(self._surface, C.COLOR_ROPE, (kx, rope_y), 2)

        elif tile_id == C.GOLD:
            # Diamond shape
            cx, cy = x + ts // 2, y + ts // 2
            r = ts // 5
            points = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
            pygame.draw.polygon(self._surface, C.COLOR_GOLD, points)
            # Glint
            pygame.draw.circle(self._surface, C.COLOR_GOLD_GLINT,
                                (cx - r // 2, cy - r // 2), 2)

        elif tile_id == C.HIDDEN_LADDER:
            pass  # Renders as empty space — invisible until revealed

        elif tile_id == C.HOLE_OPEN:
            pass  # Void — background shows through

        elif tile_id == C.HOLE_FILLING:
            # Partial brick closing in — drawn as two inward rectangles
            progress = 0.5  # Sprint 1: static midpoint; animated in Sprint 3
            fill_w = int(ts * progress * 0.5)
            pygame.draw.rect(self._surface, C.COLOR_DIGGABLE_BRICK,
                             pygame.Rect(x, y, fill_w, ts))
            pygame.draw.rect(self._surface, C.COLOR_DIGGABLE_BRICK,
                             pygame.Rect(x + ts - fill_w, y, fill_w, ts))

        # EMPTY: draw nothing (background color already filled)

    # ------------------------------------------------------------------
    # HUD
    # ------------------------------------------------------------------

    def _draw_hud(self) -> None:
        hud_rect = pygame.Rect(0, 0, C.WINDOW_WIDTH, C.HUD_HEIGHT)
        pygame.draw.rect(self._surface, C.COLOR_HUD_BG, hud_rect)
        label = self._font.render("LODE RUNNER  |  Sprint 1 Foundation", True,
                                  C.COLOR_HUD_TEXT)
        self._surface.blit(label, (8, 8))
```

- [ ] **Step 2: Commit**

```bash
git add renderer.py
git commit -m "feat: implement static tile renderer for Sprint 1"
```

---

## Task 6: main.py (game loop)

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Replace main.py with full pygame init and game loop**

```python
"""Lode Runner — entry point and main game loop."""

import sys

import pygame

import constants as C
from level import Level
from renderer import Renderer


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Lode Runner")

    screen = pygame.display.set_mode((C.WINDOW_WIDTH, C.WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    level = Level.from_file("levels/level_01.json")
    renderer = Renderer(screen)

    running = True
    while running:
        # Cap at 60fps; dt is elapsed seconds since last frame
        _dt = clock.tick(C.FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (C.KEY_PAUSE, pygame.K_q):
                    running = False

        renderer.draw(level)
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the game — a window should open showing the level**

```bash
uv run python main.py
```

Expected: Pygame window opens at 896×544. Level 1 tiles visible — brown diggable bricks, blue solid bricks, yellow-green ladders, orange rope, gold diamonds. Press Escape or Q to quit.

- [ ] **Step 3: Run the full test suite — all should pass**

```bash
uv run pytest tests/ -v
```

Expected: All tests `PASSED`.

- [ ] **Step 4: Run linter**

```bash
uv run ruff check .
```

Expected: No errors.

- [ ] **Step 5: Final commit**

```bash
git add main.py renderer.py
git commit -m "feat: implement main game loop with pygame init and static renderer"
```

---

## Sprint 1 Complete — Handoff to Code Review

Post a `deliverable` message to `orchestrator_pm` with:
- Files created/modified: `constants.py`, `level.py`, `renderer.py`, `main.py`, `levels/level_01.json`, `tests/test_level.py`
- Test status: `uv run pytest tests/ -v` output
- Lint status: `uv run ruff check .` output
- Visual confirmation: game window renders level 1 tiles correctly

Idle your agent: PUT /agents/{your-name} `{"status": "idle"}`
