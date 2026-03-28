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
        self.enemy_spawns: list[SpawnPoint] = [SpawnPoint(**s) for s in data["enemy_spawns"]]
        self.escape_ladder_cols: list[int] = list(data["escape_ladder_cols"])
        # Hole state: (col, row) -> elapsed seconds since dig
        self._holes: dict[tuple[int, int], float] = {}

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
    # Hole lifecycle
    # ------------------------------------------------------------------

    def dig_hole(self, col: int, row: int) -> bool:
        """Dig a hole at (col, row). Returns True if successful.

        Only DIGGABLE_BRICK can be dug. Converts tile to HOLE_OPEN and
        starts the hole timer. Returns False if tile is not diggable or
        out of bounds.
        """
        if not self.is_diggable(col, row):
            return False
        self.set_tile(col, row, C.HOLE_OPEN)
        self._holes[(col, row)] = 0.0
        return True

    def update_holes(self, dt: float) -> None:
        """Advance all hole timers. Transitions:

        - After HOLE_OPEN_DURATION seconds: HOLE_OPEN -> HOLE_FILLING
        - After HOLE_OPEN_DURATION + HOLE_FILL_DURATION seconds: HOLE_FILLING -> DIGGABLE_BRICK
        """
        closed: list[tuple[int, int]] = []
        for pos, elapsed in self._holes.items():
            elapsed += dt
            self._holes[pos] = elapsed
            col, row = pos
            if elapsed >= C.HOLE_OPEN_DURATION + C.HOLE_FILL_DURATION:
                self.set_tile(col, row, C.DIGGABLE_BRICK)
                closed.append(pos)
            elif elapsed >= C.HOLE_OPEN_DURATION:
                self.set_tile(col, row, C.HOLE_FILLING)
        for pos in closed:
            del self._holes[pos]

    def get_hole_progress(self, col: int, row: int) -> float:
        """Return fill progress for a hole: 0.0 = just opened, 1.0 = fully filled.

        Returns 0.0 for non-hole tiles and during the HOLE_OPEN phase.
        During HOLE_FILLING, returns a float 0.0-1.0 proportional to how
        much of HOLE_FILL_DURATION has elapsed.
        """
        if (col, row) not in self._holes:
            return 0.0
        elapsed = self._holes[(col, row)]
        if elapsed < C.HOLE_OPEN_DURATION:
            return 0.0
        fill_elapsed = elapsed - C.HOLE_OPEN_DURATION
        return min(fill_elapsed / C.HOLE_FILL_DURATION, 1.0)

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
