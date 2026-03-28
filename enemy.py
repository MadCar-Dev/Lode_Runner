"""Enemy entity — state machine, greedy pathfinding AI, gold carrying, trapping."""

from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

import constants as C

if TYPE_CHECKING:
    from level import Level
    from player import Player


class EnemyState(Enum):
    IDLE = auto()
    RUNNING_LEFT = auto()
    RUNNING_RIGHT = auto()
    CLIMBING_UP = auto()
    CLIMBING_DOWN = auto()
    ROPE_LEFT = auto()
    ROPE_RIGHT = auto()
    FALLING = auto()
    TRAPPED = auto()
    DEAD = auto()


class Enemy:
    """A single enemy entity with greedy chase AI."""

    def __init__(self, col: int, row: int) -> None:
        self.x: float = float(col * C.TILE_SIZE)
        self.y: float = float(row * C.TILE_SIZE)
        self.state: EnemyState = EnemyState.IDLE
        self._spawn_col: int = col
        self._spawn_row: int = row
        self.has_gold: bool = False
        self._trap_timer: float = 0.0
        self._respawn_timer: float = 0.0
        self.anim_frame: int = 0
        self._anim_timer: float = 0.0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def col(self) -> int:
        return int(self.x / C.TILE_SIZE)

    @property
    def row(self) -> int:
        return int(self.y / C.TILE_SIZE)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self, dt: float, level: "Level", player: "Player") -> None:
        """Advance enemy AI and physics for one frame."""
        if self.state == EnemyState.DEAD:
            self._handle_dead(dt, level)
            return

        if self.state == EnemyState.TRAPPED:
            self._handle_trapped(dt, level)
            return

        # Check if standing on a hole -> become trapped
        tile_here = level.get_tile(self.col, self.row)
        if tile_here == C.HOLE_OPEN and self._is_on_floor_of_hole(level):
            self.state = EnemyState.TRAPPED
            self._trap_timer = 0.0
            self._snap_to_tile()
            return

        # Gravity first
        if not self._has_support(level):
            self._apply_gravity(dt, level)
            self.state = EnemyState.FALLING
            self._update_anim(dt)
            return

        # On solid ground or ladder or rope — run AI
        self._snap_y()
        self._run_ai(dt, level, player)
        self._try_pick_up_gold(level)
        self._update_anim(dt)

    def _die(self, level: "Level | None" = None) -> None:
        """Kill this enemy. Drops gold at current position if carrying."""
        if self.has_gold and level is not None:
            level.set_tile(self.col, self.row, C.GOLD)
            self.has_gold = False
        elif self.has_gold:
            self.has_gold = False
        self.state = EnemyState.DEAD
        self._respawn_timer = 0.0

    # ------------------------------------------------------------------
    # AI — greedy heuristic
    # ------------------------------------------------------------------

    def _run_ai(self, dt: float, level: "Level", player: "Player") -> None:
        """Greedy pathfinding: horizontal-first, then vertical via ladders."""
        pcol, prow = player.col, player.row
        ecol, erow = self.col, self.row

        on_ladder = self._is_on_ladder(level)
        on_rope = self._is_on_rope(level)

        # If on rope, move horizontally toward player
        if on_rope:
            self._handle_rope(dt, level, pcol)
            return

        # Same column — move vertically toward player's row
        if ecol == pcol:
            if erow < prow:
                # Player below — try to go down
                if on_ladder:
                    self._move_vertical(C.ENEMY_CLIMB_SPEED * C.TILE_SIZE * dt, level)
                    self.state = EnemyState.CLIMBING_DOWN
                    return
                # Try to fall off ledge or find ladder (do nothing extra, gravity handles)
            elif erow > prow:
                # Player above — try to climb up
                if on_ladder:
                    self._move_vertical(-C.ENEMY_CLIMB_SPEED * C.TILE_SIZE * dt, level)
                    self.state = EnemyState.CLIMBING_UP
                    return
            else:
                # Same position
                self.state = EnemyState.IDLE
                return

        # Different column — try horizontal first
        direction = -1 if pcol < ecol else 1
        if self._can_move_horizontal(direction, level):
            dx = direction * C.ENEMY_RUN_SPEED * C.TILE_SIZE * dt
            self._move_horizontal(dx, level)
            self.state = EnemyState.RUNNING_LEFT if direction == -1 else EnemyState.RUNNING_RIGHT
            return

        # Blocked horizontally — try ladder in current column
        if on_ladder:
            v_dir = -1 if prow < erow else 1
            self._move_vertical(v_dir * C.ENEMY_CLIMB_SPEED * C.TILE_SIZE * dt, level)
            self.state = EnemyState.CLIMBING_UP if v_dir == -1 else EnemyState.CLIMBING_DOWN
            return

        # Check if there's a ladder nearby (look at current tile or below)
        if level.is_ladder(ecol, erow + 1) and prow > erow:
            # Step down onto ladder below
            self._move_vertical(C.ENEMY_CLIMB_SPEED * C.TILE_SIZE * dt, level)
            self.state = EnemyState.CLIMBING_DOWN
            return

        # Stuck — idle
        self.state = EnemyState.IDLE

    def _handle_rope(self, dt: float, level: "Level", player_col: int) -> None:
        """Move along rope toward player's column."""
        self._snap_y()
        ecol = self.col
        if player_col < ecol:
            self._move_horizontal(-C.ENEMY_RUN_SPEED * C.TILE_SIZE * dt, level)
            self.state = EnemyState.ROPE_LEFT
        elif player_col > ecol:
            self._move_horizontal(C.ENEMY_RUN_SPEED * C.TILE_SIZE * dt, level)
            self.state = EnemyState.ROPE_RIGHT
        else:
            self.state = EnemyState.IDLE
        # Check if moved off rope
        nearest_col = round(self.x / C.TILE_SIZE)
        if not level.is_rope(nearest_col, self.row):
            self.state = EnemyState.FALLING

    # ------------------------------------------------------------------
    # Trapped / Dead handlers
    # ------------------------------------------------------------------

    def _handle_trapped(self, dt: float, level: "Level") -> None:
        """Manage trapped state: escape timer or die if hole closes."""
        # Check if hole has closed (tile reverted to DIGGABLE_BRICK)
        tile_here = level.get_tile(self.col, self.row)
        if tile_here == C.DIGGABLE_BRICK:
            self._die(level)
            return

        self._trap_timer += dt
        if self._trap_timer >= C.ENEMY_ESCAPE_TIME:
            # Attempt to climb out — move up by one tile
            self.y -= C.TILE_SIZE
            self.state = EnemyState.IDLE
            self._trap_timer = 0.0

    def _handle_dead(self, dt: float, level: "Level") -> None:
        """Wait for respawn timer, then respawn at top of spawn column."""
        self._respawn_timer += dt
        if self._respawn_timer >= C.HOLE_FILL_DURATION:  # 2-second-ish respawn delay
            self.x = float(self._spawn_col * C.TILE_SIZE)
            self.y = 0.0  # row 0 — will fall from top
            self.state = EnemyState.FALLING
            self._respawn_timer = 0.0

    # ------------------------------------------------------------------
    # Gold
    # ------------------------------------------------------------------

    def _try_pick_up_gold(self, level: "Level") -> None:
        """Pick up gold if enemy steps on a GOLD tile and isn't already carrying."""
        if self.has_gold:
            return
        if level.get_tile(self.col, self.row) == C.GOLD:
            level.set_tile(self.col, self.row, C.EMPTY)
            self.has_gold = True

    # ------------------------------------------------------------------
    # Support detection (mirrors Player logic)
    # ------------------------------------------------------------------

    def _has_support(self, level: "Level") -> bool:
        """True if enemy has floor, ladder, or rope support."""
        if self._is_on_floor(level):
            return True
        if self._is_on_ladder(level):
            return True
        if self._is_on_rope(level):
            return True
        return False

    def _is_on_floor(self, level: "Level") -> bool:
        if self.y % C.TILE_SIZE > C.TILE_SNAP_TOLERANCE:
            return False
        return level.is_standable(self.col, self.row + 1)

    def _is_on_floor_of_hole(self, level: "Level") -> bool:
        """True if enemy is tile-aligned and sitting in a hole (not just falling through)."""
        if self.y % C.TILE_SIZE > C.TILE_SNAP_TOLERANCE:
            return False
        # Standing in a hole means the tile AT enemy position is HOLE_OPEN
        # and there's something standable below (or bottom of grid)
        below = self.row + 1
        if below >= C.GRID_ROWS:
            return True
        return level.is_standable(self.col, below)

    def _is_on_ladder(self, level: "Level") -> bool:
        if self.x % C.TILE_SIZE > C.TILE_SNAP_TOLERANCE:
            return False
        return level.is_ladder(self.col, self.row)

    def _is_on_rope(self, level: "Level") -> bool:
        if self.x % C.TILE_SIZE > C.TILE_SNAP_TOLERANCE:
            return False
        return level.is_rope(self.col, self.row)

    # ------------------------------------------------------------------
    # Movement primitives (mirrors Player)
    # ------------------------------------------------------------------

    def _snap_x(self) -> None:
        self.x = float(round(self.x / C.TILE_SIZE) * C.TILE_SIZE)

    def _snap_y(self) -> None:
        self.y = float(round(self.y / C.TILE_SIZE) * C.TILE_SIZE)

    def _snap_to_tile(self) -> None:
        self._snap_x()
        self._snap_y()

    def _can_move_horizontal(self, direction: int, level: "Level") -> bool:
        """Check if enemy can step one tile in the given direction."""
        target_col = self.col + direction
        return level.is_passable(target_col, self.row)

    def _move_horizontal(self, dx: float, level: "Level") -> None:
        target_x = self.x + dx
        if dx > 0:
            new_right = int(target_x) + C.TILE_SIZE - 1
            new_right_col = new_right // C.TILE_SIZE
            cur_right_col = (int(self.x) + C.TILE_SIZE - 1) // C.TILE_SIZE
            if new_right_col > cur_right_col and level.is_solid(new_right_col, self.row):
                target_x = float(new_right_col * C.TILE_SIZE - C.TILE_SIZE)
        elif dx < 0:
            new_left_col = int(target_x) // C.TILE_SIZE
            cur_left_col = int(self.x) // C.TILE_SIZE
            if new_left_col < cur_left_col and level.is_solid(new_left_col, self.row):
                target_x = float((new_left_col + 1) * C.TILE_SIZE)
        target_x = max(0.0, min(target_x, float((C.GRID_COLS - 1) * C.TILE_SIZE)))
        self.x = target_x

    def _move_vertical(self, dy: float, level: "Level") -> None:
        target_y = self.y + dy
        if dy < 0:
            new_top_row = int(target_y) // C.TILE_SIZE
            cur_top_row = int(self.y) // C.TILE_SIZE
            if new_top_row < cur_top_row and level.is_solid(self.col, new_top_row):
                target_y = float((new_top_row + 1) * C.TILE_SIZE)
        elif dy > 0:
            new_bottom_row = (int(target_y) + C.TILE_SIZE) // C.TILE_SIZE
            old_bottom_row = (int(self.y) + C.TILE_SIZE) // C.TILE_SIZE
            if new_bottom_row > old_bottom_row and level.is_standable(self.col, new_bottom_row):
                target_y = float((new_bottom_row - 1) * C.TILE_SIZE)
        target_y = max(0.0, min(target_y, float((C.GRID_ROWS - 1) * C.TILE_SIZE)))
        self.y = target_y

    def _apply_gravity(self, dt: float, level: "Level") -> None:
        dy = C.ENEMY_FALL_SPEED * C.TILE_SIZE * dt
        target_y = self.y + dy
        old_bottom_row = (int(self.y) + C.TILE_SIZE) // C.TILE_SIZE
        new_bottom_row = (int(target_y) + C.TILE_SIZE) // C.TILE_SIZE
        if new_bottom_row > old_bottom_row and level.is_standable(self.col, new_bottom_row):
            target_y = float((new_bottom_row - 1) * C.TILE_SIZE)
            self.state = EnemyState.IDLE
        # Also check if landing on a rope
        if self._is_on_rope(level) and self.state == EnemyState.FALLING:
            self._snap_y()
            self.state = EnemyState.IDLE
            return
        self.y = min(target_y, float((C.GRID_ROWS - 1) * C.TILE_SIZE))

    def _update_anim(self, dt: float) -> None:
        self._anim_timer += dt
        if self._anim_timer >= 1.0 / C.PLAYER_ANIM_FPS:
            self._anim_timer -= 1.0 / C.PLAYER_ANIM_FPS
            self.anim_frame = (self.anim_frame + 1) % C.PLAYER_ANIM_FRAMES
